import logging
from tqdm.asyncio import tqdm

from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.patched import Message
from telethon.tl.types import User, ChatFull

from src.classes.channel import ChannelRecord
from src.classes.user import UserRecord
from src.common.local_commands import matchAdminsByNames
from src.common.common_api_commands import *


async def channelScanRecursion(client: TelegramClient, channelObj: Channel, currentDepth: int = 1, channelInstance: ChannelRecord | None = None,
                               creatorId: int | None = None, trackUsers: set[str] = [], banned_usernames: set[str] = []) -> ChannelRecord:
    """
        Рекурсивно сканирует подканалы и добавляет их пользователей в основной канал.
    """
    try:
        channelId = channelObj.id
        if currentDepth > MAX_DEPTH:
            tqdm.write(f"[i] Max recursion depth reached. Skipping {channelId}: {currentDepth} > {MAX_DEPTH}")
            return
        
        if not channelInstance:
            channelInstance: ChannelRecord = await getUsersFromChannelComments(client, channelObj, trackUsers, banned_usernames)
        
        if creatorId:
            channelInstance.creatorName = creatorId

        # admins: set[str] = await scanForAdmins(client, channelId)
        # channelInstance.admins = await matchAdminsByNames(channelInstance.members, admins)

        if not channelInstance or not channelInstance.subchannels:
            tqdm.write(f"[i] No subchannels for @{channelInstance.title} =(((")
            return channelInstance
        
        for username, subchannelId in channelInstance.subchannels.items():
            
            subChanObj: Channel = await client.get_entity(subchannelId)
            subtree = await channelScanRecursion(client, subChanObj, currentDepth=currentDepth + 1, creatorId=username)
            if subtree:
                channelInstance.subchannels[username] = subtree

    except KeyboardInterrupt:
        tqdm.write("[!] Прерывание пользователем")
    finally:
        return channelInstance


async def getUsersFromChannelComments(client: TelegramClient, channelObj: Channel, targetUsers: set[str],
                             banned_usernames: set[str] = []) -> list[UserRecord]:
    try:
        channelInstance = await getChannelInfo(client, channelObj)
        if not channelInstance.linkedChat:
            tqdm.write(f"[!] У канала @{channelInstance.usernamme} нет привязанного чата с комментариями.")
            return channelInstance

        channelInstance = await getUsersByComments(client, channelInstance, targetUsers=targetUsers, banned_usernames=banned_usernames,
                                                      totalMessages=channelInstance.totalMessages, participantsCount=channelInstance.totalParticipants)

    except Exception as e:
        tqdm.write(f"Ошибка при получении пользователей из комментариев канала @{channelInstance.usernamme}: {e}")
        logging.error(e)
    finally:
        return channelInstance  


async def getChannelInfo(client: TelegramClient, channelObj: Channel) -> ChannelRecord:
    # Получаем объект канала
    tqdm.write(f"--- Gathering info from {channelObj.title} (@{channelObj.username}) ---")

    # Получаем полную информацию о канале (ищем привязанный чат)
    full_channel: ChatFull = await client(GetFullChannelRequest(channelObj))
    participants = full_channel.full_chat.participants_count
    approx_total_messages = full_channel.full_chat.read_inbox_max_id
    if approx_total_messages == 0:
        approx_total_messages = full_channel.full_chat.pts
    linked_chat: int = full_channel.full_chat.linked_chat_id

    channelInstance = ChannelRecord(
        channelId=channelObj.id,
        channelUsername=channelObj.username,
        channelTitle=channelObj.title,
        creatorName=channelObj.username or 'Unknown',
        totalParticipants=participants,
        totalMessages=approx_total_messages,
        linkedChat=linked_chat
    )

    return channelInstance