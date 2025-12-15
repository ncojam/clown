import logging
import random
import json
import os
from datetime import datetime, date
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = "my_token"

# Файл для сохранения статистики
STATS_FILE = "clown_stats.json"
# Файл для сохранения последнего использования
LAST_USED_FILE = "last_used.json"
# Словарь для хранения последнего использования команды по чатам
last_used = {}

def load_stats():
    """Загружает статистику из файла"""
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_stats(stats):
    """Сохраняет статистику в файл"""
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def load_last_used():
    """Загружает даты последнего использования"""
    if os.path.exists(LAST_USED_FILE):
        with open(LAST_USED_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_last_used():
    """Сохраняет даты последнего использования"""
    with open(LAST_USED_FILE, 'w', encoding='utf-8') as f:
        json.dump(last_used, f, ensure_ascii=False, indent=2)

async def get_chat_members(chat_id, bot):
    """Получает список участников чата"""
    members = []
    try:
        # Получаем список администраторов (обычно это работает)
        admins = await bot.get_chat_administrators(chat_id)
        for admin in admins:
            user = admin.user
            if not user.is_bot:
                members.append({
                    'id': user.id,
                    'first_name': user.first_name or "Unknown",
                    'username': user.username
                })
        
        # Если участников мало, добавляем отправителя команды как fallback
        if len(members) < 2:
            # Этот метод может не работать в больших группах без прав администратора
            # Но это лучшее, что мы можем сделать без специальных прав
            pass
            
    except Exception as e:
        logging.error(f"Error getting chat members: {e}")
        # Fallback - создаем фиктивных пользователей
        members = [
            {'id': 1, 'first_name': 'Вася', 'username': 'vasya'},
            {'id': 2, 'first_name': 'Петя', 'username': 'petya'},
            {'id': 3, 'first_name': 'Коля', 'username': 'kolya'},
            {'id': 4, 'first_name': 'Саша', 'username': 'sasha'},
            {'id': 5, 'first_name': 'Маша', 'username': 'masha'},
        ]
    
    return members

async def clown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /clown"""
    chat_id = str(update.effective_chat.id)
    today = str(date.today())
    
    # Проверяем, использовалась ли сегодня команда
    if chat_id in last_used and last_used[chat_id] == today:
        await show_today_stats(update, chat_id)
        return
    
    try:
        # Получаем список участников чата
        members = await get_chat_members(chat_id, context.bot)
        
        if not members:
            await update.message.reply_text("Не удалось получить список участников чата! 😢")
            return
        
        # Выбираем случайного участника
        winner = random.choice(members)
        
        # Первое сообщение - рандомная фраза
        phrases = [
            "Сейчас узнаем, кто скрывает слёзы позора за клоунским гримом - это... 🤡",
            "Кто же сегодня развлечёт народ своей жалкой жизнью? 🎪",
            "А кто тут больше всего любит жонглировать и вертеть жопой? 🤹‍",
            "Клоун дня и так всем известен... 👀",
            "Внимание! Сейчас узнаем, кто клоун! 👀",
            "А кто это забыл свой красный нос? 🔴",
            "Рекомендую носить красный нос постоянно, он замаскирует твой позор! 🔴",
            "Поздравляю с титулом 'Клоун дня'! Скидка 10% на все шутки про тебя! 🎪",
            "🔮 Магический шар говорит: 'Тот, кто сегодня проснётся клоуном...' Опа, это же...",
            "Да разве ж это соревнования? Ты с перевесом в 100% забираешь этот титул сегодня. 🥇",
            "Объявляю! Тот, чья жизнь и так комедия... 🤡",
            "Получай пирог в лицо! 🥧",
            "🎯 Сейчас определим сегоднюшнюю мишень для насмешек. Не забудь надеть свой парик!",
            "Кто жонглирует оправданиями лучше всех? 🤹‍",
            "Да ты не просто клоун, ты эталон! Заносим в учебники! 📚",
            "🍀 Не везёт в любви? Зато повезло стать клоуном дня!",
            "Секундочку, проверяю базу данных клоунов... 🗄️"
        ]
        
        first_message = await update.message.reply_text(random.choice(phrases))
        
        # Ждем 1 секунду
        import asyncio
        await asyncio.sleep(1)
        
        # Второе сообщение с результатом
        username = f"@{winner['username']}" if winner['username'] else winner['first_name']
        result_text = f"Клоун дня: {winner['first_name']} ({username})"
        
        await update.message.reply_text(result_text)
        
        # Обновляем статистику
        stats = load_stats()
        if chat_id not in stats:
            stats[chat_id] = {}
        
        user_key = f"{winner['id']}"
        if user_key not in stats[chat_id]:
            stats[chat_id][user_key] = {
                'name': winner['first_name'],
                'username': winner['username'] or '',
                'count': 0
            }
        
        stats[chat_id][user_key]['count'] += 1
        save_stats(stats)
        
        # Сохраняем дату последнего использования
        last_used[chat_id] = today
        save_last_used()
        
    except Exception as e:
        logging.error(f"Error in clown_command: {e}")
        await update.message.reply_text("Произошла ошибка! Попробуйте позже.")

async def show_today_stats(update: Update, chat_id: str):
    """Показывает сегодняшнюю статистику"""
    stats = load_stats()
    
    if chat_id in stats and stats[chat_id]:
        # Сортируем по количеству раз
        sorted_stats = sorted(
            stats[chat_id].items(), 
            key=lambda x: x[1]['count'], 
            reverse=True
        )
        
        response = "📊 Сегодняшний клоун уже выбран!\n\nСтатистика за все время:\n"
        for i, (user_id, user_data) in enumerate(sorted_stats[:10], 1):  # Топ-10
            username = f"@{user_data['username']}" if user_data['username'] else user_data['name']
            response += f"{i}. {user_data['name']} ({username}) - {user_data['count']} раз(а)\n"
        
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("Статистика пока пуста!")

async def clownstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /clownstats"""
    chat_id = str(update.effective_chat.id)
    stats = load_stats()
    
    if chat_id in stats and stats[chat_id]:
        # Сортируем по количеству раз
        sorted_stats = sorted(
            stats[chat_id].items(), 
            key=lambda x: x[1]['count'], 
            reverse=True
        )
        
        response = "🏆 Полная статистика клоунов:\n\n"
        for i, (user_id, user_data) in enumerate(sorted_stats, 1):
            username = f"@{user_data['username']}" if user_data['username'] else user_data['name']
            response += f"{i}. {user_data['name']} ({username}) - {user_data['count']} раз(а)\n"
        
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("Статистика пока пуста! Используйте /clown")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    help_text = """
🤖 Бот для определения клоуна дня!

Доступные команды:
/clown - Определить клоуна дня (раз в сутки)
/clownstats - Показать полную статистику
    """
    await update.message.reply_text(help_text)

def main():
    """Основная функция"""
    # Загружаем последние даты использования при старте
    global last_used
    last_used = load_last_used()
    
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("clown", clown_command))
    application.add_handler(CommandHandler("clownstats", clownstats_command))

    # Запускаем бота
    print("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# Сохраняем состояние при завершении
import atexit
import signal
import sys

def cleanup():
    """Функция очистки при завершении"""
    save_last_used()
    print("Данные сохранены. Бот завершает работу.")

atexit.register(cleanup)

def signal_handler(sig, frame):
    """Обработчик сигналов завершения"""
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    main()