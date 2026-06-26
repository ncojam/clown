import json
import os
import logging

# Папка для данных
DATA_DIR = os.environ.get('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))

def get_path(filename):
    return os.path.join(DATA_DIR, filename)

STATS_FILE = get_path("clown_stats.json")
LAST_USED_FILE = get_path("last_used.json")
MEMBERS_FILE = get_path("chat_members.json")
PHRASES_FILE = get_path("phrases.json")
GROUP_SETTINGS_FILE = get_path("group_settings.json")

logger = logging.getLogger(__name__)

last_used = {}
chat_members = {}
phrases_data = {}
group_settings = {}

def load_json_file(filepath, default=None):
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
    logger.info(f"⚠️ Файл {filepath} не найден")
    return default

def save_json_file(filepath, data):
    logger.info(f"💾 Сохранение {filepath}...")  # DEBUG → INFO
    logger.info(f"  Данных: {len(data)} записей")  # показываем что сохраняем
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Сохранён {filepath}")  # DEBUG → INFO
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения {filepath}: {e}")
        logger.error(f"  Данные: {data}")  # покажем что пытались сохранить

def load_members():
    global chat_members
    chat_members = load_json_file(MEMBERS_FILE)
    if chat_members:
        for chat_id, members in chat_members.items():
            active = len([m for m in members if m.get('active', True)])
            logger.info(f"  Чат {chat_id}: {active} активных из {len(members)}")

def save_members():
    save_json_file(MEMBERS_FILE, chat_members)

def load_stats():
    return load_json_file(STATS_FILE)

def save_stats(stats):
    save_json_file(STATS_FILE, stats)

def load_last_used():
    global last_used
    last_used = load_json_file(LAST_USED_FILE)
    return last_used

def save_last_used():
    save_json_file(LAST_USED_FILE, last_used)

def load_phrases():
    global phrases_data
    phrases_data = load_json_file(PHRASES_FILE)
    if phrases_data:
        logger.info(f"Загружены режимы фраз: {list(phrases_data.keys())}")
    return phrases_data

def load_group_settings():
    global group_settings
    group_settings = load_json_file(GROUP_SETTINGS_FILE)
    return group_settings

def save_group_settings():
    save_json_file(GROUP_SETTINGS_FILE, group_settings)

def get_members_for_chat(chat_id):
    chat_id_str = str(chat_id)
    if chat_id_str in chat_members:
        members = chat_members[chat_id_str]
        active_members = [m for m in members if m.get('active', True)]
        logger.info(f"Чат {chat_id_str}: {len(active_members)} активных")
        return active_members
    logger.warning(f"Чат {chat_id_str}: нет участников")
    return []

def get_chat_mode(chat_id):
    chat_id_str = str(chat_id)
    mode = group_settings.get(chat_id_str, 'clown')
    if mode not in phrases_data:
        mode = 'default'
    return mode

def get_phrases_for_chat(chat_id):
    mode = get_chat_mode(chat_id)
    return phrases_data.get(mode, phrases_data.get('default', {}))

def load_all_data():
    load_last_used()
    load_members()
    load_phrases()
    load_group_settings()

def save_all_data():
    save_last_used()
    save_members()
    save_group_settings()
    
def get_chat_members():
    return chat_members