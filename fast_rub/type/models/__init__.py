import json

class _BaseModels:
    def __init__(
        self,
        data: dict
    ) -> None:
        self.data = data
    
    def to_dict(
        self
    ) -> dict:
        """convert Update to Dict / تبدیل آپدیت به دیکشنری"""
        return self.data
    
    def get(
        self,
        key: str,
        defult = None
    ):
        try:
            return self.data[key]
        except:
            return defult
    
    def __setitem__(
        self,
        key,
        value
    ):
        self.data[key] = value
    
    def __getitem__(
        self,
        key
    ):
        result = self.get(key)
        if not result:
            raise KeyError(f"The {key} has not in datas .")
        return result

    def __str__(self) -> str:
        return json.dumps(
            self.to_dict(),
            indent=4,
            ensure_ascii=False
        )

    def __repr__(self) -> str:
        return self.__str__()

class Bot(_BaseModels):
    @property
    def bot_id(self) -> str:
        return self.data["bot_id"]
    @property
    def bot_title(self) -> str:
        return self.data["bot_title"]
    @property
    def description(self) -> str:
        return self.data["description"]
    @property
    def username(self) -> str:
        return self.data["username"]
    @property
    def start_message(self) -> str:
        return self.data["start_message"]
    @property
    def share_url(self) -> str:
        return self.data["share_url"]

class Chat(_BaseModels):
    @property
    def first_name(self) -> str:
        return self.data["first_name"]
    @property
    def title(self) -> str:
        return self.data["title"]
    @property
    def user_id(self) -> str:
        return self.data["user_id"]
    @property
    def chat_id(self) -> str:
        return self.data["chat_id"]
    @property
    def last_name(self) -> str:
        return self.data["last_name"]
