

class EditMessageKeypad:
    async def edit_message_keypad(self: "fast_rub.Client", chat_id: str, message_id: str, rows: list):
        """مثال rows :
        "rows": [
                {
                    "buttons": [
                    {
                        "id": "100",
                        "type": "Simple",
                        "button_text": "Add Account"
                    }
                    ]
                },
                {
                    "buttons": [
                    {
                        "id": "101",
                        "type": "Simple",
                        "button_text": "Edit Account"
                    },
                    {
                        "id": "102",
                        "type": "Simple",
                        "button_text": "Remove Account"
                    }
                    ]
                }
                ]"""
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "inline_keypad": {"rows": rows},
        }
        result = await self.send_request("editMessageText", data, request_type="post")
        return result