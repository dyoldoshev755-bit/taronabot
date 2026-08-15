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

# YouTube va TikTok video yuklash sozlamalari (iOS client orqali)
ydl_opts_video = {
    'format': 'best',
    'outtmpl': 'video.mp4',
    'noplaylist': True,
    'quiet': True,
    'nocheckcertificate': True,
    'extractor_args': {'youtube': {'player_client': ['ios', 'web']}}
}

# Musiqa yuklash sozlamalari (MP3)
ydl_opts_audio = {
    'format': 'bestaudio/best',
    'outtmpl': 'audio.mp3',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'quiet': True,
    'nocheckcertificate': True,
    'extractor_args': {'youtube': {'player_client': ['ios', 'web']}}
}

# 1. Video havolalari kelganda (YouTube yoki TikTok)
@bot.message_handler(func=lambda msg: msg.text and any(d in msg.text for d in ['tiktok.com', 'youtu.be', 'youtube.com']))
def download_video(message):
    sent_msg = bot.reply_to(message, "⚡️ Video yuklanmoqda, kuting...")
    url = message.text.strip().split()[0]
    try:
        with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
            ydl.download([url])
        
        if os.path.exists('video.mp4'):
            with open('video.mp4', 'rb') as v:
                bot.send_video(message.chat.id, v, caption="📥 **@taronatopmusicbot orqali yuklandi!**", parse_mode="Markdown")
            bot.delete_message(message.chat.id, sent_msg.message_id)
            os.remove('video.mp4')
        else:
            bot.edit_message_text("❌ Video topilmadi.", message.chat.id, sent_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik: {e}", message.chat.id, sent_msg.message_id)

# 2. Artist yoki musiqa nomi yozilganda qidirish
@bot.message_handler(func=lambda msg: msg.text and not any(d in msg.text for d in ['tiktok.com', 'youtu.be', 'youtube.com']))
def search_music(message):
    query = message.text.strip()
    sent_msg = bot.reply_to(message, f"🔍 '{query}' bo'yicha musiqalar qidirilmoqda...")
    
    try:
        search_opts = {
            'format': 'bestaudio',
            'quiet': True,
            'nocheckcertificate': True,
            'extractor_args': {'youtube': {'player_client': ['ios', 'web']}}
        }
        with yt_dlp.YoutubeDL(search_opts) as ydl:
            info = ydl.extract_info(f"ytsearch10:{query}", download=False)
            
        entries = info.get('entries', [])
        if not entries:
            bot.edit_message_text("❌ Hech qanday musiqa topilmadi.", message.chat.id, sent_msg.message_id)
            return
            
        markup = InlineKeyboardMarkup()
        for i, entry in enumerate(entries):
            title = entry.get('title', 'Musiqa')
            video_id = entry.get('id')
            if len(title) > 35:
                title = title[:32] + "..."
            markup.add(InlineKeyboardButton(f"{i+1}. {title}", callback_data=f"mus_{video_id}"))
            
        bot.edit_message_text("🎵 **Topilgan musiqalar (birini tanlang):**", message.chat.id, sent_msg.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ Qidirishda xatolik: {e}", message.chat.id, sent_msg.message_id)

# 3. Tugmani bosganda musiqani MP3 qilib yuborish
@bot.callback_query_handler(func=lambda call: call.data.startswith('mus_'))
def send_audio(call):
    video_id = call.data.split('_')[1]
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    bot.answer_callback_query(call.id, "Musiqa yuklanmoqda...")
    sent_msg = bot.send_message(call.message.chat.id, "📥 Musiqa tayyorlanmoqda, ozgina kuting...")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
            ydl.download([url])
            
        audio_file = None
        for f in os.listdir('.'):
            if f.endswith('.mp3'):
                audio_file = f
                break
                
        if audio_file and os.path.exists(audio_file):
            with open(audio_file, 'rb') as aud:
                bot.send_audio(call.message.chat.id, aud, caption="🎧 **@taronatopmusicbot**", parse_mode="Markdown")
            bot.delete_message(call.message.chat.id, sent_msg.message_id)
            os.remove(audio_file)
        else:
            bot.edit_message_text("❌ Musiqali faylni topib bo'lmadi.", call.message.chat.id, sent_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Yuklashda xatolik: {e}", call.message.chat.id, sent_msg.message_id)

def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception:
            time.sleep(3)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
                               
        
