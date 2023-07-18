import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from sqlalchemy import create_engine
from config import bot_token, db_url

bot = Bot(token=bot_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
engine = create_engine(db_url)

async def setup_commands():
    await bot.set_my_commands([
        types.BotCommand(command='edit_profile', description='✏️ Редактировать профиль'),
        types.BotCommand(command='change_location', description='🌍 Сменить локацию'),
        types.BotCommand(command='view_ads', description='📄 Просмотреть объявления'),
        types.BotCommand(command='my_ads', description='📄 Мои объявления'),
    ])
if __name__ == '__main__':
    from handlers import *

    full_timep_default(
        # default labels
        label_up='⇪', label_down='⇓',
        hour_format='{0:02}h', minute_format='{0:02}m', second_format='{0:02}s'
    )
    executor.start_polling(dp)
