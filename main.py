import os
import uvloop
import pyrogram as p
import logging
from dotenv import load_dotenv

from telethon.sync import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import InputUser



from src import commands, router


logger = logging.getLogger('pyrogram').setLevel(logging.ERROR)
logging.basicConfig(
        level=logging.DEBUG, 
        format="[%(levelname)s] - %(asctime)s - %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
        filename=f"./logs/log.log",
        filemode="a"
    )

uvloop.install()
load_dotenv('./config/.env')

app = p.Client(
    name=os.getenv('name'),
    api_id=os.getenv('api_id'),
    api_hash=os.getenv('api_hash'),
    workdir=r"./session"
)

async def main():
    async with app:
        # await commands.getChannelUsers(app, chat_id='innochapay')
        print(await app.get_users('asya_vespa'))

app.run(main())