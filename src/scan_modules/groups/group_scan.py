import os
import re
import logging
import asyncio
from tqdm.asyncio import tqdm

from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantsRequest
from telethon.tl.patched import Message
from telethon.tl.types import ChatFull, Chat

from src.classes.group import GroupRecord
from src.common.common_api_commands import MAX_PARTICIPANTS_GROUP, USER_SEARCH_LIMIT, API_MAX_USERS_REQUEST, FLOOD_WAIT


async def getChatUsers(client: TelegramClient, chatObj: Chat, trackUsers: set[str] = [],
                       banned_usernames: set[str] = [], supergroup = False) -> GroupRecord | None:
    groupInstance: GroupRecord = None
    try:
        groupInstance: GroupRecord = await getGroupInfo(client, chatObj, supergroup)
        groupId = groupInstance.groupId
        if groupInstance.totalMembers > MAX_PARTICIPANTS_GROUP:
            tqdm.write(f"[!] Too many members in @{groupInstance.groupTitle} ({groupInstance.totalMembers} > {MAX_PARTICIPANTS_GROUP}). \
You may set up max count in .env file (up to 10000)")
            return groupInstance
        
        if not groupInstance.isSupergroup:
            users, admins = await scanUsersFromGroup(client, groupId, trackUsers, banned_usernames)   
        else:
            users, admins = await scanUsersFromSupergroup(client, groupId, trackUsers, banned_usernames)

        groupInstance.admins = admins
        groupInstance.members = users
    
    except Exception as e:
        tqdm.write(f"Ошибка при получении пользователей из комментариев канала @{groupId}: {e}")
        logging.error(e)
    finally:
        return groupInstance
    

async def getGroupInfo(client: TelegramClient, chat: Chat, supergroup: bool) -> list[ChatFull, GroupRecord]:
    """
        ## Obtains information about a group or supergroup.
        Returns a `GroupRecord` instance with details about the group.
    """
    if not supergroup:
        groupInstance = GroupRecord(
            group_id=chat.id,
            group_username=getattr(chat, 'username', None), # If private there is no username
            group_title=chat.title,
            total_members=chat.participants_count,
            is_supergroup=supergroup
        )
    
    else:
        full: ChatFull = await client(GetFullChannelRequest(chat))
        groupInstance = GroupRecord(
            group_id=chat.id,
            group_username=getattr(chat, 'username', None),
            group_title=chat.title,
            creator_id=(full.full_chat.creator_user_id 
                        if hasattr(full.full_chat, 'creator_user_id') else None),
            creator_name=None,  # можно получить через get_participants(filter=ChannelParticipantsCreator)
            total_members=full.full_chat.participants_count,
            total_messages=full.full_chat.read_inbox_max_id or full.full_chat.pts,
            is_supergroup=supergroup,
            description=full.full_chat.about
        )

    return groupInstance


async def scanUsersFromSupergroup(client: TelegramClient, groupId: str | int):
    """
        ## Scans the specified supergroup for users.
        Returns a tuple of sets containing users and admins found in the group.
    """
    users = set()
    admins = set()
    async for user in client.iter_participants(groupId, limit=USER_SEARCH_LIMIT, batch_size=API_MAX_USERS_REQUEST):
        users.add(user)
        if getattr(user, "admin_rights", None):
            admins.add(user)

    tqdm.write(f"[+] Users found: {len(users)}")
    return users, admins


async def scanUsersFromGroup(client: TelegramClient, groupId: str | int, 
                             trackUsers: set[str] = [], banned_usernames: set[str] = []):
    """
        ## Scans the specified group for users.
        Returns a tuple of sets containing users and admins found in the group.
    """
    message: Message
    async for message in client.iter_messages(groupId, wait_time=FLOOD_WAIT):
        if not message.sender:
            continue
