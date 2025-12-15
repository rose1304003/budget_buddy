from fastapi import APIRouter, Request
import os
import httpx

router = APIRouter()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


@router.post("/telegram/webhook")
async def telegram_webhook(req: Request):
    update = await req.json()

    message = update.get("message") or update.get("edited_message")
    if not message or not TOKEN:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    reply_text = "✅ Bot is online!" if text.startswith("/start") else f"🧾 Got: {text}"

    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": reply_text},
        )

    return {"ok": True}
