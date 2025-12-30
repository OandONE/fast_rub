from typing import Optional

class Chat:
    def __init__(self, *, first_name: Optional[str] = None, last_name: Optional[str] = None,user_id: Optional[str] = None,username: Optional[str] = None):
        self._first_name = first_name
        self._last_name = last_name
        self._user_id = user_id
        self._username = username

    @property
    def first_name(self) -> Optional[str]:
        return self._first_name
    
    @property
    def last_name(self) -> Optional[str]:
        return self._last_name
    
    @property
    def title(self) -> Optional[str]:
        return self._first_name
    
    @property
    def user_id(self) -> Optional[str]:
        return self._user_id
    
    @property
    def username(self) -> Optional[str]:
        return self._username

    def to_dict(self) -> dict:
        return {
            "first_name": self._first_name,
            "title": self._first_name,
            "last_name": self._last_name,
            "user_id": self._user_id,
            "username": self._username
        }

    def __repr__(self):
        return f"User({self.to_dict()!r})"

    def __str__(self):
        import json
        return json.dumps(self.to_dict(), indent=4, ensure_ascii=False)