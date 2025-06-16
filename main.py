import os
import logging
import uvloop
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.sessions import StringSession

# Загрузка переменных окружения
load_dotenv('./config/.env')

from src import commands 
from src import visuals

# Настройка логов
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] - %(asctime)s - %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
    filename=f"./logs/log.log",
    filemode="w"
)

# Оптимизация asyncio
uvloop.install()

api_id = int(os.getenv('api_id'))
api_hash = os.getenv('api_hash')
session_name = os.getenv('name')  # имя файла сессии

client = TelegramClient('./session/' + session_name, api_id, api_hash)

async def main():
    channelId = input("[i] Input target channel id/username\n> ")
    async with client:
        # Получение информации о пользователе
        # await commands.get_channel_from_user(client, 'dmfrpro', 11)
        allChannels = await commands.channelScanRecursion(client, channelId)
        visuals.visualize_channel_record(allChannels)
        visuals.visualize_subchannels_tree(allChannels)

client.loop.run_until_complete(main())
