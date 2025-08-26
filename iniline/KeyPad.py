class KeyPad:
    def __init__(self):
        """Create KeyPad / ساخت کی پد"""
        self.list_KeyPads = []
    def add_1row(self,id: str,button_text: str, type: str = "Simple"):
        """add key pad 1vs1 / افزودن کی پد یکی"""
        self.list_KeyPads.append(
            {"buttons": [{"id": id, "type": type, "button_text": button_text}]}
        )
    def add_2row(self,id1: str, button_text1: str, id2: str,button_text2: str,type1: str = "Simple",type2: str = "Simple"):
        """add key pad 2vs2 / افزودن کی پد دو تایی"""
        self.list_KeyPads.append(
            {
                "buttons": [
                    {"id": id1, "type": type1, "button_text": button_text1},
                    {"id": id2, "type": type2, "button_text": button_text2},
                ]
            }
        )
    def add_3row(self,id1: str, button_text1: str,id2: str,button_text2: str,id3: str,button_text3: str,type1: str = "Simple",type2: str = "Simple",type3: str = "Simple"):
        """add key pad 3vs3 / افزودن کی پد سه تایی"""
        self.list_KeyPads.append(
            {
                "buttons": [
                    {"id": id1, "type": type1, "button_text": button_text1},
                    {"id": id2, "type": type2, "button_text": button_text2},
                    {"id": id3, "type": type3, "button_text": button_text3},
                ]
            }
        )
    def add_4row(self,id1: str, button_text1: str,id2: str,button_text2: str,id3: str,button_text3: str,id4: str,type4: str,button_text4: str,type1: str = "Simple",type2: str = "Simple",type3: str = "Simple"):
        """add key pad 4vs4 / افزودن کی پد چهار تایی"""
        self.list_KeyPads.append(
            {
                "buttons": [
                    {"id": id1, "type": type1, "button_text": button_text1},
                    {"id": id2, "type": type2, "button_text": button_text2},
                    {"id": id3, "type": type3, "button_text": button_text3},
                    {"id": id4, "type": type4, "button_text": button_text4},
                ]
            }
        )
    def add_data(self,data:dict):
        """add data to list key pads / افزودن دستی دیتا به لیست کی پد ها"""
        self.list_KeyPads.append(data)
    def get(self) -> list:
        """getting list key pads / گرفتن لیست کی پد ها"""
        return self.list_KeyPads