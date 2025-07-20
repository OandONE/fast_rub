from .methods import Methods


class Client(Methods):
    pass
    # async def send_message_keypad_InlineKeypad(self,chat_id:str,text:str,chat_keypad,inline_keypad,chat_keypad_type,disable_notification:bool=False,reply_to_message_id:Optional[str]=None):
    #     """مثال :
    #     {
    #                     "buttons": [
    #                         {
    #                             "id": "100",
    #                             "type": "Simple",
    #                             "button_text": "Add Account"
    #                         }
    #                     ]
    #                 },
    #                 {
    #                     "buttons": [
    #                         {
    #                             "id": "101",
    #                             "type": "Simple",
    #                             "button_text": "Edit Account"
    #                         },
    #                         {
    #                             "id": "102",
    #                             "type": "Simple",
    #                             "button_text": "Remove Account"
    #                         }
    #                     ]
    #                 }"""
    #     data = {
    #         "chat_id": chat_id,
    #         "text": "Welcome",
    #         "inline_keypad": {
    #             "rows": [
    #                 rows
    #             ]
    #         }
    #     }
    #     result=await self.send_request("sendMessage",data,request_type="post")
    #     return result
    # async def send_message_keypad(self,chat_id:str,text:str,chat_keypad_type,chat_keypad,disable_notification:bool=False,reply_to_message_id:Optional[str]=None):
    #     data = {
    #         "chat_id": chat_id,
    #         "text": "Welcome",
    #         "chat_keypad_type": "New",
    #         "chat_keypad": {
    #             "rows": [
    #                 {
    #                     "buttons": [
    #                         {
    #                             "id": "100",
    #                             "type": "Simple",
    #                             "button_text": "Add Account"
    #                         }
    #                     ]
    #                 },
    #                 {
    #                     "buttons": [
    #                         {
    #                             "id": "101",
    #                             "type": "Simple",
    #                             "button_text": "Edit Account"
    #                         },
    #                         {
    #                             "id": "102",
    #                             "type": "Simple",
    #                             "button_text": "Remove Account"
    #                         }
    #                     ]
    #                 }
    #             ],
    #             "resize_keyboard": True,
    #             "on_time_keyboard": False
    #         }
    #     }
    #     result=await self.send_request("sendMessage",data,request_type="post")
    #     return result
