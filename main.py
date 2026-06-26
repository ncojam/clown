import sys
import atexit
import signal
import logging
from config import setup_logging
from data_manager import load_all_data, save_all_data
from handlers import register_handlers
from bot_runner import BotRunner

setup_logging()
logger = logging.getLogger(__name__)

def cleanup(runner=None):
    logger.info("Сохранение данных...")
    save_all_data()
    if runner:
        runner.stop()
    logger.info("Бот завершил работу")

def main():
    logger.info("=" * 50)
    logger.info("CLOWN BOT")
    logger.info("=" * 50)
    
    # Загружаем данные
    logger.info("📂 Загрузка данных...")
    load_all_data()
    logger.info("✅ Данные загружены")
    
    # Создаём бота
    runner = BotRunner()
    
    # Регистрируем обработчики
    register_handlers(runner.bot)
    logger.info("✅ Обработчики зарегистрированы")
    
    # Настраиваем graceful shutdown
    def sig_handler(sig, frame):
        logger.info(f"Сигнал {sig}")
        cleanup(runner)
        sys.exit(0)
    
    atexit.register(lambda: cleanup(runner))
    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)
    
    # Запускаем
    try:
        runner.start()
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
        cleanup(runner)

if __name__ == '__main__':
    main()