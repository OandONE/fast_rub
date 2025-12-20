class Bot:
    def __init__(self, *, bot_id: str, bot_title: str,description: str,username: str, start_message: str, share_url: str):
        self._bot_id = bot_id
        self._bot_title = bot_title
        self._description = description
        self._username = username
        self._start_message = start_message
        self._share_url = share_url

    @property
    def bot_id(self) -> str:
        return self._bot_id
    
    @property
    def bot_title(self) -> str:
        return self._bot_title
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def start_message(self) -> str:
        return self._start_message
    
    @property
    def username(self) -> str:
        return self._username
    
    @property
    def share_url(self) -> str:
        return self._share_url

    def to_dict(self) -> dict:
        return {
            "bot_id": self._bot_id,
            "bot_title": self._bot_title,
            "description": self._description,
            "username": self._username,
            "description": self._description,
            "share_url": self._share_url
        }

    def __repr__(self):
        return f"Bot({self.to_dict()!r})"

    def __str__(self):
        import json
        return json.dumps(self.to_dict(), indent=4, ensure_ascii=False)