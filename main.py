import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# Initialize Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        logging.error("BOT_TOKEN is not set in .env file.")
        return

    # Initialize Bot and Dispatcher
    from aiogram.client.session.aiohttp import AiohttpSession
    session = AiohttpSession(timeout=300)
    bot = Bot(token=BOT_TOKEN, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    from aiogram.fsm.storage.memory import MemoryStorage
    dp = Dispatcher(storage=MemoryStorage())

    # Import and include routers (handlers)
    from handlers import messages, languages
    dp.include_router(messages.router)
    dp.include_router(languages.router)
    
    # We will uncomment the above once we create the handlers

    logging.info("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped!")
