from src.classes.user import UserRecord
from src.classes.channel import ChannelRecord

class GroupRecord:
    def __init__(
        self,
        group_id: int,
        group_username: str | None,
        group_title: str,
        creator_id: int | None,
        creator_name: str | None,
        total_members: int = -1,
        total_messages: int = -1,
        is_supergroup: bool = False,
        description: str | None = None,
    ):
        self.groupId = group_id
        self.groupUsername = group_username
        self.groupTitle = group_title
        self.creatorId = creator_id
        self.creatorUsername = creator_name
        
        self.totalMembers = total_members
        self.totalMessages = total_messages
        
        self.isSupergroup = is_supergroup        
        self.description = description
        
        self.members_found: int = 0
        self.members: dict[int | str, UserRecord] = {}
        self.admins: dict[int | str, UserRecord] = {}
        self.subchannels: set[ChannelRecord] = set()
    
    async def add_member(self, user_id: int | str, user_obj) -> None:
        if user_id not in self.members:
            self.members[user_id] = user_obj
            self.members_found += 1
    
    def add_admin(self, user_id: int | str, participant_obj) -> None:
        self.admins[user_id] = participant_obj
    
    def __repr__(self):
        return (f"GroupRecord(title={self.group_title!r}, members={self.members_found}, "
                f"admins={len(self.admins)}), subchannels={len(self.subchannels)})")
    
    def __hash__(self):
        return hash(self.groupId)
    
    def __eq__(self, other):
        return isinstance(other, GroupRecord) and self.groupId == other.groupId
