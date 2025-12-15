from fastapi import Header, HTTPException
from .settings import settings
from .telegram_auth import verify_init_data, TelegramUser

def get_current_user(
    x_tg_init_data: str | None = Header(default=None),
    x_tg_user_id: str | None = Header(default=None)
) -> TelegramUser:
    """Get current user from Telegram initData or simple bot user ID."""
    
    # Try proper initData first (from web app)
    if x_tg_init_data:
        user = verify_init_data(x_tg_init_data, settings.telegram_bot_token)
        if user:
            return user
    
    # Allow simple user ID for bot commands (temporary/testing)
    if x_tg_user_id:
        try:
            user_id = int(x_tg_user_id)
            return TelegramUser(
                id=user_id,
                first_name="Bot User",
                last_name="",
                username="",
                language_code="en"
            )
        except (ValueError, TypeError):
            pass
    
    raise HTTPException(
        status_code=401,
        detail="Unauthorized (invalid Telegram initData)"
    )