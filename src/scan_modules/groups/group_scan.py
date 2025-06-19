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
from telethon.tl.types import ChatFull, ChannelParticipantsSearch

from src.classes.group import GroupRecord
from src.classes.user import UserRecord
from src.common.local_commands import matchAdminsByNames
from src.common.common_api_commands import *


async def getChatUsers(client: TelegramClient, chatObj: Chat, trackUsers: set[str] = [],
                       banned_usernames: set[str] = [], supergroup = False) -> GroupRecord | None:
    groupInstance: GroupRecord = None
    try:
        groupInstance: GroupRecord = await getGroupInfo(client, chatObj)
        groupId = groupInstance.groupId
        if groupInstance.totalMembers > MAX_PARTICIPANTS_GROUP:
            tqdm.write(f"[!] Too many members in @{groupInstance.groupTitle} ({groupInstance.totalMembers} > {MAX_PARTICIPANTS_GROUP}). \
You may set up max count in .env file (up to 10000)")
            return groupInstance
        
        if not groupInstance.isSupergroup:
            users, admins = await scanUsersFromGroup(client, groupId)
        else:
            users, admins = await scanUsersFromSupergroup(client, groupId)

        groupInstance.admins = admins
        groupInstance.members = users
    
    except Exception as e:
        tqdm.write(f"Ошибка при получении пользователей из комментариев канала @{groupId}: {e}")
        logging.error(e)
    finally:
        return groupInstance
    

async def getGroupInfo(client: TelegramClient, chat: Chat) -> list[ChatFull, GroupRecord]:
    """
        ## Obtains information about a group or supergroup.
        Returns a `GroupRecord` instance with details about the group.
    """
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
        is_supergroup=getattr(chat, 'megagroup', False),
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


async def scanUsersFromGroup(client: TelegramClient, groupId: str | int):
    """
        ## Scans the specified group for users.
        Returns a tuple of sets containing users and admins found in the group.
    """
    users = set()
    admins = set()

    offset = 0
    limit = 100
    while True:
        part = await client(GetParticipantsRequest(
            groupId, ChannelParticipantsSearch(''), offset, limit, hash=0
        ))
        if not part.users:
            break
        for user in part.users:
            users.add(user.id, user)
            if user.admin_rights:
                admins.add(user.id, user)
        offset += len(part.users)
