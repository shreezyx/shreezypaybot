
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# === Configuration ===
import os
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
SOURCE_GROUP_ID = -4777887764  # Group A
DEST_GROUP_ID = -4707332741    # Group B
ALLOWED_USER_ID = 7736896844      # Only forward messages from this user (Group A → B)
BANNED_KEYWORDS = ["总入款", "汇率", "交易费率","pay"]  # Don't forward if found in message

# === Message Handler ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    # === Group A → Group B ===
    if msg.chat.id == SOURCE_GROUP_ID:
        if msg.from_user.id != ALLOWED_USER_ID:
            return
        text = msg.text or msg.caption or ""
        if any(word.lower() in text.lower() for word in BANNED_KEYWORDS):
            return
        await resend_message(msg, DEST_GROUP_ID, context)

    # === Group B → Group A (no filter) ===
    elif msg.chat.id == DEST_GROUP_ID:
        await resend_message(msg, SOURCE_GROUP_ID, context)

# === Re-sending Logic (not forwarding, clean send) ===
async def resend_message(msg, target_chat_id, context):
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
        print("Unsupported message type:", msg)

# === Start the Bot ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    app.run_polling()
