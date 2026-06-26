import os
import logging
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")

# Файлы для данных
STATS_FILE = "clown_stats.json"
LAST_USED_FILE = "last_used.json"
MEMBERS_FILE = "chat_members.json"
PHRASES_FILE = "phrases.json"
GROUP_SETTINGS_FILE = "group_settings.json"

# Настройки polling
POLLING_TIMEOUT = 30  # long polling timeout
POLLING_INTERVAL = 5  # пауза между запросами (сек)

# Настройки логирования
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.DEBUG

def setup_logging():
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
    logging.getLogger(__name__).info("Логирование настроено")