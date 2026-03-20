import logging

from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import ChatFull
from tqdm.asyncio import tqdm

from classes.channel import ChannelRecord
from classes.user import UserRecord
from common.common_api_commands import (
    MAX_PARTICIPANTS_CHANNEL,
    Channel,
    getUsersByComments,
    scanForAdmins,
)
from common.local_commands import matchAdminsByNames


async def channelScanRecursion(
    client: TelegramClient,
    channelObj: Channel,
    max_depth: int,
    trackUsers: set[str],
    banned_usernames: set[str],
    currentDepth: int = 1,
    channelInstance: ChannelRecord | None = None,
    creatorId: int | None = None,
    isBlocked: bool = False,
) -> list[ChannelRecord, bool]:
    """
    ## Recursively scans a Telegram channel and its subchannels, gathering information about each channel and its members
    ### Returns:
    - A Channel instance (ChannelRecord)
    - Are you blocked by telegram API (bool)
    """
    channelInstance: ChannelRecord = None
    try:
        channelId = channelObj.id
        if currentDepth > max_depth:
            message = f"[i] Max recursion depth reached. Skipping {channelId}: {currentDepth} > {max_depth}"
            tqdm.write(message)
            logging.info(message)
            return None, False

        if not channelInstance:
            channelInstance: ChannelRecord = await getUsersFromChannelComments(
                client=client,
                channelObj=channelObj,
                targetUsers=trackUsers,
                banned_usernames=banned_usernames,
                max_depth=max_depth,
            )

        if channelInstance.totalParticipants > MAX_PARTICIPANTS_CHANNEL:
            message = f"[i] Skipping {channelInstance.title} ({channelInstance.usernamme}). Participants exceed maximum value {channelInstance.totalParticipants} > {max_depth}"
            tqdm.write(message)
            logging.info(message)
            return channelInstance, False

        if creatorId:
            channelInstance.creatorName = creatorId

        admins: set[str] = await scanForAdmins(client, channelId)
        channelInstance.admins = await matchAdminsByNames(
            channelInstance.members, admins
        )

        # На первой итерации необходимо указать админов канала (если найдены)
        if currentDepth == 1:
            for ID in channelInstance.admins:
                user = channelInstance.members.get(ID)
                user.adminInChannel.add(channelId)

        if not channelInstance or not channelInstance.subchannels:
            tqdm.write(f"[i] No subchannels for @{channelInstance.usernamme} =(((")
            return channelInstance, False

        for username, subchannelId in channelInstance.subchannels.items():
            subChanObj: Channel = await client.get_entity(subchannelId)
            subtree, isBlocked = await channelScanRecursion(
                client,
                subChanObj,
                currentDepth=currentDepth + 1,
                creatorId=username,
                trackUsers=trackUsers,
                banned_usernames=banned_usernames,
                max_depth=max_depth,
            )
            if subtree:
                channelInstance.subchannels[username] = subtree

            # Break cycle to prevent account ban
            if isBlocked:
                break

    except KeyboardInterrupt:
        tqdm.write("[!] Caught CTRL+C")
    except Exception as e:
        tqdm.write(f"[!] API requests exhausted or something else happened: {e}")
        return channelInstance, True
    return channelInstance, isBlocked


async def getUsersFromChannelComments(
    client: TelegramClient,
    channelObj: Channel,
    targetUsers: set[str],
    max_depth: int,
    banned_usernames: set[str] = None,
) -> list[UserRecord]:
    try:
        channelInstance = await getChannelInfo(client, channelObj)
        if not channelInstance.linkedChat:
            tqdm.write(
                f"[!] У канала @{channelInstance.usernamme} нет привязанного чата с комментариями."
            )
            return channelInstance

        channelInstance = await getUsersByComments(
            client,
            channelInstance,
            targetUsers=targetUsers,
            banned_usernames=banned_usernames,
            totalMessages=channelInstance.totalMessages,
            participantsCount=channelInstance.totalParticipants,
            max_depth=max_depth,
        )

    except Exception as e:
        tqdm.write(
            f"Ошибка при получении пользователей из комментариев канала @{channelInstance.usernamme}: {e}"
        )
        logging.error(e)

    return channelInstance


async def getChannelInfo(client: TelegramClient, channelObj: Channel) -> ChannelRecord:
    # Получаем объект канала
    tqdm.write(
        f"--- Gathering info from {channelObj.title} (@{channelObj.username}) ---"
    )

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
        creatorName=channelObj.username or "Unknown",
        totalParticipants=participants,
        totalMessages=approx_total_messages,
        linkedChat=linked_chat,
    )

    return channelInstance
