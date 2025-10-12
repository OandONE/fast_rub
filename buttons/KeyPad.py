from typing import Literal, List, Dict,Optional

ButtonType = Literal[
    "simple", "Selection", "Calendar", "NumberPicker", "StringPicker",
    "Location", "Payment", "CameraImage", "CameraVideo", "GalleryImage",
    "GalleryVideo", "File", "Audio", "RecordAudio", "MyPhoneNumber",
    "MyLocation", "Textbox", "Link", "AskMyPhoneNumber", "AskLocation", "Barcode"
]


class KeyPad:
    def __init__(self):
        self.list_KeyPads: List[Dict] = []

    def _create_button(self, id: str, button_text: Optional[str]=None, type: ButtonType = "simple",dict_:Optional[dict]=None) -> dict:
        if not dict_:
            return {"id": id, "type": type, "button_text": button_text}
        dict_["id"] = id
        dict_["type"] = type
        dict_["button_text"] = button_text
        return dict_

    def get(self) -> list:
        """getting buttons list / گرفتن لیست دکمه ها"""
        return self.list_KeyPads

    def clear(self):
        """clear list buttons / پاکسازی لیست دکمه ها"""
        self.list_KeyPads.clear()

    def add_1row(self): return _RowBuilder1(self)
    def add_2row(self): return _RowBuilder2(self)
    def add_3row(self): return _RowBuilder3(self)
    def add_4row(self): return _RowBuilder4(self)


class _RowBuilder1:
    def __init__(self, parent: KeyPad):
        self.parent = parent

    def simple(self, id: str, button_text: str) -> 'KeyPad':
        self.parent.list_KeyPads.append({
            "buttons": [self.parent._create_button(id, button_text)]
        })
        return self.parent

    def text_box(self,id:str,text:str,hint:str,type_input:Literal["Number","String"]="String",line_hint:Literal["MultiLine","SingleLine"]="SingleLine"):
        self.parent.list_KeyPads.append({
            "buttons":[self.parent._create_button(id,button_text=text,type="Textbox",dict_={"type_line": line_hint,"type_keypad": type_input,"title":hint})]
        })
        return self.parent

class _RowBuilder2:
    def __init__(self, parent: KeyPad):
        self.parent = parent

    def simple(self,
        id1: str, button_text1: str,
        id2: str, button_text2: str
    ) -> 'KeyPad':
        self.parent.list_KeyPads.append({
            "buttons": [
                self.parent._create_button(id1, button_text1),
                self.parent._create_button(id2, button_text2)
            ]
        })
        return self.parent
    def text_box(self,id:str,text:str,hint:str,id2:str,text2:str,hint2:str,type_input:Literal["Number","String"]="String",line_hint:Literal["MultiLine","SingleLine"]="SingleLine",type_input2:Literal["Number","String"]="String",line_hint2:Literal["MultiLine","SingleLine"]="SingleLine"):
        self.parent.list_KeyPads.append({
            "buttons":[
                self.parent._create_button(id,button_text=text,type="Textbox",dict_={"type_line": line_hint,"type_keypad": type_input,"title":hint}),
                self.parent._create_button(id2,button_text=text2,type="Textbox",dict_={"type_line": line_hint2,"type_keypad": type_input2,"title":hint2})
            ]
        })
        return self.parent

class _RowBuilder3:
    def __init__(self, parent: KeyPad):
        self.parent = parent

    def simple(self,
        id1: str, button_text1: str,
        id2: str, button_text2: str,
        id3: str, button_text3: str
    ) -> 'KeyPad':
        self.parent.list_KeyPads.append({
            "buttons": [
                self.parent._create_button(id1, button_text1),
                self.parent._create_button(id2, button_text2),
                self.parent._create_button(id3, button_text3)
            ]
        })
        return self.parent

    def text_box(
        self,
        id1: str, text1: str, hint1: str,
        id2: str, text2: str, hint2: str,
        id3: str, text3: str, hint3: str,
        type_input1: Literal["Number", "String"] = "String",
        line_hint1: Literal["MultiLine", "SingleLine"] = "SingleLine",
        type_input2: Literal["Number", "String"] = "String",
        line_hint2: Literal["MultiLine", "SingleLine"] = "SingleLine",
        type_input3: Literal["Number", "String"] = "String",
        line_hint3: Literal["MultiLine", "SingleLine"] = "SingleLine"
    ) -> 'KeyPad':
        self.parent.list_KeyPads.append({
            "buttons": [
                self.parent._create_button(id1, button_text=text1, type="Textbox",
                    dict_={"type_line": line_hint1, "type_keypad": type_input1, "title": hint1}),
                self.parent._create_button(id2, button_text=text2, type="Textbox",
                    dict_={"type_line": line_hint2, "type_keypad": type_input2, "title": hint2}),
                self.parent._create_button(id3, button_text=text3, type="Textbox",
                    dict_={"type_line": line_hint3, "type_keypad": type_input3, "title": hint3})
            ]
        })
        return self.parent


class _RowBuilder4:
    def __init__(self, parent: KeyPad):
        self.parent = parent

    def simple(self,
        id1: str, button_text1: str,
        id2: str, button_text2: str,
        id3: str, button_text3: str,
        id4: str, button_text4: str
    ) -> 'KeyPad':
        self.parent.list_KeyPads.append({
            "buttons": [
                self.parent._create_button(id1, button_text1),
                self.parent._create_button(id2, button_text2),
                self.parent._create_button(id3, button_text3),
                self.parent._create_button(id4, button_text4)
            ]
        })
        return self.parent

    def text_box(
        self,
        id1: str, text1: str, hint1: str,
        id2: str, text2: str, hint2: str,
        id3: str, text3: str, hint3: str,
        id4: str, text4: str, hint4: str,
        type_input1: Literal["Number", "String"] = "String",
        line_hint1: Literal["MultiLine", "SingleLine"] = "SingleLine",
        type_input2: Literal["Number", "String"] = "String",
        line_hint2: Literal["MultiLine", "SingleLine"] = "SingleLine",
        type_input3: Literal["Number", "String"] = "String",
        line_hint3: Literal["MultiLine", "SingleLine"] = "SingleLine",
        type_input4: Literal["Number", "String"] = "String",
        line_hint4: Literal["MultiLine", "SingleLine"] = "SingleLine"
    ) -> 'KeyPad':
        self.parent.list_KeyPads.append({
            "buttons": [
                self.parent._create_button(id1, button_text=text1, type="Textbox",
                    dict_={"type_line": line_hint1, "type_keypad": type_input1, "title": hint1}),
                self.parent._create_button(id2, button_text=text2, type="Textbox",
                    dict_={"type_line": line_hint2, "type_keypad": type_input2, "title": hint2}),
                self.parent._create_button(id3, button_text=text3, type="Textbox",
                    dict_={"type_line": line_hint3, "type_keypad": type_input3, "title": hint3}),
                self.parent._create_button(id4, button_text=text4, type="Textbox",
                    dict_={"type_line": line_hint4, "type_keypad": type_input4, "title": hint4})
            ]
        })
        return self.parent
