"""
## Contains common API commands for Telegram client operations.
These commands are used across different modules to interact with Telegram API.
"""

import asyncio
import logging
import os
import re

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.patched import Message
from telethon.tl.types import Channel, ChannelForbidden, Chat, User, UserFull
from tqdm.asyncio import tqdm

from classes.channel import ChannelRecord
from classes.group import GroupRecord
from classes.user import UserRecord

# Загрузка переменных окружения
load_dotenv("./config/.env")

logger = logging.getLogger(__name__)
# MAX_DEPTH = int(os.getenv("MAX_DEPTH", 5))
FLOOD_WAIT = float(
    os.getenv("SAFE_FLOOD_TIME", 1)
)  # Время ожидания между запросами, по умолчанию 0.5 секунды
USER_SEARCH_LIMIT = int(os.getenv("USER_SEARCH_LIMIT", 50))
API_MESSAGES_PER_REQUEST = int(os.getenv("API_MESSAGES_PER_REQUEST"))
ADMIN_MAX_PROBING = int(os.getenv("ADMIN_MAX_PROBING"))
MAX_PARTICIPANTS_GROUP = int(
    os.getenv("MAX_PARTICIPANTS_GROUP", 666)
)  # Максимальное количество участников в группе для обработки
MAX_PARTICIPANTS_CHANNEL = int(
    os.getenv("MAX_PARTICIPANTS_CHANNEL", 1000)
)  # Максимальное количество участников для обработки
API_MAX_USERS_REQUEST = int(
    os.getenv("API_MAX_USERS_REQUEST", 200)
)  # Максимальное количество пользователей, получаемых за один запрос
MAX_USERS_SCAN_ITERATIONS = int(os.getenv("MAX_USERS_SCAN_ITERATIONS", 5))


async def startScanningProcess(
    client: TelegramClient,
    chatId: str | int,
    recursionDepth: int,
    trackUsers: set[str] = None,
    banned_usernames: set[str] = None,
) -> list[ChannelRecord]:
    from scan_modules.channels.channel_scan import channelScanRecursion
    from scan_modules.groups.group_scan import getChatUsers

    if not recursionDepth:
        recursionDepth = 1

    totalChannels: list[ChannelRecord] = []

    if not trackUsers:
        trackUsers = set()

    if not banned_usernames:
        banned_usernames = set()

    # We've got link
    try:
        chatObj = await client.get_entity(chatId)
    except Exception as e:
        logging.error(e)
        tqdm.write(
            f"Cannot get {chatId} entity. Ensure you're provide existing ID and you have joined this chat if it's private"
        )
        return

    if not chatObj:
        tqdm.write(
            f"[!] Bruhhh cannot obtain any info about @{chatId}. Double check ID or username"
        )
        return

    if isinstance(chatObj, Channel) and not chatObj.megagroup:
        tqdm.write(f"[i] Scanning channel @{chatObj.username} ({chatObj.id})")
        channelInstance, _ = await channelScanRecursion(
            client,
            chatObj,
            trackUsers=trackUsers,
            banned_usernames=banned_usernames,
            max_depth=recursionDepth,
        )

        if channelInstance:
            totalChannels.append(channelInstance)

    # If chat is present:
    # Scan chat for channels -> recursively scan all found channels
    elif isinstance(chatObj, Chat) or (isinstance(chatObj, Channel)):
        tqdm.write(f"[i] Scanning chat {chatObj.title} ({chatObj.id})")
        isSupergroup = isinstance(chatObj, Channel) and chatObj.megagroup
        groupInstance: GroupRecord = await getChatUsers(
            client,
            chatObj,
            trackUsers=trackUsers,
            banned_usernames=banned_usernames,
            supergroup=isSupergroup,
            max_depth=recursionDepth,
        )
        for subchannelId in groupInstance.subchannels.values():
            channelObj = await client.get_entity(subchannelId)
            channelInstance, isBlocked = await channelScanRecursion(
                client,
                channelObj,
                trackUsers=trackUsers,
                banned_usernames=banned_usernames,
                max_depth=recursionDepth,
            )

            if channelInstance:
                totalChannels.append(channelInstance)

            if isBlocked:
                break

    return totalChannels


async def get_channel_from_user(
    client: TelegramClient,
    username: str,
    current_channel_id: int,
    user: User | None = None,
) -> int | str | None:
    """
    ## Obtains a channel ID from a user's profile or bio
    Returns the channel ID if found, otherwise None
    """
    try:
        if not user:
            user = await client.get_entity(username)

        await asyncio.sleep(
            0.05
        )  # Задержка для избежания превышения частоты запросов API
        full_user: UserFull = await client(GetFullUserRequest(user))

        personal_channel_id = getattr(full_user.full_user, "personal_channel_id", None)
        bio = full_user.full_user.about

        if personal_channel_id == current_channel_id:
            tqdm.write(
                f"[i] Пользователь @{username} уже связан с каналом ID: {current_channel_id}"
            )
            return None

        # Search in profile
        if personal_channel_id:
            tqdm.write(
                f"[🎉] У пользователя @{username} прикреплён канал. ID: {personal_channel_id}"
            )
            return personal_channel_id
        # Search in bio
        elif bio:
            channel_in_bio = re.match(r"(https:\/\/)?t\.me\/[a-z0-9]+", bio)
            if channel_in_bio:
                tqdm.write(
                    f"[🎉] У пользователя @{username} канал в коментах. ID: {channel_in_bio.group(0)}"
                )
                return channel_in_bio.group(0)
    except Exception as e:
        tqdm.write(f"[!] Error while trying to get channel from user @{username}: {e}")
        logger.error(f"Error while trying to get channel from user @{username}: {e}")


async def scanForAdmins(client: TelegramClient, channelId: str | int) -> set[str]:
    """
    ## Scans the specified channel for admin signatures in messages
    Returns a list of admin usernames found in the channel
    """
    admins = set()
    message: Message
    adminFound = False
    adminFoundMessage = False
    counter = 1

    maxMessages = API_MESSAGES_PER_REQUEST * ADMIN_MAX_PROBING
    tqdm.write("[i] Probing channel for admin signatures")
    async for message in tqdm(
        client.iter_messages(channelId, wait_time=FLOOD_WAIT, limit=maxMessages),
        total=maxMessages,
        desc="Searching for admins",
    ):
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


async def getUsersByComments(
    client: TelegramClient,
    chatRecord: GroupRecord | ChannelRecord,
    targetUsers: set[str],
    max_depth: int,
    banned_usernames: set[str],
    totalMessages: int = 0,
    participantsCount: int = 0,
) -> list[dict[UserRecord], dict[int, int]]:
    """
    ### Generic method to get users from comments in a channel or chat
    Returns dict of `UserRecord` instances and a dict of subchannels found.
    """
    try:
        message: Message
        # originalPostId = None
        thisChatId = chatRecord.id
        chatToScan = (
            chatRecord.linkedChat
            if isinstance(chatRecord, ChannelRecord)
            else thisChatId
        )

        async for message in tqdm(
            client.iter_messages(chatToScan, wait_time=FLOOD_WAIT, reverse=True),
            total=totalMessages
            * 5,  # Because msg count is inaccurate and actual count x5 times bigger in avg
            desc="Scanning channel messages",
        ):
            if not message.sender:
                continue

            res = await search(
                message=message,
                client=client,
                thisChatId=thisChatId,
                chatRecord=chatRecord,
                banned_usernames=banned_usernames,
                targetUsers=targetUsers,
            )
            if not res:
                continue

            user, senderUsername = res[0], res[1]
            tqdm.write(
                f"[+] New user found: {user.full_name if user.full_name else 'Unknown'} (@{senderUsername or str(user.id)})"
            )

        tqdm.write(
            f"\n[i] Users found: {chatRecord.membersFound}/{participantsCount}\n{'-' * 64}"
        )

    except Exception as e:
        tqdm.write(f"Ошибка при получении пользователей из комментариев: {e}")
        logging.error(e)

    return chatRecord


async def search(
    message: Message,
    client,
    thisChatId: int,
    chatRecord: GroupRecord | ChannelRecord,
    banned_usernames: set[str],
    targetUsers: set[str],
    originalPostId: int = None,
):
    sender = message.sender  # Optimized
    if sender is None:
        return None

    senderId: int = sender.id
    try:
        senderUsername: str = sender.username
    except Exception:
        if not senderUsername:
            # Skip to avoid error
            if isinstance(sender, ChannelForbidden):
                logging.warning(f"[!] Skipping... megagroup? {senderId} {sender.title}")
                return None

            # Dont waste API calls on deleted users
            logging.debug(f"[!] User @{senderId} is deleted? Skipping anyway...")
            senderUsername = str(senderId)

            return None

    if senderUsername in banned_usernames or str(senderId) in banned_usernames:
        logging.debug(
            f"[i] User @{senderUsername} and their (potential) channel is banned from scanning. Skipping..."
        )
        return None

    # If user asked to track some channel subs
    # TODO: if user is not present comment wouldnt be saved
    # На самом деле мне слшиком похцй это делать если хотите киньте PullReq :)
    if senderUsername in targetUsers or str(senderId) in targetUsers:
        user: UserRecord = chatRecord.getUser(senderId)
        if not user:
            user = UserRecord(sender)
            chatRecord.addUser(senderId, user)

        msgDate = message.date.strftime("%Y-%m-%d %H:%M:%S")
        text = message.text or "<Non-text object>"
        link = await makeLink(message.id, chatRecord, originalPostId)
        user.capturedMessages[f"{msgDate} : {link}"] = (
            f"{text[:100]} {'...' if len(text) > 100 else ''}"
        )

        return None

    # Drain messages buffer if we met post from channel and continue
    if senderId == thisChatId:
        if message.forward:
            originalPostId = message.forward.channel_post
        return None

    # Check if user is already present in channel or we deal not with user
    if chatRecord.getUser(senderId) or not isinstance(sender, User):
        return None

    user = UserRecord(sender)
    if senderUsername:
        # Check if the user has a channel; If so add them
        subChannId = await get_channel_from_user(client, senderUsername, thisChatId)
        if subChannId:
            chatRecord.addSubChannel(senderUsername, subChannId)
            user.adminInChannel.add(subChannId)

    chatRecord.addUser(senderId, user)
    # elif isinstance(sender, Channel): # Admin found
    #     prefix = "[+] New admin found:"
    #     await channelInstance.addAdmin(sender.)

    return user, senderUsername


async def makeLink(
    messageId: int, chat: ChannelRecord | GroupRecord, originalPostId: int | None = None
) -> str:
    """
    ## Generates a link to the public/private channel/group/supergroup.
    Returns a string with the link
    """
    if chat.isChannel:
        if not chat.isSupergroup:
            return (
                f"https://t.me/{chat.usernamme}/{originalPostId}/?comment={messageId}"
            )

    username = chat.usernamme
    if not username:
        return f"https://t.me/c/{chat.id}/{messageId}"
    return f"https://t.me/{username}/{messageId}"
