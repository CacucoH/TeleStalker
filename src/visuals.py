import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.text import Text
from rich import box
from telethon.tl.types import User
from rich import print as rprint

from src.classes.channel import ChannelRecord
from src.classes.group import GroupRecord
from src.classes.user import UserRecord
REPORT_DIR = "reports"


def visualize_channel_record(record: ChannelRecord):
    console = Console()
    table = Table(title=f"📊 Анализ канала: {record.title}", show_lines=True)

    table.add_column("Параметр", style="cyan", no_wrap=True)
    table.add_column("Значение", style="magenta")

    table.add_row("Channel ID", str(record.id))
    table.add_row("Creator", record.creatorName)
    table.add_row("Total Participants", '~' + str(record.totalParticipants))
    table.add_row("Total Messages", '~' + str(record.totalMessages))
    # table.add_row("members Found", str(record.membersFound))
    table.add_row("Admins Found", str(len(record.admins)))
    table.add_row("Subchannels", str(len(record.subchannels)))

    console.print(table)
    writeOutputToFile(data=table, filename=f"channel-{record.title}")


def createSubchannelsTree(record: ChannelRecord, root: bool = True) -> Tree:
    if not isinstance(record, ChannelRecord):
        return
    
    prefix = "🌐" if root else "📎"
    tree = Tree(f"{prefix} [bold]{record.title}[/] ({record.usernamme}) by [green]@{record.creatorName}[/] ({record.membersFound}/{record.totalParticipants} пользователей)")

    tree = output_user_info(tree, record.members.values(), record.id)
    
    for _, subchannel in record.subchannels.items():
        subtree = createSubchannelsTree(subchannel, root=False)
        if subtree:
            tree.add(subtree)
    
    return tree


def visualize_group_record(group: GroupRecord):
    console = Console()

    title_text = Text(group.title, style="bold cyan")
    if group.usernamme:
        title_text.append(f" (@{group.usernamme})", style="dim")

    group_table = Table.grid(padding=(0, 1))
    group_table.add_column(justify="right", style="bold")
    group_table.add_column()

    group_table.add_row("ID:", str(group.id))
    group_table.add_row("Creator:", group.creatorName or "N/A")
    group_table.add_row("Total Members:", str(group.totalParticipants if group.totalParticipants != -1 else group.membersFound))
    group_table.add_row("Admins Found:", str(len(group.admins)))
    group_table.add_row("Messages:", str(group.totalMessages if group.totalMessages != -1 else "N/A"))
    group_table.add_row("Supergroup:", "✅" if group.isSupergroup else "❌")

    if group.description:
        group_table.add_row("Description:", group.description.strip())

    bTable = Panel(group_table, title=title_text, expand=False, border_style="green", box=box.ROUNDED)
    console.print(bTable)

    tree = Tree(f"👥 Users")
    tree = output_user_info(tree, group.members.values(), group.id)

    console.print(tree)

    groupType = "group"
    if group.isSupergroup:
        groupType = "supergroup"

    writeOutputToFile(f"{groupType}-{group.title}", bTable)
    writeOutputToFile(f"{groupType}-{group.title}", tree)


def visualize_subchannels_tree(record: ChannelRecord):
    console = Console()
    tree = createSubchannelsTree(record)
    console.print(tree)
    writeOutputToFile(data=tree, filename=f"channel-{record.title}")


def writeOutputToFile(filename: str, data) -> bool:
    filepath = os.path.join(REPORT_DIR, filename)
    with open(filepath, 'a') as targetFile:
        rprint(data, file=targetFile)


def output_user_info(tree: Tree, users: set[UserRecord], currentChatId: int) -> Tree:
    user: UserRecord
    for user in users:
        phoneNum = ' | [bold red]' + user.phone + '[/]' if user.phone else ''
        admin = ' | [bold red]admin[/]' if currentChatId in user.adminInChannel else ''
        hasChannel = ''
        if not admin:
            hasChannel = f' | [green]adm in {len(user.adminInChannel)} chat(s)[/]' if user.adminInChannel else ''
        user_branch = tree.add(f"👤 {user.id} | @{user.username} | {user.full_name}{admin}{phoneNum}{hasChannel}")
        for link, comment in user.capturedMessages.items():
            user_branch.add(f"💬 [blue]{link}[/] | {comment}")
    return tree