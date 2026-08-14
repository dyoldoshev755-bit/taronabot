import os
import time
import threading
from flask import Flask
import telebot
import yt_dlp

TOKEN = "8864516759:AAGFTzWxCyLHU_eQmlhx_G3FEBGttI7PLqQ"
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlayapti!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

ydl_opts = {
    'format': 'best',
    'outtmpl': 'video.mp4',
    'noplaylist': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'quiet': True,
    'nocheckcertificate': True
}

@bot.message_handler(func=lambda msg: any(domain in msg.text for domain in ['tiktok.com', 'youtu.be', 'youtube.com']))
def handle_social_media(message):
    status = bot.reply_to(message, "⚡️ Video yuklanmoqda...")
    url = message.text.strip().split()[0]
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        if os.path.exists('video.mp4'):
            success = False
            for attempt in range(3):
                try:
                    with open('video.mp4', 'rb') as v:
                        bot.send_video(message.chat.id, v, caption="📥 **@taronatopmusicbot orqali yuklandi!**", parse_mode="Markdown")
                    success = True
                    break
                except Exception:
                    time.sleep(2)
            
            bot.delete_message(message.chat.id, status.message_id)
            os.remove('video.mp4')
            
            if not success:
                bot.send_message(message.chat.id, "❌ Videoni yuborib bo'lmadi.")
        else:
            bot.edit_message_text("❌ Video topilmadi.", message.chat.id, status.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik yuz berdi: {e}", message.chat.id, status.message_id)

def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=15, long_polling_timeout=10)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
                        
