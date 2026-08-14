import os
import time
import threading
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

TOKEN = "8864516759:AAGFTzWxCyLHU_eQmlhx_G3FEBGttI7PLqQ"
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlayapti!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# YouTube va TikTok video yuklash sozlamasi
ydl_opts_video = {
    'format': 'best',
    'outtmpl': 'video.mp4',
    'noplaylist': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'quiet': True,
    'nocheckcertificate': True
}

# Musiqa yuklash sozlamasi (MP3)
ydl_opts_audio = {
    'format': 'bestaudio/best',
    'outtmpl': 'audio.mp3',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'quiet': True,
    'nocheckcertificate': True
}

# 1. Havolalar kelganda (YouTube / TikTok video)
@bot.message_handler(func=lambda msg: any(domain in msg.text for domain in ['tiktok.com', 'youtu.be', 'youtube.com']))
def handle_social_media(message):
    status = bot.reply_to(message, "⚡️ Video yuklanmoqda...")
    url = message.text.strip().split()[0]
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
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

# 2. Artist yoki musiqa nomi yozilganda (10 tagacha musiqa chiqarish)
@bot.message_handler(func=lambda msg: not any(domain in msg.text for domain in ['tiktok.com', 'youtu.be', 'youtube.com']))
def search_music(message):
    query = message.text.strip()
    status = bot.reply_to(message, f"🔍 '{query' bo'yicha musiqalar qidirilmoqda...")
    
    try:
        search_opts = {
            'default_search': 'ytsearch10',
            'format': 'bestaudio',
            'quiet': True,
            'nocheckcertificate': True
        }
        
        with yt_dlp.YoutubeDL(search_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            
        entries = info.get('entries', [])
        if not entries:
            bot.edit_message_text("❌ Hech qanday musiqa topilmadi.", message.chat.id, status.message_id)
            return
            
        markup = InlineKeyboardMarkup()
        for i, entry in enumerate(entries):
            title = entry.get('title', 'Musiqa')
            url = entry.get('webpage_url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
            # Tugma matni uzun bo'lib ketmasligi uchun qisqartiramiz
            if len(title) > 35:
                title = title[:32] + "..."
            markup.add(InlineKeyboardButton(f"{i+1}. {title}", callback_data=f"dl_{entry.get('id')}"))
            
        bot.edit_message_text("🎵 **Quyidagi musiqalardan birini tanlang:**", message.chat.id, status.message_id, reply_markup=markup, parse_mode="Markdown")
        
    except Exception as e:
        bot.edit_message_text(f"❌ Qidirishda xatolik yuz berdi: {e}", message.chat.id, status.message_id)

# 3. Tugmani bosganda musiqani yuklab yuborish
@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def callback_download_audio(call):
    video_id = call.data.split('_')[1]
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    bot.answer_callback_query(call.id, "Musiqa yuklanmoqda, ozgina kuting...")
    status = bot.send_message(call.message.chat.id, "📥 Musiqa yuklab olinmoqda...")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
            ydl.download([url])
            
        audio_file = None
        for file in os.listdir('.'):
            if file.endswith('.mp3'):
                audio_file = file
                break
                
        if audio_file and os.path.exists(audio_file):
            with open(audio_file, 'rb') as aud:
                bot.send_audio(call.message.chat.id, aud, caption="🎧 **@taronatopmusicbot**", parse_mode="Markdown")
            bot.delete_message(call.message.chat.id, status.message_id)
            os.remove(audio_file)
        else:
            bot.edit_message_text("❌ Musiqani yuklab bo'lmadi.", call.message.chat.id, status.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik: {e}", call.message.chat.id, status.message_id)

def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=15, long_polling_timeout=10)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
    
