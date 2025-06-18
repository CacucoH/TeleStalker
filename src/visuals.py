import os
from rich.table import Table
from rich.console import Console
from rich.tree import Tree
from telethon.tl.types import User
from rich import print as rprint

from src.classes.channel import ChannelRecord
from src.classes.user import UserRecord
REPORT_DIR = "reports"


def visualize_channel_record(record: ChannelRecord):
    console = Console()
    table = Table(title=f"📊 Анализ канала: {record.channelTitle}", show_lines=True)

    table.add_column("Параметр", style="cyan", no_wrap=True)
    table.add_column("Значение", style="magenta")

    table.add_row("Channel ID", str(record.channelId))
    table.add_row("Creator", record.creatorName)
    table.add_row("Total Participants", str(record.totalParticipants))
    table.add_row("Total Messages", str(record.totalMessages))
    table.add_row("Users Found", str(record.usersFound))
    table.add_row("Admins Found", str(len(record.admins)))
    table.add_row("Subchannels", str(len(record.subchannels)))

    console.print(table)
    writeOutputToFile(data=table, filename=record.channelTitle)
    

def createSubchannelsTree(record: ChannelRecord, root: bool = True) -> Tree:
    prefix = "🌐" if root else "📎"
    
    tree = Tree(f"{prefix} [bold]{record.channelTitle}[/] ({record.channelUsername}) by [green]@{record.creatorName}[/] ({record.usersFound}/{record.totalParticipants} пользователей)")
    user: UserRecord
    for user, status in record.admins.items():
        phoneNum = '| [bold red]' + user.phone + '[/]' if user.phone else ''
        user_branch = tree.add(f"👤 {user.id} | @{user.username} | {user.full_name} {phoneNum} | {status}")
        for link, comment in user.capturedMessages.items():
            user_branch.add(f"💬 [blue]{link}[/] | {comment}")

    for user in record.users.values():
        phoneNum = '| [bold red]' + user.phone + '[/]' if user.phone else ''
        user_branch = tree.add(f"👤 {user.id} | @{user.username} | {user.full_name} {phoneNum}")
        for link, comment in user.capturedMessages.items():
            user_branch.add(f"💬 [blue]{link}[/] | {comment}")
    
    for _, subchannel in record.subchannels.items():
        tree.add(createSubchannelsTree(subchannel, root=False))
    
    return tree


def visualize_subchannels_tree(record: ChannelRecord):
    console = Console()
    tree = createSubchannelsTree(record)
    console.print(tree)
    writeOutputToFile(data=tree, filename=record.channelTitle)


def writeOutputToFile(filename: str, data) -> bool:
    filepath = os.path.join(REPORT_DIR, filename)
    with open(filepath, 'a') as targetFile:
        rprint(data, file=targetFile)

