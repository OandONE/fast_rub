import json
from typing import Optional

class metadata:
    def __init__(self, data:list) -> None:
        self.data = data
    def from_index(self, index:int) -> int:
        """from index / از اندیس"""
        return self.data[index]["from_index"]
    def length(self, index:int) -> int:
        """len / اندازه"""
        return self.data[index]["length"]
    def type(self, index:int) -> str:
        """type / نوع"""
        return self.data[index]["type"]
    def link_url(self, index:int) -> Optional[str]:
        """link / لینک"""
        return self.data[index]["link_url"] if "link_url" in self.data[index] else None
    def __str__(self) -> str:
        return json.dumps(self.data,indent=4,ensure_ascii=False)
    def __repr__(self) -> str:
        return self.__str__()
