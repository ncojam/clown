# Первым делом!
import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import os
import logging
from dotenv import load_dotenv
from telegram import Bot
from telegram.request import HTTPXRequest

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

async def test():
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
    )
    
    bot = Bot(token=os.getenv('BOT_TOKEN'), request=request)
    
    print("Проверка бота...")
    me = await bot.get_me()
    print(f"✅ Бот работает: @{me.username}")
    
    print("Проверка getUpdates...")
    updates = await bot.get_updates(limit=1)
    print(f"✅ Updates получены: {len(updates)} штук")

asyncio.run(test())