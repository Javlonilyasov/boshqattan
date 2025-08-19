import os
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

TOKEN = "7810423105:AAGyuqAz6RfhhP1nIxdj8FbdUs9iHBk82ug"

# Random emoji reactionlar
REACTIONS = ["👍", "🔥", "😂", "❤️", "👏", "😮"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Menga Instagram link yubor 📥")

async def handle_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "instagram.com" not in url:
        return  # faqat instagram linklarga ishlasin

    progress_msg = await update.message.reply_text("⏳ Yuklab olinmoqda...")

    try:
        ydl_opts = {
            "outtmpl": "video.%(ext)s",
            "cookiefile": "cookies.txt",  # cookie fayl kerak bo'lishi mumkin
            "format": "mp4"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        caption_text = ""
        if update.message.from_user.username:
            caption_text = f"🎬 @{update.message.from_user.username} yubordi"
        else:
            caption_text = f"🎬 {update.message.from_user.first_name} yubordi"

        # Guruhda reply qilib yuborish
        if update.message.chat.type in ["group", "supergroup"]:
            sent_msg = await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=open(file_path, "rb"),
                caption=caption_text
            )

            # Havola yuborgan xabarni o'chirish
            try:
                await update.message.delete()
            except Exception as e:
                print("⚠️ Xabar o'chirilmadi:", e)

        else:  # shaxsiy chatda oddiy yuborish
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=open(file_path, "rb")
            )

        await progress_msg.delete()
        os.remove(file_path)

        # Random reaction bosish
        reaction = random.choice(REACTIONS)
        try:
            await context.bot.set_message_reaction(
                chat_id=update.effective_chat.id,
                message_id=sent_msg.message_id if update.message.chat.type in ["group", "supergroup"] else update.message.message_id,
                reaction=[reaction]
            )
        except Exception as e:
            print("⚠️ Reaction bosilmadi:", e)

    except Exception as e:
        await progress_msg.delete()
        await update.message.reply_text(f"❌ Xatolik: {e}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_instagram))
    print("✅ Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
