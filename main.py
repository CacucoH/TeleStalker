import os
import logging
import uvloop
import argparse

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
session_name = os.getenv('name')

client = TelegramClient('./session/' + session_name, api_id, api_hash)


def defineArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
                    prog='teleStalker',
                    description='Searches for users in channels and their subchannels recursively. Makes OSINT process much easier and saves your time',
                    epilog='')
    parser.add_argument('-c', '--channel', required=True, help="Target channel ID/Username (w/o \"@\" symbol)")
    parser.add_argument('-u', '--users', help="If you want, you may specify username, usernames or user IDs set to search for comments (space separated, w/o \"@\" symbol)", nargs="+")
    parser.add_argument('-r', '--recursion-depth', help="Specify how large our recursion tree would be. Optimal values are 2-3, to scan only channel you specified set this 1. By default value is 1")
    parser.add_argument('-e', '--exclude', help="Exlude user from scanning by their USERNAME. You may specify multiple usernames to exclude (space separated, w/o \"@\" symbol)", nargs="+")
    args = parser.parse_args()

    return args

async def main():
    args = defineArgs()
    recursionDepth = args.recursion_depth
    if recursionDepth:
        os.environ['MAX_DEPTH'] = recursionDepth

    users = []
    if args.users:
        users = set(args.users)
    
    if args.exclude:
        exclude = set(args.exclude)

    async with client:
        print(f"> Started TeleSlaker")
        allChannels = await commands.channelScanRecursion(client, args.channel, trackUsers=users, banned_usernames=exclude)
        # allChannels = await commands.channelScanRecursion(client, 'pzgynrmo', trackUsers=['Qurrik', 'McTagger'])
        visuals.visualize_channel_record(allChannels)
        visuals.visualize_subchannels_tree(allChannels)

client.loop.run_until_complete(main())