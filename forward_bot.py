
from telegram import Update, Message
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import os
import logging

# === Configuration ===
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

GROUP_PAIRS = [
   {
        "source_group_id": -1002529651007,     # Group A1
        "dest_group_id": -4707332741,         # Group B1
        "allowed_user_ids": [7736896844,5755763845,7831921686]      # Allowed users in Group A1
    },
    {
        "source_group_id": -4788525991,    # Group A2
        "dest_group_id": -4789201862,      # Group B2
        "allowed_user_ids": [7673528399,104784211]
    },
]

BANNED_KEYWORDS = ["总入款", "汇率", "交易费率", "pay"]

# === In-memory message ID map ===
# (src_group, src_msg_id) → dest_msg_id
message_map = {}

# === Message Handler ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    chat_id = msg.chat.id
    sender_id = msg.from_user.id if msg.from_user else None
    is_bot_sender = msg.from_user and msg.from_user.is_bot
    text = msg.text or msg.caption or ""

    for pair in GROUP_PAIRS:
        source_group = pair["source_group_id"]
        dest_group = pair["dest_group_id"]
        allowed_users = pair["allowed_user_ids"]

        # === Source → Destination ===
        if chat_id == source_group:
            # Allow if user is in allowed list or is a bot
            if sender_id not in allowed_users and not is_bot_sender:
                return
            if any(word.lower() in text.lower() for word in BANNED_KEYWORDS):
                return
            reply_to_id = get_reply_target(msg, source_group, dest_group)
            sent_msg = await resend_message(msg, dest_group, context, reply_to_message_id=reply_to_id)
            if sent_msg:
                message_map[(source_group, msg.message_id)] = sent_msg.message_id
                message_map[(dest_group, sent_msg.message_id)] = msg.message_id
            return

        # === Destination → Source ===
        elif chat_id == dest_group:
            reply_to_id = get_reply_target(msg, dest_group, source_group)
            sent_msg = await resend_message(msg, source_group, context, reply_to_message_id=reply_to_id)
            if sent_msg:
                message_map[(dest_group, msg.message_id)] = sent_msg.message_id
                message_map[(source_group, sent_msg.message_id)] = msg.message_id
            return

# === Determine reply target ===
def get_reply_target(msg: Message, src_group: int, dest_group: int):
    if msg.reply_to_message:
        reply_src_id = msg.reply_to_message.message_id
        return message_map.get((src_group, reply_src_id))
    return None

# === Re-send message cleanly ===
async def resend_message(msg: Message, target_chat_id: int, context: ContextTypes.DEFAULT_TYPE, reply_to_message_id=None):
    try:
        if msg.text:
            return await context.bot.send_message(
                chat_id=target_chat_id,
                text=msg.text,
                reply_to_message_id=reply_to_message_id
            )

        elif msg.photo:
            return await context.bot.send_photo(
                chat_id=target_chat_id,
                photo=msg.photo[-1].file_id,
                caption=msg.caption or "",
                reply_to_message_id=reply_to_message_id
            )

        elif msg.video:
            return await context.bot.send_video(
                chat_id=target_chat_id,
                video=msg.video.file_id,
                caption=msg.caption or "",
                reply_to_message_id=reply_to_message_id
            )

        elif msg.document:
            return await context.bot.send_document(
                chat_id=target_chat_id,
                document=msg.document.file_id,
                caption=msg.caption or "",
                reply_to_message_id=reply_to_message_id
            )

        else:
            logging.warning(f"Unsupported message type: {msg}")
            return None

    except Exception as e:
        logging.error(f"Error resending message: {e}")
        return None

# === Run the bot ===
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    app.run_polling()
