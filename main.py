import logging
import random
import json
import os
from datetime import datetime, date
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")

# Файлы для данных
STATS_FILE = "clown_stats.json"
LAST_USED_FILE = "last_used.json"
MEMBERS_FILE = "chat_members.json"  # Новый файл для хранения участников

# Словари для данных
last_used = {}
chat_members = {}  # Словарь для хранения участников по чатам

def load_members():
    """Загружает список участников из файла"""
    global chat_members
    if os.path.exists(MEMBERS_FILE):
        try:
            with open(MEMBERS_FILE, 'r', encoding='utf-8') as f:
                chat_members = json.load(f)
                logging.info(f"Загружены участники для {len(chat_members)} чатов")
        except Exception as e:
            logging.error(f"Ошибка загрузки участников: {e}")
            chat_members = {}
    else:
        chat_members = {}
        logging.info("Файл участников не найден, создан пустой список")

def save_members():
    """Сохраняет список участников в файл"""
    try:
        with open(MEMBERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(chat_members, f, ensure_ascii=False, indent=2)
        logging.info("Список участников сохранен")
    except Exception as e:
        logging.error(f"Ошибка сохранения участников: {e}")

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

def get_members_for_chat(chat_id):
    """Получает список участников для указанного чата"""
    chat_id_str = str(chat_id)
    if chat_id_str in chat_members:
        members = chat_members[chat_id_str]
        # Фильтруем активных участников
        active_members = [m for m in members if m.get('active', True)]
        logging.info(f"Для чата {chat_id} найдено {len(active_members)} активных участников из {len(members)}")
        return active_members
    else:
        logging.warning(f"Для чата {chat_id} нет списка участников")
        return []

async def clown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /clown"""
    try:
        logging.info(f"=== START clown_command ===")
        logging.info(f"Chat ID: {update.effective_chat.id}")
        logging.info(f"Chat type: {update.effective_chat.type}")
        logging.info(f"From user: {update.effective_user.id if update.effective_user else 'None'}")
        
        chat_id = str(update.effective_chat.id)
        today = str(date.today())
        logging.info(f"Today: {today}")
        logging.info(f"Last used data loaded: {len(last_used)} chats")
        
        # Проверяем, использовалась ли сегодня команда
        if chat_id in last_used and last_used[chat_id] == today:
            logging.info(f"Command already used today in chat {chat_id}. Showing stats...")
            await show_today_stats(update, chat_id)
            logging.info(f"=== END clown_command (already used today) ===")
            return
    
        try:
            logging.info(f"Getting members for chat {chat_id}...")
            members = get_members_for_chat(chat_id)
            logging.info(f"Found: {len(members)} members")
            
            if not members:
                logging.error(f"No members found for chat {chat_id}!")
                response = (
                    "❌ Нет списка участников для этого чата!\n\n"
                    "Администратор должен добавить участников командой:\n"
                    "/addmember @username - добавить участника\n"
                    "/listmembers - показать список участников\n"
                    "Или использовать /initmembers для создания списка из администраторов"
                )
                await update.message.reply_text(response)
                logging.info(f"=== END clown_command (no members) ===")
                return
            
            # Логируем первых 3 участника для проверки
            for i, member in enumerate(members[:3]):
                logging.info(f"Member {i}: ID={member.get('id')}, Name={member.get('name')}, Username={member.get('username')}")
            
            # Выбираем случайного участника
            logging.info(f"Selecting random winner from {len(members)} members...")
            winner = random.choice(members)
            logging.info(f"Winner selected: ID={winner.get('id')}, Name={winner.get('name')}, Username={winner.get('username')}")
            
            # Получаем фразы для этого чата на основе его режима
            chat_phrases = get_phrases_for_chat(update.effective_chat.id)
            phrases = chat_phrases.get('pre', phrases_data.get('default', {}).get('pre', ["Кто же сегодня будет выбран? 🤔"]))
            
            logging.info(f"Sending first message...")
            first_message = await update.message.reply_text(random.choice(phrases))
            logging.info(f"First message sent with ID: {first_message.message_id}")
            
            # Ждем 1 секунду
            import asyncio
            logging.info(f"Sleeping for 1 second...")
            await asyncio.sleep(1)
            logging.info(f"Sleep completed")
            
            # Второе сообщение с результатом
            winner_name = winner.get('name', 'Неизвестный')
            winner_username = winner.get('username', '')
            username_display = f"@{winner_username}" if winner_username else winner_name
            
            result_template = chat_phrases.get(
                'result', 
                phrases_data.get('default', {}).get('result', "{name} ({username})")
            )
            result_text = result_template.format(name=winner_name, username=username_display)
            logging.info(f"Result text: {result_text}")
            
            await update.message.reply_text(result_text)
            logging.info(f"Result message sent")
            
            # Обновляем статистику
            logging.info(f"Loading stats...")
            stats = load_stats()
            logging.info(f"Loaded stats for {len(stats)} chats")
            
            if chat_id not in stats:
                logging.info(f"Chat {chat_id} not in stats, creating new entry")
                stats[chat_id] = {}
            
            # Используем ID или username как ключ
            user_key = str(winner.get('id')) if winner.get('id') else f"user_{winner_username}"
            logging.info(f"User key: {user_key}")
            
            if user_key not in stats[chat_id]:
                logging.info(f"User {user_key} not in chat stats, creating new entry")
                stats[chat_id][user_key] = {
                    'name': winner_name,
                    'username': winner_username,
                    'count': 0
                }
            else:
                logging.info(f"User {user_key} already in stats. Current count: {stats[chat_id][user_key]['count']}")
            
            stats[chat_id][user_key]['count'] += 1
            logging.info(f"Updated count for user {user_key}: {stats[chat_id][user_key]['count']}")
            
            save_stats(stats)
            logging.info(f"Stats saved")
            
            # Сохраняем дату последнего использования
            last_used[chat_id] = today
            save_last_used()
            logging.info(f"Last used updated for chat {chat_id}: {today}")
            
            logging.info(f"=== END clown_command (success) ===")
            
        except Exception as inner_e:
            logging.error(f"INNER ERROR in clown_command: {inner_e}", exc_info=True)
            logging.error(f"Error type: {type(inner_e)}")
            logging.error(f"Error args: {inner_e.args}")
            await update.message.reply_text("Произошла внутренняя ошибка при выполнении команды! 🔧")
            
    except Exception as e:
        logging.error(f"OUTER ERROR in clown_command: {e}", exc_info=True)
        logging.error(f"Full error traceback:", exc_info=True)
        await update.message.reply_text("Произошла критическая ошибка! Попробуйте позже. ⚠️")

async def addmember_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавляет участника в список"""
    chat_id = str(update.effective_chat.id)
    
    if not context.args:
        await update.message.reply_text(
            "Использование: /addmember @username [имя]\n"
            "Пример: /addmember @ivanov Иван\n"
            "Или: /addmember @ivanov"
        )
        return
    
    username = context.args[0]
    if not username.startswith('@'):
        username = '@' + username
    
    # Убираем @ для хранения
    username_clean = username[1:]
    
    # Проверяем есть ли имя
    name = context.args[1] if len(context.args) > 1 else username_clean
    
    # Инициализируем список участников для чата если нужно
    if chat_id not in chat_members:
        chat_members[chat_id] = []
    
    # Проверяем, есть ли уже такой участник
    for member in chat_members[chat_id]:
        if member.get('username') == username_clean:
            await update.message.reply_text(f"❌ Участник {username} уже в списке!")
            return
    
    # Добавляем нового участника
    new_member = {
        'username': username_clean,
        'name': name,
        'active': True,
        'added_by': update.effective_user.username or update.effective_user.first_name,
        'added_date': str(date.today())
    }
    
    chat_members[chat_id].append(new_member)
    save_members()
    
    await update.message.reply_text(f"✅ Добавлен участник: {name} ({username})")

async def removemember_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет участника из списка"""
    chat_id = str(update.effective_chat.id)
    
    if not context.args:
        await update.message.reply_text(
            "Использование: /removemember @username\n"
            "Пример: /removemember @ivanov"
        )
        return
    
    username = context.args[0]
    if not username.startswith('@'):
        username = '@' + username
    
    username_clean = username[1:]
    
    if chat_id not in chat_members:
        await update.message.reply_text("❌ Для этого чата нет списка участников!")
        return
    
    # Ищем и удаляем участника
    original_length = len(chat_members[chat_id])
    chat_members[chat_id] = [
        m for m in chat_members[chat_id] 
        if m.get('username') != username_clean
    ]
    
    if len(chat_members[chat_id]) < original_length:
        save_members()
        await update.message.reply_text(f"✅ Участник {username} удален из списка")
    else:
        await update.message.reply_text(f"❌ Участник {username} не найден в списке")

async def listmembers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список участников"""
    chat_id = str(update.effective_chat.id)
    
    if chat_id not in chat_members or not chat_members[chat_id]:
        await update.message.reply_text("📭 Список участников пуст!")
        return
    
    members = chat_members[chat_id]
    active_count = len([m for m in members if m.get('active', True)])
    
    response = f"👥 Участники чата ({active_count} активных из {len(members)}):\n\n"
    
    for i, member in enumerate(members, 1):
        status = "✅" if member.get('active', True) else "❌"
        username = f"@{member['username']}" if member.get('username') else "без @"
        name = member.get('name', 'Без имени')
        added_by = f"добавил: {member.get('added_by', 'неизвестно')}"
        
        response += f"{i}. {status} {name} {username}\n"
        if member.get('added_by'):
            response += f"   👤 {added_by}\n"
    
    await update.message.reply_text(response)

async def initmembers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Инициализирует список участников из администраторов чата"""
    chat_id = str(update.effective_chat.id)
    
    try:
        # Получаем администраторов чата
        admins = await context.bot.get_chat_administrators(chat_id)
        
        if chat_id not in chat_members:
            chat_members[chat_id] = []
        
        added_count = 0
        for admin in admins:
            user = admin.user
            
            # Пропускаем ботов
            if user.is_bot:
                continue
            
            username = user.username or ""
            name = user.first_name or user.username or "Без имени"
            
            # Проверяем, есть ли уже такой участник
            exists = any(
                m.get('username') == username 
                for m in chat_members[chat_id]
            )
            
            if not exists and username:
                new_member = {
                    'id': user.id,
                    'username': username,
                    'name': name,
                    'active': True,
                    'added_by': 'system',
                    'added_date': str(date.today())
                }
                chat_members[chat_id].append(new_member)
                added_count += 1
        
        save_members()
        
        if added_count > 0:
            await update.message.reply_text(
                f"✅ Добавлено {added_count} администраторов в список участников!\n"
                f"Используйте /listmembers для просмотра"
            )
        else:
            await update.message.reply_text(
                "ℹ️ Новые администраторы не найдены или уже есть в списке"
            )
            
    except Exception as e:
        logging.error(f"Error in initmembers: {e}")
        await update.message.reply_text(
            "❌ Не удалось получить список администраторов.\n"
            "Убедитесь, что бот является администратором чата!"
        )

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
        
        # Получаем режим чата для правильного названия
        mode = get_chat_mode(chat_id)
        mode_names = {
            'clown': '🤡 клоун',
            'pidor': '🏳️‍🌈 пидор',
            'default': '🎯 победитель'
        }
        mode_name = mode_names.get(mode, 'победитель')
        
        response = f"📊 Сегодняшний {mode_name} уже выбран!\n\nСтатистика за все время:\n"
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
        
        # Получаем режим чата для правильного названия
        mode = get_chat_mode(chat_id)
        mode_names = {
            'clown': '🤡 клоунов',
            'pidor': '🏳️‍🌈 пидоров',
            'default': '🎯 победителей'
        }
        mode_name = mode_names.get(mode, 'победителей')
        
        response = f"🏆 Полная статистика {mode_name}:\n\n"
        for i, (user_id, user_data) in enumerate(sorted_stats, 1):
            username = f"@{user_data['username']}" if user_data['username'] else user_data['name']
            response += f"{i}. {user_data['name']} ({username}) - {user_data['count']} раз(а)\n"
        
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("Статистика пока пуста! Используйте /clown")
        
# Загрузка фраз из общего файла
PHRASES_FILE = "phrases.json"

def load_phrases():
    """Загружает фразы из общего файла"""
    if os.path.exists(PHRASES_FILE):
        with open(PHRASES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}  # fallback

phrases_data = load_phrases()

# Загрузка настроек групп
GROUP_SETTINGS_FILE = "group_settings.json"

def load_group_settings():
    """Загружает настройки для всех групп"""
    if os.path.exists(GROUP_SETTINGS_FILE):
        with open(GROUP_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_group_settings(settings):
    """Сохраняет настройки групп"""
    with open(GROUP_SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

group_settings = load_group_settings()

def get_chat_mode(chat_id):
    """Получает режим для конкретного чата"""
    chat_id_str = str(chat_id)
    mode = group_settings.get(chat_id_str, 'clown')  # По умолчанию 'clown'
    
    # Проверяем, есть ли фразы для этого режима
    if mode in phrases_data:
        return mode
    else:
        return 'default'  # fallback

def get_phrases_for_chat(chat_id):
    """Получает фразы для конкретного чата на основе его режима"""
    mode = get_chat_mode(chat_id)
    return phrases_data.get(mode, phrases_data.get('default', {}))

async def setmode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Устанавливает режим для конкретной группы"""
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id
    
    # Проверяем права администратора
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        is_admin = any(admin.user.id == user_id for admin in admins)
        
        if not is_admin:
            await update.message.reply_text("❌ Только администраторы могут менять режим бота!")
            return
    except Exception as e:
        await update.message.reply_text("❌ Не удалось проверить права администратора!")
        return
    
    if not context.args:
        current_mode = get_chat_mode(chat_id)
        await update.message.reply_text(
            f"📋 Текущий режим для этой группы: **{current_mode}**\n\n"
            f"Доступные режимы: clown, pidor\n"
            f"Использование: /setmode clown или /setmode pidor"
        )
        return
    
    new_mode = context.args[0].lower()
    if new_mode not in ['clown', 'pidor']:
        await update.message.reply_text("❌ Доступные режимы: clown, pidor")
        return
    
    # Сохраняем настройку для группы
    group_settings[chat_id] = new_mode
    save_group_settings(group_settings)
    
    await update.message.reply_text(
        f"✅ Режим для этой группы изменён на: **{new_mode}**\n\n"
        f"Теперь команда /clown будет использовать соответствующие фразы."
    )

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    help_text = """
🤖 Бот для определения клоуна/пидора дня!

🎪 Основные команды:
/clown или /pidor - Определить победителя дня (раз в сутки)
/clownstats или /pidorstats - Показать полную статистику

⚙️ Настройка режима (для администраторов):
/setmode clown - переключить на режим "Клоун дня"
/setmode pidor - переключить на режим "Пидор дня"
/setmode - показать текущий режим

👥 Управление участниками (для администраторов):
/addmember @username имя - добавить участника
/removemember @username - удалить участника
/listmembers - показать список участников
/initmembers - создать список из администраторов чата

📝 Пример:
/addmember @ivanov Иван
/addmember @petrov Петр
"""
    await update.message.reply_text(help_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await start_command(update, context)

def main():
    """Основная функция"""
    # Загружаем данные при старте
    global last_used
    last_used = load_last_used()
    load_members()
    
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clown", clown_command))
    application.add_handler(CommandHandler("pidor", clown_command))
    application.add_handler(CommandHandler("clownstats", clownstats_command))
    application.add_handler(CommandHandler("pidorstats", clownstats_command))
    application.add_handler(CommandHandler("addmember", addmember_command))
    application.add_handler(CommandHandler("removemember", removemember_command))
    application.add_handler(CommandHandler("listmembers", listmembers_command))
    application.add_handler(CommandHandler("initmembers", initmembers_command))
    application.add_handler(CommandHandler("setmode", setmode_command))

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
    save_members()
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