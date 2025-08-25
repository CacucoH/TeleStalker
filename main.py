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

from src.common import common_api_commands 
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
    parser.add_argument('-c', '--chat', required=True, help="Specify target chat. It may be group or channel, provide ID/Invite link/Username (without \"@\" symbol)")
    parser.add_argument('-u', '--users', help="If you want, you may specify username, usernames or user IDs set to search for comments (space separated, w/o \"@\" symbol). Would not work with supergroups", nargs="+")
    parser.add_argument('-r', '--recursion-depth', help="Specify how large our recursion tree would be. Optimal values are 2-3. By default scans only given channel")
    parser.add_argument('-e', '--exclude', help="Exlude user from scanning by their USERNAME. You may specify multiple usernames to exclude (space separated, w/o \"@\" symbol). Would not work with supergroups", nargs="+")
    args = parser.parse_args()

    return args

async def main():
    # args = defineArgs()
    # recursionDepth = args.recursion_depth
    # if recursionDepth:
    #     os.environ['MAX_DEPTH'] = recursionDepth

    # users = set()
    # exclude = set()

    # users = []
    # if args.users:
    #     users = set(args.users)
    
    # if args.exclude:
    #     exclude = set(args.exclude)

    async with client:
        print(f"> Started TeleSlaker")
        # allChannels = await common_api_commands.startScanningProcess(client, args.chat, trackUsers=users, banned_usernames=exclude)
         

        if not allChannels:
            print(f"[!] No channels found or scanned")
            return

        for channel in allChannels:
            visuals.visualize_channel_record(channel)
            visuals.visualize_subchannels_tree(channel)
try:
    client.loop.run_until_complete(main())
except KeyboardInterrupt:
    print("[!] Interrupted by user")