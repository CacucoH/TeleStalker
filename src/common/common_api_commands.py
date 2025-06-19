"""
    ## Contains common API commands for Telegram client operations.
    These commands are used across different modules to interact with Telegram API.
"""
import os
import re
import asyncio
import logging
from tqdm.asyncio import tqdm

from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.patched import Message
from telethon.tl.types import UserFull, Channel, Chat

from src.classes.channel import ChannelRecord
from src.classes.group import GroupRecord
from src.scan_modules.channels.channel_scan import channelScanRecursion
from src.scan_modules.groups.group_scan import getChatUsers

logger = logging.getLogger(__name__)
MAX_DEPTH = int(os.getenv('MAX_DEPTH', 5))
FLOOD_WAIT = float(os.getenv('SAFE_FLOOD_TIME', 1))  # Время ожидания между запросами, по умолчанию 0.5 секунды
USER_SEARCH_LIMIT = int(os.getenv('USER_SEARCH_LIMIT', 50))
API_MESSAGES_PER_REQUEST = int(os.getenv('API_MESSAGES_PER_REQUEST'))
ADMIN_MAX_PROBING = int(os.getenv('ADMIN_MAX_PROBING'))
MAX_PARTICIPANTS_GROUP = int(os.getenv('MAX_PARTICIPANTS_GROUP', 666))  # Максимальное количество участников в группе для обработки
MAX_PARTICIPANTS_CHANNEL = int(os.getenv('MAX_PARTICIPANTS_CHANNEL', 1000))  # Максимальное количество участников для обработки
API_MAX_USERS_REQUEST = int(os.getenv('API_MAX_USERS_REQUEST', 200))  # Максимальное количество пользователей, получаемых за один запрос


async def startScanningProcess(client: TelegramClient, chatlId: str | int, trackUsers: set[str] = set(),
                               banned_usernames: set[str] = set()) -> list[ChannelRecord] | None:
    totalChannels: list[ChannelRecord] = []
    chatObj = await client.get_entity(chatlId)
    if not chatObj:
        tqdm.write(f"[!] Bruhhh cannot obtain any info about @{chatlId}. Double check ID or username")
        return

    if isinstance(chatObj, Channel):
        tqdm.write(f"[i] Scanning channel @{chatObj.title} ({chatObj.id})")
        totalChannels.append(await channelScanRecursion(client, chatObj, trackUsers, banned_usernames))
    
    # If chat is presented:
    # Scan chat for channels -> recursively scan all found channels
    elif isinstance(chatObj, Chat) or (isinstance(chatObj, Channel) and chatObj.megagroup):
        tqdm.write(f"[i] Scanning chat {chatObj.title} ({chatObj.id})")
        isSupergroup = isinstance(chatObj, Channel) and chatObj.megagroup
        groupInstance: GroupRecord = await getChatUsers(client, chatObj.id, trackUsers=trackUsers,
                                                        banned_usernames=banned_usernames, supergroup=isSupergroup)
        
        for subchannel in groupInstance.subchannels:
            channelInstance: ChannelRecord = await channelScanRecursion(client, subchannel.channelId, channelInstance=subchannel,
                                                         trackUsers=trackUsers, banned_usernames=banned_usernames)
            totalChannels.append(channelInstance)

    return totalChannels


async def get_channel_from_user(client: TelegramClient, username: str, current_channel_id: int) -> int | str | None:
    """
        ## Obtains a channel ID from a user's profile or bio
        Returns the channel ID if found, otherwise None
    """
    try:
        user = await client.get_entity(username)
        await asyncio.sleep(0.2)  # Задержка для избежания превышения частоты запросов API
        full_user: UserFull = await client(GetFullUserRequest(user))
        
        personal_channel_id = getattr(full_user.full_user, 'personal_channel_id', None)
        bio = getattr(full_user.full_user, 'about')

        if personal_channel_id == current_channel_id:
            tqdm.write(f"[i] Пользователь @{username} уже связан с каналом ID: {current_channel_id}")
            return None
        
        # Search in profile
        if personal_channel_id:
            tqdm.write(f"[🎉] У пользователя @{username} прикреплён канал. ID: {personal_channel_id}")
            return personal_channel_id
        # Search in bio
        elif bio:
            channel_in_bio = re.match(r'(https:\/\/)?t\.me\/[a-z0-9]+', bio)
            if channel_in_bio:
                tqdm.write(f"[🎉] У пользователя @{username} канал в коментах. ID: {channel_in_bio.group(0)}")
                return channel_in_bio.group(0)
    except Exception as e:
        tqdm.write(f"[!] Error while trying to get channel from user @{username}: {e}")
        logger.error(f"Error while trying to get channel from user @{username}: {e}")


async def scanForAdmins(client: TelegramClient, channelId: str | int) -> list[str]:
    """
        ## Scans the specified channel for admin signatures in messages
        Returns a list of admin usernames found in the channel
    """
    admins = set()
    message: Message
    adminFound = False
    adminFoundMessage = False
    counter = 1

    maxMessages = API_MESSAGES_PER_REQUEST*ADMIN_MAX_PROBING
    tqdm.write("[i] Probing channel for admin signatures")
    async for message in tqdm(client.iter_messages(channelId, wait_time=FLOOD_WAIT, limit=maxMessages), total=maxMessages, desc="Searching for admins"):
        adminName = message.post_author
        if adminName:
            admins.add(adminName)
            adminFound = True

        if not adminFoundMessage and counter > API_MESSAGES_PER_REQUEST:
            if not adminFound:
                tqdm.write("[-] Seems like admin signatures disabled in this channel")
                break
            adminFoundMessage = True
            tqdm.write("[i] Admin signatures found, continuing probing!!!")
        
        counter += 1

    if admins:
        tqdm.write(f"[+] Found {len(admins)} admins for this chat")
    return admins