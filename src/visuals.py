from rich.table import Table
from rich.console import Console
from rich.tree import Tree
from telethon.tl.types import User

from src.classes.channel import ChannelRecord

def visualize_channel_record(record: ChannelRecord):
    console = Console()
    table = Table(title=f"📊 Анализ канала: {record.channelName}", show_lines=True)

    table.add_column("Параметр", style="cyan", no_wrap=True)
    table.add_column("Значение", style="magenta")

    table.add_row("Channel ID", str(record.channelId))
    table.add_row("Creator", record.creatorName)
    table.add_row("Total Participants", str(record.totalParticipants))
    table.add_row("Total Messages", str(record.totalMessages))
    table.add_row("Users Found", str(record.usersFound))
    table.add_row("Subchannels", str(len(record.subchannels)))

    console.print(table)

def createSubchannelsTree(record: ChannelRecord, root: bool = True) -> Tree:
    prefix = "🌐" if root else "📎"
    
    tree = Tree(f"{prefix} [bold]{record.channelName}[/] ({record.usersFound}/{record.totalParticipants} пользователей)")
    for user_id, user_data in record.users.items():
        tree.add(f"👤 {user_id} | @{user_data.username} | {user_data.first_name} {user_data.last_name or ''} {'| [bold red]' + user_data.phone + '[/bold red]' if user_data.phone else ''}")
    
    for username, subchannel in record.subchannels.items():
        tree.add(createSubchannelsTree(subchannel, root=False))
    
    return tree

def visualize_subchannels_tree(record: ChannelRecord):
    console = Console()
    tree = createSubchannelsTree(record)
    console.print(tree)
