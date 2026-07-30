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
