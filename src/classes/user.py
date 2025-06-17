from src.classes import channel
class UserRecord:
    def __init__(self, user):
        self.id = user.id
        self.username = user.username
        self.full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        self.is_bot = user.bot
        self.is_verified = user.verified
        self.is_premium = user.premium
        self.status = type(user.status).__name__ if user.status else "Unknown"
        self.is_scam = user.scam
        self.is_fake = user.fake
        self.lang_code = user.lang_code
        self.emoji_status = getattr(user.emoji_status, 'document_id', None)
        self.phone = user.phone
        self.adminInChannel = set()
        self.capturedMessages = {}
        
    def __repr__(self):
        return f"<UserRecord {self.full_name} @{self.username} ({self.status})>"

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, UserRecord):
            return self.id == other.id
        elif isinstance(other, int):
            return self.id == other
        return False
