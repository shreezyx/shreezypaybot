
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import os
import logging

# === Configuration ===
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

# List of group pairs
GROUP_PAIRS = [
    {
        "source_group_id": -1002529651007,     # Group A1
        "dest_group_id": -4707332741,         # Group B1
        "allowed_user_ids": [7736896844,5755763845,7831921686]      # Allowed users in Group A1
    },
    {
        "source_group_id": -1002668261562,    # Group A2
        "dest_group_id": -4789201862,      # Group B2
        "allowed_user_ids": [7333557425]
    },
    # Add more pairs here
]

BANNED_KEYWORDS = ["总入款", "汇率", "交易费率", "pay"]  # Don't forward if found in message

# === Message Handler ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    chat_id = msg.chat.id
    sender_id = msg.from_user.id if msg.from_user else None
    text = msg.text or msg.caption or ""

    for pair in GROUP_PAIRS:
        source_group = pair["source_group_id"]
        dest_group = pair["dest_group_id"]
        allowed_users = pair["allowed_user_ids"]

        # === Group A → Group B ===
        if chat_id == source_group:
            if sender_id not in allowed_users:
                return
            if any(word.lower() in text.lower() for word in BANNED_KEYWORDS):
                return
            await resend_message(msg, dest_group, context)
            return

        # === Group B → Group A (no filter) ===
        elif chat_id == dest_group:
            await resend_message(msg, source_group, context)
            return

# === Re-sending Logic (not forwarding, clean send) ===
async def resend_message(msg, target_chat_id, context):
    try:
        if msg.text:
            await context.bot.send_message(chat_id=target_chat_id, text=msg.text)

        elif msg.photo:
            await context.bot.send_photo(
                chat_id=target_chat_id,
                photo=msg.photo[-1].file_id,
                caption=msg.caption or ""
            )

        elif msg.video:
            await context.bot.send_video(
                chat_id=target_chat_id,
                video=msg.video.file_id,
                caption=msg.caption or ""
            )

        elif msg.document:
            await context.bot.send_document(
                chat_id=target_chat_id,
                document=msg.document.file_id,
                caption=msg.caption or ""
            )

        else:
            logging.warning(f"Unsupported message type: {msg}")

    except Exception as e:
        logging.error(f"Error resending message: {e}")

# === Start the Bot ===
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    app.run_polling()
