class ChannelRecord:
    def __init__(self, channelId: int, channelName: str, creatorName: str, totalParticipants: int = -1, totalMessages: int = -1):
        self.totalParticipants = totalParticipants
        self.totalMessages = totalMessages
        self.channelId = channelId
        self.channelName = channelName
        self.creatorName = creatorName
        self.usersFound = 0
        self.subchannels = {}
        self.subchannelsList = {}
        self.users = {}

    async def addUser(self, userId, user) -> bool:
        if userId not in self.users:
            self.incrementUsersCount()
            self.users[userId] = user
            return True
        return False
    
    async def addSubchannel(self, userName: str, subchannelRecord):
        self.subchannels[userName] = subchannelRecord

    def incrementUsersCount(self):
        self.usersFound += 1

    def __repr__(self):
        return f"ChannelRecord(channelName={self.channelName}, creatorName={self.creatorName}, usersFound={self.usersFound}), users={self.users})"