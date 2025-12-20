from typing import List, Dict, Iterator
import json

class KeyPad:
    def __init__(self):
        self.list_KeyPads: List[Dict] = []

    def _create_button(self, id: str, button_text: str, type: str = "Simple") -> dict:
        return {"id": id, "type": type, "button_text": button_text}

    def append(self, *buttons: dict):
        if not buttons:
            raise ValueError("حداقل یک دکمه باید ارسال شود")

        self.list_KeyPads.append({
            "buttons": list(buttons)
        })

    def simple(self, id: str, button_text: str) -> dict:
        return self._create_button(id, button_text)

    def pop(self, index: int = -1):
        self.list_KeyPads.pop(index)

    def clear(self):
        self.list_KeyPads.clear()

    def get(self) -> list:
        return self.list_KeyPads
    
    def get_data_by_id(self, id: str) -> dict:
        """
            find button by id / پیدا کردن دکمه با آیدی

            Docstring for get_data_by_id
            
            :param id: Description
            :type id: str
            :return: Description
            :rtype: dict[Any, Any]
        """
        for buttons in self.list_KeyPads:
            for button in buttons["buttons"]:
                if button["id"] == id:
                    return button
        
        raise IndexError("The Id Not Found !")
    
    def get_all_by_id(self, id: str) -> List[dict]:
        """
        Find all buttons with given id.
        """
        result = []

        for row in self.list_KeyPads:
            for button in row["buttons"]:
                if button["id"] == id:
                    result.append(button)

        return result

    def remove_by_id(self, id: str) -> dict:
        """
        remove button by id / حذف دکمه با آیدی
        """
        for row_index, row in enumerate(self.list_KeyPads):
            buttons = row["buttons"]

            for btn_index, button in enumerate(buttons):
                if button["id"] == id:
                    removed = buttons.pop(btn_index)

                    # اگر سطر خالی شد، کل سطر حذف شود
                    if not buttons:
                        self.list_KeyPads.pop(row_index)

                    return removed

        raise KeyError(f"Button with id '{id}' not found")

    def remove_all_by_id(self, id: str) -> List[dict]:
        """
        Remove all buttons with given id.
        """
        removed = []

        for row in list(self.list_KeyPads):  # کپی برای حذف امن
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

    def get_all_buttons(self) -> List[dict]:
        return [
            button
            for row in self.list_KeyPads
            for button in row["buttons"]
        ]


    def __str__(self) -> str:
        return json.dumps(self.list_KeyPads,indent=4,ensure_ascii=False)

    def __repr__(self) -> str:
        return self.__str__()
    
    def __getitem__(self, index):
        return self.list_KeyPads[index]

    def __iter__(self) -> Iterator[Dict]:
        return iter(self.list_KeyPads)

    def __len__(self) -> int:
        return len(self.list_KeyPads)
