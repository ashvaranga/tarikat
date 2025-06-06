import os
import telebot
from telebot import types
import yadisk

# Настройки
TELEGRAM_TOKEN = "7922205304:AAG-YuGcaIlYdFgS_huR6vBe5fjGqHVAVC4"
YANDEX_TOKEN = "y0__xDJ7-CTARjCljgg0PvqtBMwt9GCjQgK-auQxCwObRrCQA2vdd7HIVWa4A"
WORK_DIRECTORY = "/Тарикат/Тарикат полисы"  # Рабочая папка на Яндекс.Диске

# Инициализация
bot = telebot.TeleBot(TELEGRAM_TOKEN)
y = yadisk.YaDisk(token=YANDEX_TOKEN)

# Создаем постоянную клавиатуру
def create_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True)
    markup.add(types.KeyboardButton('🔍 Найти полис'))
    return markup

# Команда /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome_text = """
 <b>Полисы теперь здесь=)</b>

Для поиска:
1. Нажмите кнопку <b>"🔍 Найти полис"</b> 
2. Или просто введите номер полиса
"""
    bot.send_message(message.chat.id, welcome_text, 
                   parse_mode="HTML",
                   reply_markup=create_keyboard())

# Обработка ВСЕХ текстовых сообщений
@bot.message_handler(content_types=['text'])
def handle_text(message):
    try:
        # Если нажали кнопку поиска
        if message.text == '🔍 Найти полис':
            msg = bot.send_message(message.chat.id, "🔍 Введите номер полиса:", 
                                 reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, process_search)
            return
            
        # Если ввели текст напрямую (не кнопку)
        else:
            process_search(message)
            
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ошибка: {str(e)}",
                       reply_markup=create_keyboard())

# Обработка поиска (общая функция)
def process_search(message):
    try:
        search_query = message.text.strip()
        
        if not search_query:
            bot.send_message(message.chat.id, "❌ Введите номер полиса", 
                           reply_markup=create_keyboard())
            return

        found_files = []
        for item in y.listdir(WORK_DIRECTORY):
            if item.name.lower().endswith('.pdf') and search_query.lower() in item.name.lower():
                found_files.append(item.name)

        if not found_files:
            bot.send_message(message.chat.id, f"❌ Полис с номером '{search_query}' не найден",
                           reply_markup=create_keyboard())
            return

        if len(found_files) == 1:
            send_pdf_file(message.chat.id, found_files[0])
        else:
            show_search_results(message.chat.id, found_files)
            
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ошибка: {str(e)}",
                       reply_markup=create_keyboard())

# Отправка файла (без изменений)
def send_pdf_file(chat_id, file_name):
    try:
        file_path = f"{WORK_DIRECTORY}/{file_name}"
        local_path = f"temp_{file_name}"
        
        y.download(file_path, local_path)
        with open(local_path, "rb") as file:
            bot.send_document(chat_id, file, caption=f"📄 {file_name}")
        os.remove(local_path)
        
        bot.send_message(chat_id, "найти ещё?", 
                       reply_markup=create_keyboard())
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при отправке файла: {str(e)}",
                       reply_markup=create_keyboard())

# Показать результаты поиска (без изменений)
def show_search_results(chat_id, files):
    markup = types.InlineKeyboardMarkup()
    for file in files[:20]:
        markup.add(types.InlineKeyboardButton(
            text=file,
            callback_data=f"download_{file}"
        ))
    
    bot.send_message(chat_id, 
                   f"🔍 Найдено {len(files)} полисов. Выберите нужный:",
                   reply_markup=markup)

# Обработка нажатия на файл (без изменений)
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        if call.data.startswith('download_'):
            file_name = call.data.replace('download_', '')
            send_pdf_file(call.message.chat.id, file_name)
            bot.answer_callback_query(call.id, "Полис отправлен")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {str(e)}")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)
