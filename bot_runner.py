import logging
import time
import telebot
from telebot import apihelper
from config import BOT_TOKEN, POLLING_TIMEOUT, POLLING_INTERVAL

logger = logging.getLogger(__name__)

class BotRunner:
    """Управление ботом и polling с паузами"""
    
    def __init__(self):
        self.bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')
        self._running = False
        
        # Настройка таймаутов
        apihelper.READ_TIMEOUT = POLLING_TIMEOUT
        apihelper.CONNECT_TIMEOUT = 10
        
        logger.info("✅ Бот создан")
    
    def start(self):
        """Запуск бота с кастомным polling"""
        logger.info("=" * 50)
        logger.info("ЗАПУСК БОТА")
        logger.info(f"Long polling timeout: {POLLING_TIMEOUT}с")
        logger.info(f"Пауза между запросами: {POLLING_INTERVAL}с")
        logger.info("=" * 50)
        
        self._running = True
        
        # Получаем информацию о боте
        try:
            me = self.bot.get_me()
            logger.info(f"🤖 Бот: @{me.username} (ID: {me.id})")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения: {e}")
            return
        
        logger.info("🚀 Бот слушает команды...")
        
        # Кастомный polling с паузами
        while self._running:
            try:
                logger.debug("Запрос обновлений...")
                self.bot.polling(
                    none_stop=False,
                    timeout=POLLING_TIMEOUT,
                    long_polling_timeout=POLLING_TIMEOUT
                )
            except Exception as e:
                logger.error(f"Ошибка polling: {e}")
                logger.info(f"Пауза {POLLING_INTERVAL}с перед повтором...")
                time.sleep(POLLING_INTERVAL)
    
    def stop(self):
        """Остановка бота"""
        logger.info("Остановка бота...")
        self._running = False
        self.bot.stop_polling()
        logger.info("✅ Бот остановлен")