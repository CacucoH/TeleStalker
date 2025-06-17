class ChannelRecord:
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
        self.totalParticipants = totalParticipants
        self.channelUsername = channelUsername
        self.linkedChat = linkedChat
        self.totalMessages = totalMessages
        self.channelId = channelId
        self.channelTitle = channelTitle
        self.creatorName = creatorName
        self.usersFound = 0
        self.subchannelsList = {}
        self.subchannels = {}
        self.users = {}
        self.admins = {}

    async def addUser(self, userId: int | str, user) -> None:
        if not await self.checkUserPresence(userId):
            self.users[userId] = user
            self.usersFound += 1

    async def getUser(self, userId: int | str):
        if await self.checkUserPresence(userId):
            return self.users[userId]
    
    async def checkUserPresence(self, userId: int | str) -> bool:
        if userId in self.users:
            return True
        return False
    
    async def checkAdminPresence(self, userId: int | str) -> bool:
        return True if userId in self.users else False
    
    def addSubChannel(self, userName: str, subchannelRecord):
        self.subchannels[userName] = subchannelRecord

    def __repr__(self):
        return f"ChannelRecord(channelName={self.channelTitle}, creatorName={self.creatorName}, usersFound={self.usersFound}), users={self.users})"

    def __hash__(self):
        return hash(self.channelId)

    def __eq__(self, other):
        if isinstance(other, ChannelRecord):
            return self.channelId == other.channelId
        return False
