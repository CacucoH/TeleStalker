from src.classes.generic import BasicRecord

class ChannelRecord(BasicRecord):
    def __init__(
            self,
            channelId: int, 
            channelUsername: str, 
            channelTitle: str, 
            creatorName: str, 
            totalParticipants: int = -1, 
            totalMessages: int = -1,
            linkedChat: int | str | None = None
        ):
        super().__init__(
            id=channelId,
            username=channelUsername, 
            title=channelTitle, 
            creatorUsername=creatorName, 
            totalParticipants=totalParticipants, 
            totalMessages=totalMessages, 
            linkedChat=linkedChat,
            isChannel=True,
            isSupergroup=False
        )
    
    async def checkAdminPresence(self, userId: int | str) -> bool:
        return True if userId in self.members else False
