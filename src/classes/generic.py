from src.classes.user import UserRecord


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
        isSupergroup: bool = False,
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
        self.members: dict[int, UserRecord] = {}
        self.admins: dict[int, UserRecord] = {}

    def addUser(self, userId: int | str, user) -> None:
        if not self.getUser(userId):
            self.members[userId] = user
            self.membersFound += 1

    def addAdmin(self, admId, admin) -> None:
        if not self.getAdmin(admId):
            self.admins[admId] = admin
            self.adminsFound += 1
            self.members[admId].adminInChannel.add(self.id)

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
