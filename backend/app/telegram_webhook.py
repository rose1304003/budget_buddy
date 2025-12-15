from fastapi import APIRouter, Request
import os
import httpx

router = APIRouter()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

@router.post("/telegram/webhook")
async def telegram_webhook(req: Request):
    update = await req.json()

    # --- VERY SIMPLE reply logic (for testing) ---
    try:
        message = update.get("message") or update.get("edited_message")
        if message:
            chat_id = message["chat"]["id"]
            text = message.get("text", "")

            # reply to /start (or any message)
            reply_text = "✅ Bot is online!" if text.startswith("/start") else f"🧾 Got: {text}"

            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(url, json={"chat_id": chat_id, "text": reply_text})
    except Exception:
        # don't crash webhook
        pass

    return {"ok": True}
