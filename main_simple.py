# main_simple.py
import telebot
import json
import os
import random
import logging
from datetime import date
from dotenv import load_dotenv
import atexit
import signal
import sys

load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")

# Файлы для данных
STATS_FILE = "clown_stats.json"
LAST_USED_FILE = "last_used.json"
MEMBERS_FILE = "chat_members.json"
PHRASES_FILE = "phrases.json"
GROUP_SETTINGS_FILE = "group_settings.json"

# Данные
last_used = {}
chat_members = {}
phrases_data = {}
group_settings = {}

def load_json(filepath, default=None):
    """Загружает JSON файл"""
    if default is None:
        default = {}
    logger.info(f"Загрузка {filepath}...")
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"✅ Загружен {filepath}: {len(data)} записей")
                return data
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки {filepath}: {e}")
    logger.info(f"⚠️ Файл {filepath} не найден, создан пустой")
    return default

def save_json(filepath, data):
    """Сохраняет JSON файл"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"✅ Сохранён {filepath}")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения {filepath}: {e}")

def load_data():
    """Загружает все данные"""
    global last_used, chat_members, phrases_data, group_settings
    
    logger.info("📂 Загрузка данных...")
    last_used = load_json(LAST_USED_FILE)
    chat_members = load_json(MEMBERS_FILE)
    phrases_data = load_json(PHRASES_FILE)
    group_settings = load_json(GROUP_SETTINGS_FILE)
    
    if phrases_data:
        logger.info(f"Загружены режимы фраз: {list(phrases_data.keys())}")
    
    logger.info("✅ Данные загружены")

def save_data():
    """Сохраняет все данные"""
    logger.info("💾 Сохранение данных...")
    save_json(LAST_USED_FILE, last_used)
    save_json(MEMBERS_FILE, chat_members)
    save_json(GROUP_SETTINGS_FILE, group_settings)
    logger.info("✅ Данные сохранены")

def get_chat_mode(chat_id):
    """Получает режим чата"""
    chat_id_str = str(chat_id)
    mode = group_settings.get(chat_id_str, 'clown')
    if mode not in phrases_data:
        mode = 'default'
    return mode

def get_phrases(chat_id):
    """Получает фразы для чата"""
    mode = get_chat_mode(chat_id)
    return phrases_data.get(mode, phrases_data.get('default', {}))

# Создаём бота
logger.info("🔧 Создание бота...")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')
logger.info("✅ Бот создан")

# ========== ОБРАБОТЧИКИ КОМАНД ==========

@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработчик /start"""
    logger.info(f"Команда /start от {message.from_user.id} в чате {message.chat.id}")
    
    help_text = """
🤖 <b>Бот для определения клоуна/пидора дня!</b>

🎪 <b>Основные команды:</b>
/clown или /pidor - Определить победителя дня (раз в сутки)
/clownstats или /pidorstats - Показать полную статистику

📝 <b>Саморегистрация:</b>
/register - Добавить себя в список участников
/unregister - Удалить себя из списка участников

⚙️ <b>Настройка режима:</b>
/setmode clown - переключить на режим "Клоун дня"
/setmode pidor - переключить на режим "Пидор дня"

👥 <b>Управление участниками:</b>
/addmember @username имя - добавить участника
/removemember @username - удалить участника
/listmembers - показать список участников
/initmembers - создать список из администраторов
"""
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['help'])
def help_command(message):
    start_command(message)

@bot.message_handler(commands=['clown', 'pidor'])
def clown_command(message):
    """Выбор клоуна/пидора дня"""
    chat_id = str(message.chat.id)
    today = str(date.today())
    
    logger.info(f"Команда clown от {message.from_user.id} в чате {chat_id}")
    
    # Проверяем, использовали ли сегодня
    if chat_id in last_used and last_used[chat_id] == today:
        logger.info(f"В чате {chat_id} уже выбирали сегодня")
        show_stats(message, chat_id)
        return
    
    # Получаем участников
    members = chat_members.get(chat_id, [])
    active_members = [m for m in members if m.get('active', True)]
    
    if not active_members:
        logger.warning(f"Нет участников в чате {chat_id}")
        bot.reply_to(message, 
            "❌ Нет списка участников для этого чата!\n\n"
            "Используйте:\n"
            "/addmember @username - добавить участника\n"
            "/initmembers - создать список из администраторов"
        )
        return
    
    # Выбираем победителя
    winner = random.choice(active_members)
    logger.info(f"Победитель в чате {chat_id}: {winner.get('name')} (@{winner.get('username')})")
    
    # Фразы
    phrases = get_phrases(message.chat.id)
    pre_phrases = phrases.get('pre', ["Кто же сегодня будет выбран? 🤔"])
    bot.reply_to(message, random.choice(pre_phrases))
    
    import time
    time.sleep(1)
    
    # Результат
    winner_name = winner.get('name', 'Неизвестный')
    winner_username = winner.get('username', '')
    username_display = f"@{winner_username}" if winner_username else winner_name
    
    result_template = phrases.get('result', "{name} ({username})")
    result_text = result_template.format(name=winner_name, username=username_display)
    bot.send_message(message.chat.id, result_text)
    
    # Обновляем статистику
    stats = load_json(STATS_FILE)
    if chat_id not in stats:
        stats[chat_id] = {}
    
    user_key = winner_username or str(winner.get('id', winner_name))
    
    if user_key not in stats[chat_id]:
        stats[chat_id][user_key] = {
            'name': winner_name,
            'username': winner_username,
            'count': 0
        }
    
    stats[chat_id][user_key]['count'] += 1
    save_json(STATS_FILE, stats)
    
    # Сохраняем дату
    last_used[chat_id] = today
    save_data()
    
    logger.info(f"✅ Команда clown выполнена для чата {chat_id}")

def show_stats(message, chat_id):
    """Показывает статистику"""
    stats = load_json(STATS_FILE)
    
    if chat_id not in stats or not stats[chat_id]:
        bot.reply_to(message, "Статистика пока пуста!")
        return
    
    sorted_stats = sorted(
        stats[chat_id].items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )
    
    mode = get_chat_mode(chat_id)
    mode_names = {
        'clown': '🤡 клоун',
        'pidor': '🏳️‍🌈 пидор',
        'default': '🎯 победитель'
    }
    mode_name = mode_names.get(mode, 'победитель')
    
    response = f"📊 Сегодняшний {mode_name} уже выбран!\n\nСтатистика за все время:\n"
    for i, (user_id, user_data) in enumerate(sorted_stats[:10], 1):
        username = f"@{user_data['username']}" if user_data.get('username') else user_data['name']
        response += f"{i}. {user_data['name']} ({username}) - {user_data['count']} раз(а)\n"
    
    bot.reply_to(message, response)

@bot.message_handler(commands=['clownstats', 'pidorstats'])
def stats_command(message):
    """Полная статистика"""
    chat_id = str(message.chat.id)
    stats = load_json(STATS_FILE)
    
    logger.info(f"Запрошена статистика для чата {chat_id}")
    
    if chat_id not in stats or not stats[chat_id]:
        bot.reply_to(message, "Статистика пока пуста! Используйте /clown")
        return
    
    sorted_stats = sorted(
        stats[chat_id].items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )
    
    mode = get_chat_mode(chat_id)
    mode_names = {
        'clown': '🤡 клоунов',
        'pidor': '🏳️‍🌈 пидоров',
        'default': '🎯 победителей'
    }
    mode_name = mode_names.get(mode, 'победителей')
    
    response = f"🏆 Полная статистика {mode_name}:\n\n"
    for i, (user_id, user_data) in enumerate(sorted_stats, 1):
        username = f"@{user_data['username']}" if user_data.get('username') else user_data['name']
        response += f"{i}. {user_data['name']} ({username}) - {user_data['count']} раз(а)\n"
    
    bot.reply_to(message, response)
    logger.info(f"Статистика отправлена для чата {chat_id}")

@bot.message_handler(commands=['register'])
def register_command(message):
    """Саморегистрация"""
    chat_id = str(message.chat.id)
    user = message.from_user
    
    logger.info(f"Регистрация пользователя {user.id} в чате {chat_id}")
    
    if user.is_bot:
        bot.reply_to(message, "❌ Боты не могут регистрироваться!")
        return
    
    if chat_id not in chat_members:
        chat_members[chat_id] = []
    
    # Проверяем, есть ли уже
    for member in chat_members[chat_id]:
        if member.get('id') == user.id:
            bot.reply_to(message, "❌ Вы уже зарегистрированы!")
            return
    
    new_member = {
        'id': user.id,
        'username': user.username or "",
        'name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.first_name or "Без имени",
        'active': True,
        'added_by': 'self_registration',
        'added_date': str(date.today())
    }
    
    chat_members[chat_id].append(new_member)
    save_data()
    
    bot.reply_to(message, f"✅ Вы успешно зарегистрированы!\nИмя: {new_member['name']}")
    logger.info(f"Пользователь {user.id} зарегистрирован в чате {chat_id}")

@bot.message_handler(commands=['unregister'])
def unregister_command(message):
    """Самоудаление"""
    chat_id = str(message.chat.id)
    user_id = message.from_user.id
    
    logger.info(f"Удаление регистрации пользователя {user_id} из чата {chat_id}")
    
    if chat_id not in chat_members:
        bot.reply_to(message, "❌ В этом чате нет списка участников!")
        return
    
    original_len = len(chat_members[chat_id])
    chat_members[chat_id] = [m for m in chat_members[chat_id] if m.get('id') != user_id]
    
    if len(chat_members[chat_id]) < original_len:
        save_data()
        bot.reply_to(message, "✅ Вы удалены из списка участников.")
        logger.info(f"Пользователь {user_id} удалён из чата {chat_id}")
    else:
        bot.reply_to(message, "❌ Вы не найдены в списке!")

@bot.message_handler(commands=['addmember'])
def addmember_command(message):
    """Добавление участника"""
    chat_id = str(message.chat.id)
    
    args = message.text.split()[1:]
    if not args:
        bot.reply_to(message, "Использование: /addmember @username [имя]")
        return
    
    username = args[0].replace('@', '')
    name = args[1] if len(args) > 1 else username
    
    logger.info(f"Добавление участника @{username} ({name}) в чат {chat_id}")
    
    if chat_id not in chat_members:
        chat_members[chat_id] = []
    
    for member in chat_members[chat_id]:
        if member.get('username') == username:
            bot.reply_to(message, f"❌ Участник @{username} уже в списке!")
            return
    
    new_member = {
        'username': username,
        'name': name,
        'active': True,
        'added_by': message.from_user.username or message.from_user.first_name,
        'added_date': str(date.today())
    }
    
    chat_members[chat_id].append(new_member)
    save_data()
    
    bot.reply_to(message, f"✅ Добавлен участник: {name} (@{username})")
    logger.info(f"Участник @{username} добавлен в чат {chat_id}")

@bot.message_handler(commands=['removemember'])
def removemember_command(message):
    """Удаление участника"""
    chat_id = str(message.chat.id)
    
    args = message.text.split()[1:]
    if not args:
        bot.reply_to(message, "Использование: /removemember @username")
        return
    
    username = args[0].replace('@', '')
    
    logger.info(f"Удаление участника @{username} из чата {chat_id}")
    
    if chat_id not in chat_members:
        bot.reply_to(message, "❌ Для этого чата нет списка участников!")
        return
    
    original_len = len(chat_members[chat_id])
    chat_members[chat_id] = [m for m in chat_members[chat_id] if m.get('username') != username]
    
    if len(chat_members[chat_id]) < original_len:
        save_data()
        bot.reply_to(message, f"✅ Участник @{username} удален из списка")
        logger.info(f"Участник @{username} удалён из чата {chat_id}")
    else:
        bot.reply_to(message, f"❌ Участник @{username} не найден в списке")

@bot.message_handler(commands=['listmembers'])
def listmembers_command(message):
    """Список участников"""
    chat_id = str(message.chat.id)
    
    logger.info(f"Запрошен список участников чата {chat_id}")
    
    if chat_id not in chat_members or not chat_members[chat_id]:
        bot.reply_to(message, "📭 Список участников пуст!")
        return
    
    members = chat_members[chat_id]
    active_count = len([m for m in members if m.get('active', True)])
    
    response = f"👥 Участники чата ({active_count} активных из {len(members)}):\n\n"
    
    for i, member in enumerate(members, 1):
        status = "✅" if member.get('active', True) else "❌"
        username = f"@{member['username']}" if member.get('username') else "без @"
        name = member.get('name', 'Без имени')
        response += f"{i}. {status} {name} {username}\n"
    
    bot.reply_to(message, response)

@bot.message_handler(commands=['initmembers'])
def initmembers_command(message):
    """Инициализация из администраторов"""
    chat_id = str(message.chat.id)
    
    logger.info(f"Инициализация участников из админов чата {chat_id}")
    
    try:
        admins = bot.get_chat_administrators(message.chat.id)
        
        if chat_id not in chat_members:
            chat_members[chat_id] = []
        
        added_count = 0
        for admin in admins:
            user = admin.user
            if user.is_bot:
                continue
            
            username = user.username or ""
            
            exists = any(m.get('username') == username for m in chat_members[chat_id])
            
            if not exists and username:
                new_member = {
                    'id': user.id,
                    'username': username,
                    'name': user.first_name or "Без имени",
                    'active': True,
                    'added_by': 'system',
                    'added_date': str(date.today())
                }
                chat_members[chat_id].append(new_member)
                added_count += 1
        
        save_data()
        
        if added_count > 0:
            bot.reply_to(message, f"✅ Добавлено {added_count} администраторов!")
        else:
            bot.reply_to(message, "ℹ️ Новые администраторы не найдены или уже есть в списке")
        
        logger.info(f"Добавлено {added_count} админов в чат {chat_id}")
        
    except Exception as e:
        logger.error(f"Ошибка в initmembers: {e}")
        bot.reply_to(message, "❌ Не удалось получить список администраторов. Бот должен быть админом чата!")

@bot.message_handler(commands=['setmode'])
def setmode_command(message):
    """Установка режима"""
    chat_id = str(message.chat.id)
    args = message.text.split()[1:]
    
    logger.info(f"Установка режима для чата {chat_id}: {args}")
    
    if not args:
        mode = get_chat_mode(chat_id)
        bot.reply_to(message, f"Текущий режим: {mode}\nДоступные: clown, pidor")
        return
    
    new_mode = args[0].lower()
    if new_mode not in ['clown', 'pidor']:
        bot.reply_to(message, "❌ Доступные режимы: clown, pidor")
        return
    
    group_settings[chat_id] = new_mode
    save_data()
    
    bot.reply_to(message, f"✅ Режим изменён на: {new_mode}")
    logger.info(f"Режим чата {chat_id} изменён на {new_mode}")

# ========== ЗАПУСК ==========

def cleanup():
    """Очистка при завершении"""
    logger.info("Завершение работы...")
    save_data()
    logger.info("Бот остановлен")

atexit.register(cleanup)
signal.signal(signal.SIGINT, lambda s, f: (cleanup(), sys.exit(0)))
signal.signal(signal.SIGTERM, lambda s, f: (cleanup(), sys.exit(0)))

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("ЗАПУСК БОТА (pyTelegramBotAPI)")
    logger.info("=" * 50)
    
    load_data()
    
    logger.info("=" * 50)
    logger.info("🚀 Бот запущен! Ожидание команд...")
    logger.info("=" * 50)
    
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        cleanup()