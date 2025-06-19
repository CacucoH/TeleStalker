import os
import re
import logging
import asyncio
from tqdm.asyncio import tqdm

from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.messages import GetDiscussionMessageRequest
from telethon.tl.functions.messages import GetMessagesRequest
from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantsRequest
from telethon.tl.patched import Message
from telethon.tl.types import (UserFull, User, Channel,
                               ChatFull, ChannelParticipantsSearch)

from src.classes.channel import ChannelRecord
from src.classes.user import UserRecord

logger = logging.getLogger(__name__)
MAX_DEPTH = int(os.getenv('MAX_DEPTH', 5))
FLOOD_WAIT = float(os.getenv('SAFE_FLOOD_TIME', 1))  # Время ожидания между запросами, по умолчанию 0.5 секунды
MAX_PARTICIPANTS = int(os.getenv('MAX_PARTICIPANTS', 1000))  # Максимальное количество участников для обработки
USER_SEARCH_LIMIT = int(os.getenv('USER_SEARCH_LIMIT', 50))
API_MESSAGES_PER_REQUEST = int(os.getenv('API_MESSAGES_PER_REQUEST'))
ADMIN_MAX_PROBING = int(os.getenv('ADMIN_MAX_PROBING'))


async def get_channel_from_user(client: TelegramClient, username: str, current_channel_id: int) -> int | str | None:
    """
        Получает ID канала, связанного с пользователем.
    """
    try:
        user = await client.get_entity(username)
        await asyncio.sleep(0.2)  # Задержка для избежания превышения лимитов API
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
        logger.error(f"Ошибка при получении канала у пользователя @{username}: {e}")


async def getChatUsers(client: TelegramClient, channelId: str | int) -> ChannelRecord | None:
    # TODO
    try:
        channelInstance = await getChannelInfo(client, channelId)
        if channelInstance.totalParticipants > MAX_PARTICIPANTS:
            tqdm.write(f"[!] Слишком много участников в канале @{channelId} ({channelInstance.totalParticipants} > {MAX_PARTICIPANTS}).")
            return channelInstance
        
        if not channelInstance.linkedChat:
            tqdm.write(f"[!] У канала @{channelId} нет привязанного чата с комментариями.")
            return channelInstance
    
        tqdm.write(f"[i] Получен ID чата с комментариями: {channelInstance.linkedChat}")
        all_users = await scanUsersFromChat(client, channelInstance.linkedChat)

        user: User
        for user in all_users:
            pass

    except Exception as e:
        tqdm.write(f"Ошибка при получении пользователей из комментариев канала @{channelId}: {e}")

    finally:
        return channelInstance


async def getUsersByComments(client: TelegramClient, channelId: int | str, targetUsers: set[str],
                             banned_usernames: set[str] = []) -> list[UserRecord]:
    channelInstance = None
    try:
        channelInstance = await getChannelInfo(client, channelId)
        if not channelInstance.linkedChat:  
            tqdm.write(f"[!] У канала @{channelId} нет привязанного чата с комментариями.")
            return channelInstance
        
        message: Message
        originalPostId = None
        async for message in tqdm(client.iter_messages(channelInstance.linkedChat, wait_time=FLOOD_WAIT, reverse=True), total=channelInstance.totalMessages, desc="Scanning channel messages"):
            if not message.sender:
                continue
            
            senderId = message.sender.id
            senderUsername: str = message.sender.username
            # Dont waste API calls on deleted users
            if not senderUsername:
                logging.debug(f"[!] User @{senderId} is deleted? Skipping anyway...")
                continue

            # If user asked to track some channel subs
            # TODO: if user is not present comment wouldnt be saved
            # На самом деле мне слшиком похцй это делать если хотите киньте PullReq :)

            # Since in comments chat we cant acces original CHANNEL post id
            # I decided to save messages in buffer for specified user
            # When we obtain post id we will match it with comments. GeNiOuS :P
            if senderUsername in targetUsers:
                user: UserRecord = await channelInstance.getUser(senderId)
                if user:
                    msgDate = message.date.strftime('%Y-%m-%d %H:%M:%S')
                    user.capturedMessages[f"{msgDate} : https://t.me/{channelInstance.channelUsername}/{originalPostId}/?comment={message.id}"] = f"{message.text[:100]} {'...' if len(message.text) > 100 else ''}"

            if senderUsername.lower() in banned_usernames:
                logging.debug(f"[i] User @{senderUsername} and their (potential) channel is banned from scanning. Skipping...")
                continue

            # Drain messages buffer if we met post from channel and continue
            if senderId == channelInstance.channelId:
                if message.forward:
                    originalPostId = message.forward.channel_post
                continue
            
            # Check if user is already present in channel
            if await channelInstance.checkUserPresence(senderId):
                continue
            
            sender = await message.get_sender()
            if isinstance(sender, User):     # User found
                user = UserRecord(sender)
                await channelInstance.addUser(senderId, user)

                # Check if the user has a channel; If so add them
                subChannId = await get_channel_from_user(client, sender.username, channelInstance.channelId)
                if subChannId:
                    channelInstance.subchannelsList[sender.username] = subChannId
                    user.adminInChannel.add(subChannId)
            
            # elif isinstance(sender, Channel): # Admin found
            #     prefix = "[+] New admin found:"
            #     await channelInstance.addAdmin(sender.)

            # Unknown type
            else:
                continue
            
            tqdm.write(f"[+] New user found: {sender.first_name} {sender.last_name or ''} (@{sender.username or '---'})")
        tqdm.write(f"\n[i] Users found: {channelInstance.usersFound}/{channelInstance.totalParticipants}\n{'-' * 64}")

    except Exception as e:
        tqdm.write(f"Ошибка при получении пользователей из комментариев канала @{channelId}: {e}")

    finally:
        return channelInstance
    

async def getChannelInfo(client: TelegramClient, channelId: str | int) -> ChannelRecord:
    # Получаем объект канала
    channel = await client.get_entity(channelId)
    tqdm.write(f"--- Получаем информацию о канале {channel.title} (@{channel.username}) ---")

    # Получаем полную информацию о канале (ищем привязанный чат)
    full_channel: ChatFull = await client(GetFullChannelRequest(channel))
    participants = full_channel.full_chat.participants_count
    approx_total_messages = full_channel.full_chat.read_inbox_max_id
    if approx_total_messages == 0:
        approx_total_messages = full_channel.full_chat.pts
    linked_chat: int = full_channel.full_chat.linked_chat_id

    channelInstance = ChannelRecord(
        channelId=channel.id,
        channelUsername=channel.username,
        channelTitle=channel.title,
        creatorName=channel.username or 'Unknown',
        totalParticipants=participants,
        totalMessages=approx_total_messages,
        linkedChat=linked_chat
    )

    return channelInstance


async def channelScanRecursion(client: TelegramClient, channelId: str | int, currentDepth: int = 1,
                               creatorId: int | None = None, trackUsers: set[str] = [], banned_usernames: set[str] = []) -> ChannelRecord:
    """
        Рекурсивно сканирует подканалы и добавляет их пользователей в основной канал.
    """
    try:
        if currentDepth > MAX_DEPTH:
            tqdm.write(f"[i] Достигнут максимальный уровень рекурсии: {currentDepth} > {MAX_DEPTH}")
            return

        channelInstance: ChannelRecord = await getUsersByComments(client, channelId, trackUsers, banned_usernames)
        if creatorId:
            channelInstance.creatorName = creatorId

        admins: set[str] = await scanForAdmins(client, channelId)
        channelInstance.admins = await matchAdminsByNames(channelInstance.users, admins)

        if not channelInstance or not channelInstance.subchannelsList:
            tqdm.write(f"[i] No subchannels for @{channelInstance.channelTitle} =(((")
            return channelInstance
        
        for username, subchannelId in channelInstance.subchannelsList.items():
            subtree = await channelScanRecursion(client, subchannelId, currentDepth=currentDepth + 1, creatorId=username)
            if subtree:
                channelInstance.addSubChannel(username, subtree)
    except KeyboardInterrupt:
        tqdm.write("[!] Прерывание пользователем")
    finally:
        return channelInstance


async def scanUsersFromChat(client: TelegramClient, channelId: str | int) -> list[int | str]:
    all_participants = []
    async for user in client.iter_participants(channelId, limit=USER_SEARCH_LIMIT):
        all_participants.append(user)
        await asyncio.sleep(FLOOD_WAIT)

    tqdm.write(f"[+] Users found: {len(all_participants)}")
    return all_participants


async def scanForAdmins(client: TelegramClient, channelId: str | int) -> list[str]:
    # If we can retrieve name of admin - cool
    admins = set()
    message: Message
    adminFound = False
    adminFoundMessage = False
    counter = 1

    tqdm.write("[i] Probing channel for admin signatures")
    async for message in tqdm(client.iter_messages(channelId, wait_time=FLOOD_WAIT, limit=API_MESSAGES_PER_REQUEST*ADMIN_MAX_PROBING), total=API_MESSAGES_PER_REQUEST*ADMIN_MAX_PROBING, desc="Searching for admins"):
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


async def matchAdminsByNames(channelUsers: dict[int, UserRecord], potentialAdmins: list[str]) -> dict[UserRecord, str]:
    foundAdmins = {}
    for user in channelUsers.values():
        userName = user.full_name
        matchedCounter = 0
        tempArray = []
        for name in potentialAdmins:
            if name in userName:
                matchedCounter += 1
                tempArray.append(user)
        
        if matchedCounter == 1:
            foundAdmins[tempArray[0]] = '[bold red]admin[/]'
        elif matchedCounter >= 2:
            for i in tempArray:
                foundAdmins[tempArray[i]] = '[bold orange]probably admin[/]'
        elif matchedCounter > 5:
            continue
    
    return foundAdmins