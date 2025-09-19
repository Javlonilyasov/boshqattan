import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from database import init_db, save_message, get_users

# .env yuklash
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]

# DB init
init_db()

# Javoblarni vaqtincha saqlash: {admin_id: {"user_id": int, "message_id": int}}
reply_targets = {}

# 🔹 Foydalanuvchilar IDlarini olish
def get_all_user_ids():
    users = get_users()
    return [u[0] for u in users]

# --- Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Xabaringizni yozing, men uni adminga yetkazaman 📩")

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Sizning Telegram ID: {update.message.from_user.id}")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Buyruqlar:\n"
        "/start – Botni ishga tushirish\n"
        "/myid – O‘z ID raqamingizni olish\n"
        "/users – So‘nggi foydalanuvchilar ro‘yxati (faqat admin)\n"
        "/reply <id> – Foydalanuvchiga bevosita javob berish\n"
        "/broadcast <matn> – Hammaga xabar yuborish (media ham mumkin)\n"
        "/send <id yoki @username> <matn> – Bot nomidan xabar yuborish\n"
    )

async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        return
    users = get_users()
    if not users:
        await update.message.reply_text("👤 Hali foydalanuvchilar yo‘q.")
        return
    msg = "👥 So‘nggi foydalanuvchilar:\n"
    for uid, uname in users:
        msg += f"🆔 {uid} | @{uname or 'yo‘q'}\n"
    await update.message.reply_text(msg)

async def reply_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        return
    try:
        user_id = int(context.args[0])
        reply_targets[update.message.from_user.id] = {"user_id": user_id, "message_id": None}
        await update.message.reply_text(f"✏️ Endi foydalanuvchi {user_id} ga javob matnini yozing.")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Foydalanish: /reply <user_id>")

# --- Broadcast ---
async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        return

    user_ids = get_all_user_ids()
    sent, failed = 0, 0

    if update.message.reply_to_message:
        # Agar reply qilingan bo‘lsa → media yuboriladi
        reply = update.message.reply_to_message
        for uid in user_ids:
            try:
                if reply.photo:
                    await context.bot.send_photo(chat_id=uid, photo=reply.photo[-1].file_id, caption=reply.caption or "")
                elif reply.video:
                    await context.bot.send_video(chat_id=uid, video=reply.video.file_id, caption=reply.caption or "")
                elif reply.document:
                    await context.bot.send_document(chat_id=uid, document=reply.document.file_id, caption=reply.caption or "")
                elif reply.audio:
                    await context.bot.send_audio(chat_id=uid, audio=reply.audio.file_id, caption=reply.caption or "")
                elif reply.voice:
                    await context.bot.send_voice(chat_id=uid, voice=reply.voice.file_id, caption=reply.caption or "")
                else:
                    await context.bot.send_message(chat_id=uid, text=reply.text or "📢 Broadcast xabar")
                sent += 1
            except:
                failed += 1
    else:
        # Oddiy text broadcast
        text = " ".join(context.args)
        if not text:
            await update.message.reply_text("❌ Matn yoki reply qilib media yuboring.")
            return
        for uid in user_ids:
            try:
                await context.bot.send_message(chat_id=uid, text=f"📢 Broadcast:\n{text}")
                sent += 1
            except:
                failed += 1

    await update.message.reply_text(f"✅ Broadcast tugadi.\nYuborildi: {sent} | Xato: {failed}")

# --- Send to specific chat (username yoki chat_id) ---
async def send_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text("❌ Foydalanish: /send <chat_id yoki @username> <matn>")
        return

    target = context.args[0]  # chat_id yoki @username
    text = " ".join(context.args[1:])

    try:
        if update.message.reply_to_message:  # Reply qilingan bo‘lsa → media yuboriladi
            reply = update.message.reply_to_message
            if reply.photo:
                await context.bot.send_photo(chat_id=target, photo=reply.photo[-1].file_id, caption=text or reply.caption or "")
            elif reply.video:
                await context.bot.send_video(chat_id=target, video=reply.video.file_id, caption=text or reply.caption or "")
            elif reply.document:
                await context.bot.send_document(chat_id=target, document=reply.document.file_id, caption=text or reply.caption or "")
            elif reply.audio:
                await context.bot.send_audio(chat_id=target, audio=reply.audio.file_id, caption=text or reply.caption or "")
            elif reply.voice:
                await context.bot.send_voice(chat_id=target, voice=reply.voice.file_id, caption=text or reply.caption or "")
            else:
                await context.bot.send_message(chat_id=target, text=text or reply.text or "📩 Xabar")
        else:  # Oddiy text yuborish
            if not text:
                await update.message.reply_text("❌ Matn yoki reply qilib media yuboring.")
                return
            await context.bot.send_message(chat_id=target, text=text)

        await update.message.reply_text(f"✅ Xabar yuborildi → {target}")
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")

# --- Message handling ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "username yo‘q"
    msg_id = update.message.message_id

    # Text yoki media aniqlash
    if update.message.text:
        text = update.message.text
    elif update.message.photo:
        text = "📷 Rasm yuborildi"
    elif update.message.video:
        text = "🎥 Video yuborildi"
    elif update.message.document:
        text = f"📄 Hujjat: {update.message.document.file_name}"
    elif update.message.voice:
        text = "🎤 Ovozli xabar yuborildi"
    elif update.message.audio:
        text = "🎶 Audio yuborildi"
    else:
        text = "❓ Noma’lum turdagi xabar"

    if user_id in ADMIN_IDS:  # admin yozsa
        if user_id in reply_targets:
            target_info = reply_targets[user_id]
            target_id = target_info["user_id"]
            target_msg_id = target_info["message_id"]

            await context.bot.send_message(
                chat_id=target_id,
                text=f"📩 Admin javobi:\n{text}",
                reply_to_message_id=target_msg_id if target_msg_id else None
            )
            await update.message.reply_text("✅ Javob foydalanuvchiga yuborildi.")
            del reply_targets[user_id]
        else:
            await update.message.reply_text("ℹ️ Javob berish uchun tugmani bosing yoki /reply <id> ishlating.")
    else:  # oddiy foydalanuvchi yozsa
        save_message(user_id, username, msg_id, text)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Javob berish", callback_data=f"reply_{user_id}_{msg_id}")]
        ])
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"📢 Yangi xabar:\n"
                    f"👤 Username: @{username}\n"
                    f"🆔 ID: {user_id}\n"
                    f"💬 Xabar: {text}"
                ),
                reply_markup=keyboard,
                disable_notification=False  # 🔔 ovoz bilan
            )
        await update.message.reply_text("✅ Xabaringiz adminga yuborildi!")

# --- Button click ---
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in ADMIN_IDS:
        await query.edit_message_text("❌ Bu tugma faqat admin uchun.")
        return

    data = query.data
    if data.startswith("reply_"):
        _, user_id, msg_id = data.split("_")
        reply_targets[query.from_user.id] = {
            "user_id": int(user_id),
            "message_id": int(msg_id)
        }
        await query.message.reply_text("✏️ Javob matnini yozing:")

# --- Main ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CommandHandler("reply", reply_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("send", send_cmd))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
