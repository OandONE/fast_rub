from collections.abc import Iterator
import json


class RowBuilder:
    """سازنده یک ردیف از دکمه‌ها"""
    def __init__(self, keypad: 'KeyPad'):
        self._keypad = keypad
        self._buttons: list[dict] = []

    def simple(self, id: str, button_text: str) -> 'RowBuilder':
        """اضافه کردن یه دکمه ساده به این ردیف"""
        self._buttons.append({"id": id, "type": "Simple", "button_text": button_text})
        return self

    def done(self) -> 'KeyPad':
        """تموم شدن این ردیف و برگشت به KeyPad"""
        if self._buttons:
            self._keypad.list_KeyPads.append({"buttons": self._buttons})
        return self._keypad


class KeyPad:
    """کیپد روبیکا — Builder Pattern"""
    
    def __init__(self):
        self.list_KeyPads: list[dict] = []

    @property
    def row(self) -> RowBuilder:
        """شروع یه ردیف جدید"""
        return RowBuilder(self)

    def simple(self, id: str, button_text: str) -> dict:
        return {"id": id, "type": "Simple", "button_text": button_text}

    def append(self, *buttons: dict):
        if not buttons:
            raise ValueError("حداقل یک دکمه باید ارسال شود")
        self.list_KeyPads.append({"buttons": list(buttons)})

    add = append

    def pop(self, index: int = -1):
        self.list_KeyPads.pop(index)

    def clear(self):
        self.list_KeyPads.clear()

    def get(self) -> list:
        return self.list_KeyPads

    build = get

    def get_data_by_id(self, id: str) -> dict:
        for buttons in self.list_KeyPads:
            for button in buttons["buttons"]:
                if button["id"] == id:
                    return button
        raise IndexError("The Id Not Found !")

    def get_all_by_id(self, id: str) -> list[dict]:
        result = []
        for row in self.list_KeyPads:
            for button in row["buttons"]:
                if button["id"] == id:
                    result.append(button)
        return result

    def remove_by_id(self, id: str) -> dict:
        for row_index, row in enumerate(self.list_KeyPads):
            buttons = row["buttons"]
            for btn_index, button in enumerate(buttons):
                if button["id"] == id:
                    removed = buttons.pop(btn_index)
                    if not buttons:
                        self.list_KeyPads.pop(row_index)
                    return removed
        raise KeyError(f"Button with id '{id}' not found")

    def remove_all_by_id(self, id: str) -> list[dict]:
        removed = []
        for row in list(self.list_KeyPads):
            buttons = row["buttons"]
            for button in buttons[:]:
                if button["id"] == id:
                    buttons.remove(button)
                    removed.append(button)
            if not buttons:
                self.list_KeyPads.remove(row)
        if not removed:
            raise KeyError(f"Button with id '{id}' not found")
        return removed

    def get_all_buttons(self) -> list[dict]:
        return [button for row in self.list_KeyPads for button in row["buttons"]]

    def __str__(self) -> str:
        return json.dumps(self.list_KeyPads, indent=4, ensure_ascii=False)

    def __repr__(self) -> str:
        return self.__str__()

    def __getitem__(self, index):
        return self.list_KeyPads[index]

    def __iter__(self) -> Iterator[dict]:
        return iter(self.list_KeyPads)

    def __len__(self) -> int:
        return len(self.list_KeyPads)
