from typing import Literal

ButtonType = Literal[
    "Simple", "Selection", "Calendar", "NumberPicker", "StringPicker", 
    "Location", "Payment", "CameraImage", "CameraVideo", "GalleryImage", 
    "GalleryVideo", "File", "Audio", "RecordAudio", "MyPhoneNumber", 
    "MyLocation", "Textbox", "Link", "AskMyPhoneNumber", "AskLocation", "Barcode"
]

class KeyPad:
    def __init__(self):
        self.list_KeyPads = []

    @property
    def list_types(self) -> Literal[
        "Simple", "Selection", "Calendar", "NumberPicker", "StringPicker", 
        "Location", "Payment", "CameraImage", "CameraVideo", "GalleryImage", 
        "GalleryVideo", "File", "Audio", "RecordAudio", "MyPhoneNumber", 
        "MyLocation", "Textbox", "Link", "AskMyPhoneNumber", "AskLocation", "Barcode"
    ]:
        return ButtonType
    
    def _create_button(self, id: str, button_text: str, type: ButtonType) -> dict:
        """ایجاد دیکشنری دکمه به صورت متمرکز"""
        return {"id": id, "type": type, "button_text": button_text}
    
    def add_1row(self, id: str, button_text: str, type: ButtonType = "Simple") -> None:
        """add key pad 1vs1 / افزودن کی پد یکی"""
        self.list_KeyPads.append({
            "buttons": [self._create_button(id, button_text, type)]
        })
    
    def add_2row(self, 
                id1: str, button_text1: str, 
                id2: str, button_text2: str,
                type1: ButtonType = "Simple", 
                type2: ButtonType = "Simple") -> None:
        """add key pad 2vs2 / افزودن کی پد دو تایی"""
        self.list_KeyPads.append({
            "buttons": [
                self._create_button(id1, button_text1, type1),
                self._create_button(id2, button_text2, type2)
            ]
        })
    
    def add_3row(self, 
                id1: str, button_text1: str,
                id2: str, button_text2: str,
                id3: str, button_text3: str,
                type1: ButtonType = "Simple",
                type2: ButtonType = "Simple", 
                type3: ButtonType = "Simple") -> None:
        """add key pad 3vs3 / افزودن کی پد سه تایی"""
        self.list_KeyPads.append({
            "buttons": [
                self._create_button(id1, button_text1, type1),
                self._create_button(id2, button_text2, type2),
                self._create_button(id3, button_text3, type3)
            ]
        })
    
    def add_4row(self, 
                id1: str, button_text1: str,
                id2: str, button_text2: str,
                id3: str, button_text3: str,
                id4: str, button_text4: str,
                type1: ButtonType = "Simple",
                type2: ButtonType = "Simple",
                type3: ButtonType = "Simple",
                type4: ButtonType = "Simple") -> None:
        """add key pad 4vs4 / افزودن کی پد چهار تایی"""
        self.list_KeyPads.append({
            "buttons": [
                self._create_button(id1, button_text1, type1),
                self._create_button(id2, button_text2, type2),
                self._create_button(id3, button_text3, type3),
                self._create_button(id4, button_text4, type4)
            ]
        })
    
    def get(self):
        return self.list_KeyPads
