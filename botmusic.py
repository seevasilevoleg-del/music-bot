from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import yt_dlp
import os

TOKEN = '8921323726:AAGx4PAeG3oyFGI0gDk1EsLUEeVLqV9GsDI'

search_results = {}

async def start(update, context):
    await update.message.reply_text(
        "🎵 **Музыкальный бот!**\n\n"
        "Напиши название песни или исполнителя,\n"
        "например: **Баста**\n\n"
        "Выбери номер песни из списка!"
    )

async def search_songs(update, context):
    query = update.message.text.strip()
    if len(query) < 2:
        await update.message.reply_text("⚠️ Напиши название песни!")
        return
    
    await update.message.reply_text(f"🔍 Ищу: {query}...")
    
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch5:{query}", download=False)
            entries = info.get('entries', [])
            
            if not entries:
                await update.message.reply_text("❌ Ничего не найдено!")
                return
            
            chat_id = update.effective_chat.id
            search_results[chat_id] = entries
            
            keyboard = []
            for i, entry in enumerate(entries):
                title = entry.get('title', f'Песня {i+1}')
                if len(title) > 40:
                    title = title[:40] + '...'
                keyboard.append([InlineKeyboardButton(f"{i+1}. {title}", callback_data=f"song_{i}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"🎵 Найдено {len(entries)} песен. Выбери номер:",
                reply_markup=reply_markup
            )
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def handle_song_selection(update, context):
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    song_index = int(query.data.split('_')[1])
    entries = search_results.get(chat_id, [])
    
    if song_index >= len(entries):
        await query.edit_message_text("❌ Ошибка! Попробуй заново.")
        return
    
    entry = entries[song_index]
    title = entry.get('title', 'Песня')
    video_id = entry.get('id')
    youtube_url = f"https://youtube.com/watch?v={video_id}"
    
    await query.edit_message_text(f"⏳ Скачиваю: {title}...")
    
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'song.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
            
            with open('song.mp3', 'rb') as audio:
                await query.message.reply_audio(audio, title=title)
            
            os.remove('song.mp3')
            await query.message.delete()
            
    except Exception as e:
        await query.message.reply_text(f"❌ Ошибка при скачивании: {str(e)}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler('start', start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_songs))
app.add_handler(CallbackQueryHandler(handle_song_selection, pattern='song_'))

print("🎵 Бот запущен!")
app.run_polling()
