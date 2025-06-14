class Channel:
    def __init__(self, channelName: str, creatorName: str, usersCount: int):
        self.channelName = channelName
        self.creatorName = creatorName
        self.usersCount = usersCount
        self.users = {}

    async def addUser(self, user):
        pass

    