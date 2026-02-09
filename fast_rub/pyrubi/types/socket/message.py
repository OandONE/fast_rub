from ....core.async_sync import *
from typing import (
    Optional,
    Any,
    TYPE_CHECKING,
    Literal,
    Union
)

if TYPE_CHECKING:
    from ...methods.methods import Methods

class ReplyInfo:
    def __init__(self, text, author_guid) -> None:
        self.text = text
        self.author_guid = author_guid
        pass

    @classmethod
    def from_json(cls, json: dict):
        return cls(json["text"], json["author_object_guid"])

class Message:
    def __init__(self, data:dict, methods:'Methods') -> None:
        self.data = data
        self.methods = methods

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        keys = key.split(".")
        value = self.data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            elif isinstance(value, list) and k.isdigit():
                value = value[int(k)]
            else:
                return None
        return value

    def get(self, key: str, default: Any = None) -> Any:
        value = self[key]
        return value if value is not None else default

    @property
    def object_guid(self) -> str:
        return self.data["chat_updates"][0].get("object_guid")
    
    @property
    def chat_type(self) -> str:
        return self.data["chat_updates"][0].get("type")
    
    @property
    def count_unseen(self) -> int:
        return int(self.data["chat_updates"][0]["chat"].get("count_unseen", 0))
    
    @property
    def last_seen_peer_mid(self) -> str:
        return self.data["chat_updates"][0]["chat"].get("last_seen_peer_mid")
    
    @property
    def time_string(self) -> str:
        return self.data["chat_updates"][0]["chat"].get("time_string")
    
    @property
    def is_mine(self) -> bool:
        return self.data["chat_updates"][0]["chat"]["last_message"].get("is_mine")
    
    @property
    def time(self) -> str:
        return self.data["chat_updates"][0]["chat"]["last_message"].get("time")
    
    @property
    def status(self) -> str:
        return self.data["chat_updates"][0]["chat"].get("status")
    
    @property
    def last_message_id(self) -> str:
        return self.data["chat_updates"][0]["chat"].get("last_message_id")
    
    @property
    def action(self) -> str:
        return self.data["message_updates"][0].get("action")
    
    @property
    def message_id(self) -> str:
        return self.data["message_updates"][0].get("message_id")
    
    @property
    def reply_message_id(self) -> str:
        return self.data["message_updates"][0]["message"].get("reply_to_message_id")
    
    @property
    def text(self) -> str:
        return str(self.data["message_updates"][0]["message"].get("text"))
    
    @property
    def is_edited(self) -> bool:
        return self.data["message_updates"][0]["message"].get("is_edited")
    
    @property
    def message_type(self) -> str:
        if self.file_inline:
            return self.file_inline["type"]
        
        return self.data["message_updates"][0]["message"].get("type")
    
    @property
    def author_type(self) -> str:
        return self.data["message_updates"][0]["message"].get("author_type")
    
    @property
    def author_guid(self) -> str:
        return self.data["message_updates"][0]["message"].get("author_object_guid")
    
    @property
    def prev_message_id(self) -> str:
        return self.data["message_updates"][0].get("prev_message_id")
    
    @property
    def state(self) -> str:
        return self.data["message_updates"][0].get("state")
    
    @property
    def title(self) -> Optional[str]:
        if self.data['show_notifications']:
            return self.data['show_notifications'][0].get('title')
    
    @property
    def author_title(self) -> str:
        return self.data['chat_updates'][0]['chat']['last_message'].get('author_title', self.title)
    
    @property
    def is_user(self) -> bool:
        return self.chat_type == "User"
    
    @property
    def is_group(self) -> bool:
        return self.chat_type == "Group"
    
    @property
    def is_forward(self) -> bool:
        return "forwarded_from" in self.data["message_updates"][0]["message"].keys()
    
    @property
    def forward_from(self) -> Optional[str]:
        return self.data["message_updates"][0]["message"]["forwarded_from"].get("type_from") if self.is_forward else None
    
    @property
    def forward_object_guid(self) -> Optional[str]:
        return self.data["message_updates"][0]["message"]["forwarded_from"].get("object_guid") if self.is_forward else None
    
    @property
    def forward_message_id(self) -> Optional[str]:
        return self.data["message_updates"][0]["message"]["forwarded_from"].get("message_id") if self.is_forward else None

    @property
    def is_event(self) -> bool:
        return 'event_data' in self.data['message_updates'][0]['message'].keys()
    
    @property
    def event_type(self) -> Optional[str]:
        return self.data['message_updates'][0]['message']['event_data'].get('type') if self.is_event else None
    
    @property
    def event_object_guid(self) -> Optional[str]:
        return self.data['message_updates'][0]['message']['event_data']['performer_object'].get('object_guid') if self.is_event else None
    
    @property
    def pinned_message_id(self) -> Optional[str]:
        return self.data['message_updates'][0]['message']['event_data'].get('pinned_message_id') if self.is_event else None
    
    @property
    def file_inline(self) -> dict:
        return self.data["message_updates"][0]["message"].get("file_inline")

    @property
    def has_link(self) -> bool:
        for link in ["http:/", "https:/", "www.", ".ir", ".com", ".net" "@"]:
            if link in self.text.lower():
                return True
        return False
    
    @auto_async
    async def reply_info(self) -> Optional[ReplyInfo]:
        if not self.reply_message_id:
            return
        return ReplyInfo.from_json((await self.methods.getMessagesById(self.object_guid, [self.reply_message_id]))["messages"][0])
    
    @auto_async
    async def reply(self, text:str) -> dict:
        return await self.methods.sendText(objectGuid=self.object_guid, text=text, messageId=self.message_id)

    @auto_async
    async def reply_image(self,file:str, text:Optional[str], file_name:Optional[str] = None,thumbInline: Optional[str] = None,is_spoil: bool = False):
        return await self.methods.sendImage(self.object_guid,file,self.message_id,text,is_spoil,thumbInline,file_name)
    
    @auto_async
    async def reply_video(self,file:str, text:Optional[str], file_name:Optional[str] = None,thumbInline: Optional[str] = None,is_spoil: bool = False):
        return await self.methods.sendVideo(self.object_guid,file,self.message_id,text,is_spoil,thumbInline,file_name)

    @auto_async
    async def reply_gif(self,file:str, text:Optional[str], file_name:Optional[str] = None,thumbInline: Optional[str] = None):
        return await self.methods.sendGif(self.object_guid,file,self.message_id,text,thumbInline,file_name)

    @auto_async
    async def reply_music(self,file:str, text:Optional[str], file_name:Optional[str] = None,performer: Optional[str] = None):
        return await self.methods.sendMusic(self.object_guid,file,self.message_id,text,file_name,performer)

    @auto_async
    async def reply_voice(self,file:str, time:int = 0, text:Optional[str] = None, file_name:Optional[str] = None):
        return await self.methods.sendVoice(self.object_guid,file,time,self.message_id,text,file_name)
    
    @auto_async
    async def reply_location(self,latitude:int, longitude:int):
        return await self.methods.sendLocation(self.object_guid,latitude,longitude,self.message_id)

    @auto_async
    async def reply_video_message(self,file:str, text:Optional[str], file_name:Optional[str],thumbInline: Optional[str] = None):
        return await self.methods.sendVideoMessage(self.object_guid,file,self.message_id,text,thumbInline,file_name)

    @auto_async
    async def reply_poll(
        self,
        question: str,
        options: list,
        allows_multiple_responses: bool = True,
        is_anonymous: bool = False,
        type: Literal["Quiz", "Regular"] = "Regular",
        correct_option_index: Optional[int] = None,
        hint: Optional[str] = None
    ):
        return await self.methods.sendPoll(
            objectGuid=self.object_guid,
            question=question,
            options=options,
            messageId=self.message_id,
            allowsMultipleResponses=allows_multiple_responses,
            isAnonymous=is_anonymous,
            type=type,
            correctOptionIndex=correct_option_index,
            hint=hint
        )

    @auto_async
    async def seen(self) -> dict:
        return await self.methods.seenChats(seenList={self.object_guid: self.message_id})
    
    @auto_async
    async def reaction(self, reaction: Union[int, str]) -> dict:
        return await self.methods.actionOnMessageReaction(objectGuid=self.object_guid, messageId=self.message_id, reactionId=reaction, action="Add")
    
    @auto_async
    async def delete(self, delete_for_all: bool = True) -> dict:
        return await self.methods.deleteMessages(objectGuid=self.object_guid, messageIds=[self.message_id], deleteForAll=delete_for_all)
    
    @auto_async
    async def pin(self) -> dict:
        return await self.methods.setPinMessage(objectGuid=self.object_guid, messageId=self.message_id,action="Pin")
    
    @auto_async
    async def forward(self, to_object_guid:str) -> dict:
        return await self.methods.forwardMessages(objectGuid=self.object_guid, messageIds=[self.message_id], toObjectGuid=to_object_guid)
    
    @auto_async
    async def ban(self) -> dict:
        return await self.methods.banChatMember(objectGuid=self.object_guid, memberGuid=self.author_guid,action="Set")
    
    @auto_async
    async def check_join(self, object_guid:str) -> Optional[bool]:
        return await self.methods.checkJoin(objectGuid=object_guid, userGuid=self.author_guid)
    
    @auto_async
    async def download(self, save: bool = False, save_as: Optional[str] = None) -> Optional[dict]:
        return await self.methods.download(objectGuid=self.object_guid, save=save, saveAs=save_as, fileInline=self.file_inline)

