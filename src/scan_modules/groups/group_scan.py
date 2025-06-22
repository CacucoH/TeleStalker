import logging
from tqdm.asyncio import tqdm

from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantsRequest
from telethon.tl.types import ChatFull, Chat, ChannelParticipantsAdmins, User

from src.classes.group import GroupRecord
from src.classes.user import UserRecord
from src.common.common_api_commands import getUsersByComments, get_channel_from_user
from src.common.common_api_commands import USER_SEARCH_LIMIT, API_MAX_USERS_REQUEST, MAX_USERS_SCAN_ITERATIONS
from src.visuals import visualize_group_record


async def getChatUsers(client: TelegramClient, chatObj: Chat, trackUsers: set[str] = [],
                       banned_usernames: set[str] = [], supergroup = False) -> GroupRecord | None:
    try:
        groupInstance: GroupRecord = await getGroupInfo(client, chatObj, supergroup)
#         if groupInstance.totalMembers > MAX_PARTICIPANTS_GROUP:
#             tqdm.write(f"[!] Too many members in @{groupInstance.title} > {MAX_PARTICIPANTS_GROUP}). \
# You may set up max count in .env file (up to 10000)")
#             return groupInstance
        
        if not groupInstance.isSupergroup:
            groupInstance = await getUsersByComments(client, groupInstance, trackUsers, banned_usernames, participantsCount=groupInstance.totalParticipants)  
        else:
            groupInstance = await scanUsersFromSupergroup(client, groupInstance)

        visualize_group_record(groupInstance)
    
    except Exception as e:
        tqdm.write(f"Ошибка при получении пользователей из комментариев группы @{groupInstance.id}: {e}")
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


async def scanUsersFromSupergroup(client: TelegramClient, groupInstance: GroupRecord):
    """
        ## Scans the specified supergroup for users.
        Returns a tuple of sets containing users and admins found in the group.
    """
    groupId = groupInstance.id
    sender: User
    async for sender in client.iter_participants(groupId, limit=USER_SEARCH_LIMIT):
        if sender.bot:
            continue
        userR = UserRecord(sender)
        userChannel = await get_channel_from_user(client, sender.username, groupId, sender)
        if userChannel:
            userR.adminInChannel.add(userChannel)
            groupInstance.addSubChannel(sender.id, userChannel)
        groupInstance.addUser(sender.id, userR)
        
    result = await client(GetParticipantsRequest(
        channel=groupId,
        filter=ChannelParticipantsAdmins(),
        offset=0,
        limit=API_MAX_USERS_REQUEST*MAX_USERS_SCAN_ITERATIONS,
        hash=0
    ))
    for sender in result.users:
        groupInstance.addAdmin(sender.id, UserRecord(sender))

    tqdm.write(f"[+] Users found: {groupInstance.totalParticipants}")
    return groupInstance