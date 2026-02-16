from src.classes.generic import BasicRecord


class GroupRecord(BasicRecord):
    def __init__(
        self,
        group_id: int,
        group_title: str,
        group_username: str | None = None,
        creator_id: int | None = None,
        creator_name: str | None = None,
        total_members: int = -1,
        total_messages: int = -1,
        is_supergroup: bool = False,
        description: str | None = None,
    ):
        super().__init__(
            id=group_id,
            username=group_username,
            title=group_title,
            creatorUsername=creator_name,
            totalParticipants=total_members,
            totalMessages=total_messages,
            linkedChat=None,  # Groups do not have linked chats like channels
            isChannel=False,
            isSupergroup=is_supergroup,
        )

        self.description = description

    @DeprecationWarning
    async def add_member(self, user_id: int | str, user_obj) -> None:
        if user_id not in self.members:
            self.members[user_id] = user_obj
            self.members_found += 1

    @DeprecationWarning
    def add_admin(self, user_id: int | str, participant_obj) -> None:
        self.admins[user_id] = participant_obj
