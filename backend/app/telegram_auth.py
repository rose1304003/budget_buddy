"""Telegram WebApp authentication module.

This module handles verification of Telegram WebApp initData to authenticate users.
"""

from __future__ import annotations
import hashlib
import hmac
import json
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class TelegramUser:
    """Represents an authenticated Telegram user."""
    id: int
    first_name: str = ""
    last_name: str = ""
    username: str = ""
    language_code: str = ""

def _parse_init_data(init_data: str) -> Dict[str, str]:
    """Parse Telegram initData query string into a dictionary.
    
    Args:
        init_data: URL-encoded query string from Telegram WebApp
        
    Returns:
        Dictionary of parsed key-value pairs
    """
    return dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))

def verify_init_data(
    init_data: str,
    bot_token: str,
    *,
    max_age_seconds: int = 24 * 60 * 60
) -> Optional[TelegramUser]:
    """Verify Telegram WebApp initData and extract user information.
    
    This function verifies the HMAC signature of the initData to ensure it
    came from Telegram and hasn't been tampered with. It also checks that
    the data is not too old.
    
    Args:
        init_data: Telegram WebApp initData query string
        bot_token: Bot token from BotFather
        max_age_seconds: Maximum age of initData in seconds (default: 24 hours)
        
    Returns:
        TelegramUser if verification succeeds, None otherwise
    """
    if not init_data:
        return None

    data = _parse_init_data(init_data)
    received_hash = data.get("hash")
    if not received_hash:
        return None

    pairs = []
    for k in sorted(data.keys()):
        if k == "hash":
            continue
        pairs.append(f"{k}={data[k]}")
    data_check_string = "\n".join(pairs)

    secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    auth_date_str = data.get("auth_date")
    if auth_date_str and auth_date_str.isdigit():
        auth_date = int(auth_date_str)
        if (int(time.time()) - auth_date) > max_age_seconds:
            return None

    user_json = data.get("user")
    if not user_json:
        return None

    try:
        user_obj: Dict[str, Any] = json.loads(user_json)
        return TelegramUser(
            id=int(user_obj.get("id")),
            first_name=str(user_obj.get("first_name") or ""),
            last_name=str(user_obj.get("last_name") or ""),
            username=str(user_obj.get("username") or ""),
            language_code=str(user_obj.get("language_code") or ""),
        )
    except Exception:
        return None
