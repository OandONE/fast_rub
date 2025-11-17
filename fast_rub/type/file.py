import json

class file:
    def __init__(self,data: dict):
        self.data = data
    @property
    def file_id(self) -> str:
        return self.data["file_id"]
    @property
    def file_name(self) -> str:
        return self.data["file_name"]
    @property
    def size(self) -> int:
        return self.data["size"]
    def __str__(self) -> str:
        return json.dumps(self.data,indent=4,ensure_ascii=False)
    def __repr__(self) -> str:
        return self.__str__()