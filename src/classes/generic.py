class BasicRecord:
    def __init__(
            self,
            id: int, 
            username: str, 
            title: str, 
            creatorUsername: str, 
            totalParticipants: int = -1, 
            totalMessages: int = -1,
            linkedChat: int | str | None = None,
            isChannel: bool = True,
            isSupergroup: bool = False
        ):
        self.id = id
        self.title = title
        self.usernamme = username
        self.creatorName = creatorUsername
        self.totalParticipants = totalParticipants
        self.linkedChat = linkedChat
        self.totalMessages = totalMessages
        self.isChannel = isChannel
        self.isSupergroup = isSupergroup
        self.membersFound = 0

        self.membersFound: int = 0
        self.adminsFound = 0
        self.subchannels = {}
        self.members = {}
        self.admins = {}

    def addUser(self, userId: int | str, user) -> None:
        if not self.getUser(userId):
            self.members[userId] = user
            self.membersFound += 1
    
    def addAdmin(self, userId: int | str, user) -> None:
        if not self.getAdmin(userId):
            self.admins[userId] = user
            self.adminsFound += 1

    def getUser(self, userId: int | str):
        return self.members.get(userId)
    
    def getAdmin(self, userId: int | str):
        return self.admins.get(userId)
    
    def addSubChannel(self, userName: str, subchannelRecord):
        self.subchannels[userName] = subchannelRecord

    def __repr__(self):
        return f"{self.__class__.__name__}(Name={self.title}, Username={self.usernamme}, creatorName={self.creatorName}, usersFound={self.membersFound}))"

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, BasicRecord):
            return self.id == other.id
        if isinstance(other, int):
            return self.id == other
        return False