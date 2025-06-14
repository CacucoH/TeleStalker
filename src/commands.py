import logging
import pyrogram as p

from pyrogram.types import Message
from pyrogram.enums import ChatType


async def getChannelUsers(app: p.Client, chat_id: int) -> None:
    logging.info(f"Entering channel {chat_id}")
    comm_info = await app.get_chat(chat_id) # Find chat with comments
    
    if not comm_info.linked_chat:
        print(f"[!] Comments are seem to be disablesd in {chat_id}")
        return
    
    comments_chat = comm_info.linked_chat.id
    
    users = {}
    message: Message
    async for message in app.get_chat_history(chat_id=comments_chat):
        if not message.from_user:
            continue

        userId = message.from_user.id
        if userId not in users:
            print(f"[+] Found new user in channel {chat_id}: {userId} {message.from_user.first_name} {message.from_user.last_name}")
            users[userId] = message.from_user

    print()
    


async def getChannelFromUser(app: p.Client, chat_id: int) -> None:
    pass