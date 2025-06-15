import os
import logging
import asyncio
from tqdm.asyncio import tqdm

from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.messages import GetDiscussionMessageRequest
from telethon.tl.functions.messages import GetMessagesRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import ChatFull, PeerUser, Message, User

from src.classes.channel import ChannelRecord

logger = logging.getLogger(__name__)
MAX_DEPTH = int(os.getenv('MAX_DEPTH', 5))
FLOOD_WAIT = float(os.getenv('SAFE_FLOOD_TIME', 1))  # Время ожидания между запросами, по умолчанию 0.5 секунды
MAX_PARTICIPANTS = int(os.getenv('MAX_PARTICIPANTS', 1000))  # Максимальное количество участников для обработки


async def get_channel_from_user(client: TelegramClient, username: str, current_channel_id: int) -> int | None:
    """
        Получает ID канала, связанного с пользователем.
    """
    try:
        await asyncio.sleep(0.5)  # Задержка для избежания превышения лимитов API
        user = await client.get_entity(username)
        full_user = await client(GetFullUserRequest(user))
        
        personal_channel_id = getattr(full_user.full_user, 'personal_channel_id', None)
        if personal_channel_id == current_channel_id:
            tqdm.write(f"[i] Пользователь @{username} уже связан с каналом ID: {current_channel_id}")
            return None
        
        if personal_channel_id:
            tqdm.write(f"[🎉] У пользователя @{username} прикреплён канал. ID: {personal_channel_id}")
            return personal_channel_id

    except Exception as e:
        logger.error(f"Ошибка при получении канала у пользователя @{username}: {e}")


async def get_channel_users(client: TelegramClient, channel_username: str) -> ChannelRecord | None:
    channelInstance = None
    try:
        # Получаем объект канала
        channel = await client.get_entity(channel_username)
        tqdm.write(f"--- Получаем информацию о канале {channel.title} (@{channel.username}) ---")

        # Получаем полную информацию о канале (ищем привязанный чат)
        full_channel = await client(GetFullChannelRequest(channel))
        participants = full_channel.full_chat.participants_count
        approx_total_messages = full_channel.full_chat.read_inbox_max_id

        channelInstance = ChannelRecord(
            channelId=channel.id,
            channelName=channel.title,
            creatorName=channel.username or 'Unknown',
            totalParticipants=participants,
            totalMessages=approx_total_messages
        )

        if participants > MAX_PARTICIPANTS:
            tqdm.write(f"[!] Слишком много участников в канале @{channel_username} ({participants} > {MAX_PARTICIPANTS}).")
            return
        
        linked_chat: int = full_channel.full_chat.linked_chat_id
        if not linked_chat:
            tqdm.write(f"[!] У канала @{channel_username} нет привязанного чата с комментариями.")
            return
    
        tqdm.write(f"[i] Получен ID чата с комментариями: {linked_chat}")

        message: Message
        async for message in client.iter_messages(linked_chat, wait_time=FLOOD_WAIT):
            sender: User = await message.get_sender()
            if not sender or not isinstance(message.from_id, PeerUser):
                # Пропускаем сообщения от не-пользователей (например, от ботов или каналов)
                continue

            user_id: int = sender.id
            if await channelInstance.addUser(user_id, sender):
                # Check if the user has a channel; If so add them
                subChannId = await get_channel_from_user(client, sender.username, channel.id)
                if subChannId:
                    channelInstance.subchannelsList[sender.username] = subChannId
                tqdm.write(f"[+] New user found: {sender.first_name} {sender.last_name or ''} (@{sender.username or '---'})")
        tqdm.write(f"\n[i] Users found: {channelInstance.usersFound}/{participants}\n{'-' * 64}")

    except Exception as e:
        tqdm.write(f"Ошибка при получении пользователей из комментариев канала @{channel_username}: {e}")

    finally:
        return channelInstance


async def channelScanRecursion(client: TelegramClient, channelId: str | int, currentDepth: int = 1) -> ChannelRecord:
    """
        Рекурсивно сканирует подканалы и добавляет их пользователей в основной канал.
    """
    if currentDepth > MAX_DEPTH:
        tqdm.write(f"[i] Достигнут максимальный уровень рекурсии: {currentDepth} > {MAX_DEPTH}")
        return

    channelInstance = await get_channel_users(client, channelId)
    if not channelInstance.subchannelsList:
        tqdm.write(f"[i] No subchannels for @{channelInstance.channelName} =(((")
        return
    
    for username, subchannelId in channelInstance.subchannelsList.items():
        subtree = await channelScanRecursion(client, subchannelId, currentDepth=currentDepth + 1)
        if subtree:
            await channelInstance.addSubchannel(username, subtree)
    
    return channelInstance
    