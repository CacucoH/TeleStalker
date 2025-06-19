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
            channelInstance: ChannelRecord = await getUsersByComments(client, channelObj, trackUsers, banned_usernames)
        
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


async def getUsersByComments(client: TelegramClient, channelObj: Channel, targetUsers: set[str],
                             banned_usernames: set[str] = []) -> list[UserRecord]:
    channelInstance = None
    try:
        channelInstance = await getChannelInfo(client, channelObj)
        channelId = channelInstance.id
        if not channelInstance.linkedChat:  
            tqdm.write(f"[!] У канала @{channelId} нет привязанного чата с комментариями.")
            return channelInstance
        
        message: Message
        originalPostId = None
        async for message in tqdm(client.iter_messages(channelInstance.linkedChat, wait_time=FLOOD_WAIT, reverse=True), total=channelInstance.totalMessages, desc="Scanning channel messages"):
            if not message.sender:
                continue
            
            sender = message.sender # Optimized
            senderId = sender.id
            senderUsername: str = sender.username
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