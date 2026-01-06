from ..methods import Methods
from typing import (
    Optional,
    Union,
    List,
    Literal
)
from ...core.async_sync import *
from ..filters import Filter

class Client(object):

    def __init__(
        self,
        session: Optional[str] = None,
        auth: Optional[str] = None,
        private: Optional[str] = None,
        platform: Literal["web", "rubx", "android"] = "web",
        api_version: int = 6,
        proxy: Optional[str] = None,
        time_out = 10,
        show_progress_bar: bool = True
    ):
        
        self.session = session
        self.platform = platform
        self.apiVersion = api_version
        self.proxy = proxy
        self.timeOut = time_out
        
        if session:
            from ..sessions import Sessions
            self.sessions = Sessions(self)

            if self.sessions.cheackSessionExists():
                self.sessionData = self.sessions.loadSessionData()
            else:
                self.sessionData = self.sessions.createSession()
        else:
            from ..utils import Utils
            self.sessionData = {
                "auth": auth,
                "private_key": Utils.privateParse(private=private) if private else None
            }

        self.methods = Methods(
            sessionData=self.sessionData,
            platform=platform,
            apiVersion=api_version,
            proxy=proxy,
            timeOut=time_out,
            showProgressBar=show_progress_bar
        )

    # propertys
    
    @property
    def auth(self):
        return self.sessionData["auth"]
    
    @property
    def private_key(self):
        return self.sessionData["private_key"]

    # Authentication methods
    
    @async_to_sync
    async def send_code(self, phone_number:str, pass_key:Optional[str] = None) -> dict:
        return await self.methods.sendCode(phoneNumber=phone_number, passKey=pass_key)
    
    @async_to_sync
    async def sign_in(self, phone_number:str, phone_code_hash:str, phone_code:str) -> dict:
        return await self.methods.signIn(phoneNumber=phone_number, phoneCodeHash=phone_code_hash, phoneCode=phone_code)
    
    @async_to_sync
    async def register_device(self, device_model:str) -> dict:
        return await self.methods.registerDevice(deviceModel=device_model)
    
    @async_to_sync
    async def logout(self) -> dict:
        return await self.methods.logout()
    
    # Chats methods

    @async_to_sync
    async def get_chats(self, start_id:Optional[str] = None) -> dict:
        return await self.methods.getChats(startId=start_id)
    
    @async_to_sync
    async def get_object_by_username(self,user_name: str) -> dict:
        return await self.methods.getObjectByUsername(user_name)

    @async_to_sync
    async def get_top_users(self) -> dict:
        return await self.methods.getTopChatUsers()
    
    @async_to_sync
    async def remove_from_top_users(self, object_guid:str) -> dict:
        return await self.methods.removeFromTopChatUsers(objectGuid=object_guid)
    
    @async_to_sync
    async def get_chat_ads(self) -> dict:
        return await self.methods.getChatAds()
    
    @async_to_sync
    async def get_chats_updates(self) -> dict:
        return await self.methods.getChatsUpdates()
    
    @async_to_sync
    async def join_chat(self, guid_or_link:str) -> dict:
        return await self.methods.joinChat(guidOrLink=guid_or_link)

    @async_to_sync
    async def action_on_join_request(self, object_guid: str, user_guid: str, action: Literal["Accept", "Reject"]):
        return await self.methods.actionOnJoinRequest(objectGuid=object_guid, userGuid=user_guid, action=action)
    
    @async_to_sync
    async def getJoinRequests(self, object_guid: str):
        return await self.methods.getJoinRequests(objectGuid=object_guid)
    
    @async_to_sync
    async def leave_chat(self, object_guid:str) -> dict:
        return await self.methods.leaveChat(objectGuid=object_guid)
    
    @async_to_sync
    async def remove_chat(self, object_guid:str) -> dict:
        return await self.methods.removeChat(objectGuid=object_guid)
    
    @async_to_sync
    async def get_chat_info(self, object_guid:str) -> dict:
        return await self.methods.getChatInfo(objectGuid=object_guid)
    
    @async_to_sync
    async def get_chat_info_by_username(self, username:str) -> dict:
        return await self.methods.getChatInfoByUsername(username=username)

    @async_to_sync
    async def get_link(self, object_guid:str) -> dict:
        return await self.methods.getChatLink(objectGuid=object_guid)
    
    @async_to_sync
    async def set_link(self, object_guid:str) -> dict:
        return await self.methods.setChatLink(objectGuid=object_guid)
    
    @async_to_sync
    async def set_admin(self, object_guid:str, member_guid:str, access_list:Optional[list], custom_title:Optional[str] = None) -> dict:
        return await self.methods.setChatAdmin(objectGuid=object_guid, memberGuid=member_guid, accessList=access_list, customTitle=custom_title, action="SetAdmin")
    
    @async_to_sync
    async def unset_admin(self, object_guid:str, member_guid:str) -> dict:
        return await self.methods.setChatAdmin(objectGuid=object_guid, memberGuid=member_guid, accessList=None, customTitle=None, action="UnsetAdmin")
    
    @async_to_sync
    async def add_member(self, object_guid:str, member_guids:Union[list,str]) -> dict:
        if isinstance(member_guids,str):
            member_guids = [member_guids]
        return await self.methods.addChatMember(objectGuid=object_guid, memberGuids=member_guids)

    @async_to_sync
    async def ban_member(self, object_guid:str, member_guid:str) -> dict:
        return await self.methods.banChatMember(objectGuid=object_guid, memberGuid=member_guid, action="Set")
    
    @async_to_sync
    async def unban_member(self, object_guid:str, member_guid:str) -> dict:
        return await self.methods.banChatMember(objectGuid=object_guid, memberGuid=member_guid, action="Unset")
    
    @async_to_sync
    async def get_banned_members(self, object_guid:str, start_id:Optional[str] = None) -> dict:
        return await self.methods.getBannedChatMembers(objectGuid=object_guid, startId=start_id)

    @async_to_sync
    async def get_all_members(self, object_guid:str, search_text:Optional[str] = None, start_id:Optional[str] = None, just_get_guids:bool=False) -> Union[dict,list]:
        return await self.methods.getChatAllMembers(objectGuid=object_guid, searchText=search_text, startId=start_id, justGetGuids=just_get_guids)
    
    @async_to_sync
    async def get_admin_members(self, object_guid:str, start_id:Optional[str] = None, just_get_guids:bool=False) -> Union[dict,list]:
        return await self.methods.getChatAdminMembers(objectGuid=object_guid, startId=start_id, justGetGuids=just_get_guids)
    
    @async_to_sync
    async def user_is_admin(self, object_guid: str, user_guid: str):
        return await self.methods.userIsAdmin(objectGuid=object_guid,userGuid=user_guid)
    
    @async_to_sync
    async def get_admin_access_list(self, object_guid:str, member_guid:str) -> dict:
        return await self.methods.getChatAdminAccessList(objectGuid=object_guid, memberGuid=member_guid)
    
    @async_to_sync
    async def get_chat_preview(self, link:str) -> dict:
        return await self.methods.chatPreviewByJoinLink(link=link)
    
    @async_to_sync
    async def create_voice_chat(self, object_guid:str) -> dict:
        return await self.methods.createChatVoiceChat(objectGuid=object_guid)
    
    @async_to_sync
    async def join_voice_chat(self, object_guid:str, my_guid:str, voice_chat_id:str,sdp_offer_data:str) -> dict:
        return await self.methods.joinVoiceChat(objectGuid=object_guid, myGuid=my_guid, voiceChatId=voice_chat_id,sdp_offer_data=sdp_offer_data)
    
    @async_to_sync
    async def set_voice_chat_setting(self, object_guid:str, voice_chat_id:str, title:Optional[str] = None, join_mute:Optional[bool]=None) -> dict:
        return await self.methods.setChatVoiceChatSetting(objectGuid=object_guid, voideChatId=voice_chat_id, title=title, joinMuted=join_mute)
    
    @async_to_sync
    async def get_voice_chat_updates(self, object_guid:str, voice_chat_id:str) -> dict:
        return await self.methods.getChatVoiceChatUpdates(objectGuid=object_guid, voideChatId=voice_chat_id)
    
    @async_to_sync
    async def get_voice_chat_participants(self, object_guid:str, voice_chat_id:str) -> dict:
        return await self.methods.getChatVoiceChatParticipants(objectGuid=object_guid, voideChatId=voice_chat_id)
    
    @async_to_sync
    async def set_voice_chat_state(self, object_guid:str, voice_chat_id:str, activity:str,participantObjectGuid:str) -> dict:
        return await self.methods.setChatVoiceChatState(objectGuid=object_guid, voideChatId=voice_chat_id, activity=activity,participantObjectGuid=participantObjectGuid)
    
    @async_to_sync
    async def send_voice_chat_activity(self, object_guid:str, voice_chat_id:str, activity:str, participant_object_guid:str) -> dict:
        return await self.methods.sendChatVoiceChatActivity(objectGuid=object_guid, voideChatId=voice_chat_id, activity=activity, participantObjectGuid=participant_object_guid)    
    
    @async_to_sync
    async def leave_voice_chat(self, object_guid:str, voice_chat_id:str) -> dict:
        return await self.methods.leaveChatVoiceChat(objectGuid=object_guid, voideChatId=voice_chat_id)
    
    @async_to_sync
    async def discard_voice_chat(self, object_guid:str, voice_chat_id:str) -> dict:
        return await self.methods.discardChatVoiceChat(objectGuid=object_guid, voideChatId=voice_chat_id)
    
    @async_to_sync
    async def pin_chat(self, object_guid:str) -> dict:
        return await self.methods.setActionChat(objectGuid=object_guid, action="Pin")
    
    @async_to_sync
    async def unpin_chat(self, object_guid:str) -> dict:
        return await self.methods.setActionChat(objectGuid=object_guid, action="Unpin")
    
    @async_to_sync
    async def mute_chat(self, object_guid:str) -> dict:
        return await self.methods.setActionChat(objectGuid=object_guid, action="Mute")
    
    @async_to_sync
    async def unmute_chat(self, object_guid:str) -> dict:
        return await self.methods.setActionChat(objectGuid=object_guid, action="Unmute")
    
    @async_to_sync
    async def seen_chats(self, seen_list:dict) -> dict:
        """
        ```python

        seen_list : dict = {"object_guid": "message_id", "object_guid": "message_id", ...}

        ```
        """
        return await self.methods.seenChats(seenList=seen_list)
    
    @async_to_sync
    async def send_chat_activity(self, object_guid:str, activity:str) -> dict:
        return await self.methods.sendChatActivity(objectGuid=object_guid, activity=activity)
    
    @async_to_sync
    async def search_chat_messages(self, object_guid:str, search_text:str) -> dict:
        return await self.methods.searchChatMessages(objectGuid=object_guid, searchText=search_text)
    
    @async_to_sync
    async def upload_avatar(self, object_guid:str, main_file:str, thumbnail_file:Optional[str] = None) -> Optional[dict]:
        return await self.methods.uploadAvatar(objectGuid=object_guid, mainFile=main_file, thumbnailFile=thumbnail_file)
    
    @async_to_sync
    async def getAvatars(self, object_guid:str) -> dict:
        return await self.methods.getAvatars(objectGuid=object_guid)
    
    @async_to_sync
    async def delete_avatar(self, object_guid:str, avatar_id:str) -> dict:
        return await self.methods.deleteAvatar(objectGuid=object_guid, avatarId=avatar_id)
    
    @async_to_sync
    async def delete_history(self, object_guid:str, last_message_id:str) -> dict:
        return await self.methods.deleteChatHistory(objectGuid=object_guid, lastMessageId=last_message_id)
    
    @async_to_sync
    async def delete_user_chat(self, user_guid:str, last_deleted_message_id:str) -> dict:
        return await self.methods.deleteUserChat(userGuid=user_guid, lastDeletedMessageId=last_deleted_message_id)
    
    @async_to_sync
    async def get_pending_owner(self, object_guid:str) -> dict:
        return await self.methods.getPendingObjectOwner(objectGuid=object_guid)
    
    @async_to_sync
    async def request_change_owner(self, object_guid:str, member_guid:str) -> dict:
        return await self.methods.requestChangeObjectOwner(objectGuid=object_guid, memberGuid=member_guid)
    
    @async_to_sync
    async def accept_request_owner(self, object_guid:str) -> dict:
        return await self.methods.replyRequestObjectOwner(objectGuid=object_guid, action="Accept")
    
    @async_to_sync
    async def reject_request_owner(self, object_guid:str) -> dict:
        return await self.methods.replyRequestObjectOwner(objectGuid=object_guid, action="Reject")
    
    @async_to_sync
    async def cancel_change_owner(self, object_guid:str) -> dict:
        return await self.methods.cancelChangeObjectOwner(objectGuid=object_guid)
    
    @async_to_sync
    async def get_chat_reaction(self, object_guid:str, min_id:str, max_id:str) -> dict:
        return await self.methods.getChatReaction(objectGuid=object_guid, minId=min_id, maxId=max_id)
    
    @async_to_sync
    async def report_chat(self, object_guid:str, description:str) -> dict:
        return await self.methods.reportObject(objectGuid=object_guid, description=description)
    
    @async_to_sync
    async def set_chat_use_time(self, object_guid:str, time:int) -> dict:
        return await self.methods.setChatUseTime(objectGuid=object_guid, time=time)
    
    # User methods
    
    @async_to_sync
    async def block_user(self, object_guid:str) -> dict:
        return await self.methods.setBlockUser(objectGuid=object_guid, action="Block")
    
    @async_to_sync
    async def unblock_user(self, object_guid:str) -> dict:
        return await self.methods.setBlockUser(objectGuid=object_guid, action="Unblock")
    
    @async_to_sync
    async def check_user_username(self, username:str) -> dict:
        return await self.methods.checkUserUsername(username=username)
    
    # Group methods
    
    @async_to_sync
    async def add_group(self, title:str, member_guids:list) -> dict:
        return await self.methods.addGroup(title=title, memberGuids=member_guids)
    
    @async_to_sync
    async def get_group_default_access(self, object_guid:str) -> dict:
        return await self.methods.getGroupDefaultAccess(objectGuid=object_guid)
    
    @async_to_sync
    async def set_group_default_access(self, object_guid:str, access_list:list=[]) -> dict:
        return await self.methods.setChatDefaultAccess(objectGuid=object_guid, accessList=access_list)

    @async_to_sync
    async def get_group_mention_list(self, object_guid:str, search_mention:str) -> dict:
        return await self.methods.getGroupMentionList(objectGuid=object_guid, searchMention=search_mention)
    
    @async_to_sync
    async def edit_group_info(self, object_guid:str, title:Optional[str] = None, description:Optional[str] = None, slow_mode:Optional[int]=None, event_messages:Optional[bool]=None, chat_history_for_new_members:Optional[bool]=None, reaction_type:Optional[str] = None, selected_reactions:Optional[list]=None) -> dict:
        return await self.methods.editGroupInfo(objectGuid=object_guid, title=title, description=description, slowMode=slow_mode, eventMessages=event_messages, chatHistoryForNewMembers=chat_history_for_new_members, reactionType=reaction_type, selectedReactions=selected_reactions)
    
    # Channels methods
    
    @async_to_sync
    async def add_channel(self, title:str, description:Optional[str] = None, member_guids:Optional[list]=None, private:bool=False) -> dict:
        return await self.methods.addChannel(title=title, description=description, memberGuids=member_guids, private=private)

    @async_to_sync
    async def edit_channel_info(self, object_guid:str, title:Optional[str] = None, description:Optional[str] = None, username:Optional[str] = None, private:Optional[bool]=None, sign_message:Optional[bool]=None, reaction_type:Optional[str] = None, selected_reactions:Optional[list]=None) -> dict:
        return await self.methods.editChannelInfo(objectGuid=object_guid, title=title, description=description, username=username, private=private, signMessages=sign_message, reactionType=reaction_type, selectedReactions=selected_reactions)
    
    @async_to_sync
    async def check_channel_username(self, username:str) -> dict:
        return await self.methods.checkChannelUsername(username=username)
    
    @async_to_sync
    async def get_channel_seen_count(self, object_guid:str, min_id:str, max_id:str) -> dict:
        return await self.methods.getChannelSeenCount(objectGuid=object_guid, minId=min_id, maxId=max_id)
    
    # Message methods
    
    @async_to_sync
    async def send_text(self, object_guid:str, text:str, message_id:Optional[str] = None) -> dict:
        return await self.methods.sendText(objectGuid=object_guid, text=text, messageId=message_id)
    
    @async_to_sync
    async def send_message(
        self,
        object_guid: str,
        text: str,
        message_id: Optional[str] = None,
        # file
        file: Optional[str] = None,
        file_name: Optional[str] = None,
        type_file: Literal["Image", "Video", "Gif", "VideoMessage","Music", "Voice","File"] = "File",
        is_spoil: bool = False,
        custom_thumb_inline: Optional[str] = None,
        time: Optional[int] = None,
        performer: Optional[str] = None,
        # poll
        question: Optional[str] = None,
        options: Optional[list] = None,
        type_poll: Literal["Regular", "Quiz"] = "Regular",
        is_anonymous: bool = True,
        correct_option_index: Optional[int] = None,
        allows_multiple_answers: bool = False,
        hint: Optional[str] = None,
        # location
        latitude: Optional[int] = None,
        longitude: Optional[int] = None,
        # contact
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        user_guid: Optional[str] = None
    ) -> Optional[dict]:
        return await self.methods.sendMessage(
            objectGuid=object_guid,
            text=text,
            mesageId=message_id,
            file=file,
            fileName=file_name,
            typeFile=type_file,
            isSpoil=is_spoil,
            customThumbInline=custom_thumb_inline,
            time=time,
            performer=performer,
            question=question,
            options=options,
            typePoll=type_poll,
            isAnonymous=is_anonymous,
            correctOptionIndex=correct_option_index,
            allowsMultipleAnswers=allows_multiple_answers,
            hint=hint,
            latitude=latitude,
            longitude=longitude,
            firstName=first_name,
            lastName=last_name,
            phoneNumber=phone_number,
            userGuid=user_guid
        )
    
    @async_to_sync
    async def send_file(self, object_guid:str, file:str, message_id:Optional[str] = None, text:Optional[str] = None, file_name:Optional[str] = None) -> Optional[dict]:
        return await self.methods.sendFile(objectGuid=object_guid, file=file, text=text, messageId=message_id, fileName=file_name)
    
    @async_to_sync
    async def send_image(self, object_guid:str, file:str, message_id:Optional[str] = None, text:Optional[str] = None, is_spoil:bool=False, thumbnail:Optional[str] = None, file_name:Optional[str] = None) -> Optional[dict]:
        return await self.methods.sendImage(objectGuid=object_guid, file=file, text=text, messageId=message_id, isSpoil=is_spoil, thumbInline=thumbnail, fileName=file_name)
    
    @async_to_sync
    async def send_video(self, object_guid:str, file:str, message_id:Optional[str] = None, text:Optional[str] = None, is_spoil:bool=False, thumbnail:Optional[str] = None, file_name:Optional[str] = None) -> Optional[dict]:
        return await self.methods.sendVideo(objectGuid=object_guid, file=file, text=text, messageId=message_id, isSpoil=is_spoil, thumbInline=thumbnail, fileName=file_name)
    
    @async_to_sync
    async def send_video_message(self, object_guid:str, file:str, message_id:Optional[str] = None, text:Optional[str] = None, thumbnail:Optional[str] = None, file_name:Optional[str] = None) -> Optional[dict]:
        return await self.methods.sendVideoMessage(objectGuid=object_guid, file=file, text=text, messageId=message_id, thumbInline=thumbnail, fileName=file_name)
    
    @async_to_sync
    async def send_gif(self, object_guid:str, file:str, message_id:Optional[str] = None, text:Optional[str] = None, thumbnail:Optional[str] = None, file_name:Optional[str] = None) -> Optional[dict]:
        return await self.methods.sendGif(objectGuid=object_guid, file=file, text=text, messageId=message_id, thumbInline=thumbnail, fileName=file_name)
    
    @async_to_sync
    async def send_music(self, object_guid:str, file:str, message_id:Optional[str] = None, text:Optional[str] = None, file_name:Optional[str] = None, performer:Optional[str] = None) -> Optional[dict]:
        return await self.methods.sendMusic(objectGuid=object_guid, file=file, text=text, messageId=message_id, fileName=file_name, performer=performer)
    
    @async_to_sync
    async def send_voice(self, object_guid:str, file:str, message_id:Optional[str] = None, text:Optional[str] = None, file_name:Optional[str] = None, time:int=0) -> Optional[dict]:
        return await self.methods.sendVoice(objectGuid=object_guid, file=file, text=text, messageId=message_id, fileName=file_name, time=time)
    
    @async_to_sync
    async def send_location(self, object_guid:str, latitude:int, longitude:int, message_id:Optional[str] = None) -> dict:
        return await self.methods.sendLocation(objectGuid=object_guid, latitude=latitude, longitude=longitude, messageId=message_id)
    
    @async_to_sync
    async def send_message_api_call(self, objectGuid:str, text:str, message_id:str, button_id:str) -> dict:
        return await self.methods.sendMessageAPICall(objectGuid=objectGuid, text=text, messageId=message_id, buttonId=button_id)
    
    @async_to_sync
    async def reaction_message(self, object_guid: str, message_id: str, reaction: Union[int,str]) -> dict:
        return await self.methods.actionOnMessageReaction(objectGuid=object_guid, messageId=message_id, reactionId=reaction, action="Add")
    
    @async_to_sync
    async def unreaction_message(self, object_guid: str, message_id: str, reaction: Union[int,str]) -> dict:
        return await self.methods.actionOnMessageReaction(objectGuid=object_guid, messageId=message_id, reactionId=reaction, action="Remove")
    
    @async_to_sync
    async def pin_message(self, object_guid:str, message_id:str) -> dict:
        return await self.methods.setPinMessage(objectGuid=object_guid, messageId=message_id, action="Pin")
    
    @async_to_sync
    async def unpin_message(self, object_guid:str, message_id:str) -> dict:
        return await self.methods.setPinMessage(objectGuid=object_guid, messageId=message_id, action="Unpin")
    
    @async_to_sync
    async def resend_message(self, object_guid:Optional[str] = None, message_id:Optional[str] = None, to_object_guid:Optional[str] = None, reply_to_message_id:Optional[str] = None, text:Optional[str] = None, file_inline:Optional[dict]=None) -> dict:
        return await self.methods.resendMessage(objectGuid=object_guid, messageId=message_id, toObjectGuid=to_object_guid, replyToMessageId=reply_to_message_id, text=text, fileInline=file_inline)
    
    @async_to_sync
    async def forward_messages(self, object_guid:str, message_ids:list, to_object_guid:str) -> dict:
        return await self.methods.forwardMessages(objectGuid=object_guid, messageIds=message_ids, toObjectGuid=to_object_guid)
    
    @async_to_sync
    async def edit_message(self, object_guid, text, message_id=None) -> dict:
        return await self.methods.editMessage(object_guid, text=text, messageId=message_id)
    
    @async_to_sync
    async def delete_messages(self, object_guid:str, message_ids:list, delete_for_all:bool=True) -> dict:
        return await self.methods.deleteMessages(objectGuid=object_guid, messageIds=message_ids, deleteForAll=delete_for_all)

    @async_to_sync
    async def auto_delete(self, object_guid: str, message_id: str, time: int, delete_for_all: bool = True):
        return await self.methods.autoDelete(objectGuid=object_guid,messageId=message_id,time=time,deleteForAll=delete_for_all)
    
    @async_to_sync
    async def seen_messages(self, object_guid:str, min_id:str, max_id:str) -> dict:
        return await self.methods.seenChatMessages(objectGuid=object_guid, minId=min_id, maxId=max_id)
    
    @async_to_sync
    async def get_messages_interval(self, object_guid:str, middle_message_id:str) -> dict:
        return await self.methods.getMessagesInterval(objectGuid=object_guid, middleMessageId=middle_message_id)
    
    @async_to_sync
    async def get_messages(self, object_guid:str, max_message_id:Optional[str] = None, filter_type:Optional[str] = None, limit:int=50) -> dict:
        return await self.methods.getMessages(objectGuid=object_guid, maxId=max_message_id, filterType=filter_type, limit=limit)
    
    @async_to_sync
    async def get_last_message(self, object_guid:str) -> dict:
        return (await self.methods.getChatInfo(objectGuid=object_guid))["chat"]["last_message"]
    
    @async_to_sync
    async def get_last_message_id(self, object_guid:str) -> str:
        return (await self.methods.getChatInfo(objectGuid=object_guid))["chat"]["last_message_id"]
    
    @async_to_sync
    async def get_messages_updates(self, object_guid:str) -> dict:
        return await self.methods.getMessagesUpdates(objectGuid=object_guid)
    
    @async_to_sync
    async def get_messages_by_id(self, object_guid:str, message_ids:list) -> dict:
        return await self.methods.getMessagesById(objectGuid=object_guid, messageIds=message_ids)
    
    @async_to_sync
    async def get_message_share_url(self, object_guid:str, message_id:str) -> dict:
        return await self.methods.getMessageShareUrl(objectGuid=object_guid, messageId=message_id)
    
    @async_to_sync
    async def click_message_url(self, object_guid:str, message_id:str, link_url:str) -> dict:
        return await self.methods.clickMessageUrl(objectGuid=object_guid, messageId=message_id, linkUrl=link_url)
    
    @async_to_sync
    async def request_send_file(self, file_name:str, mime:str, size:int) -> dict:
        return await self.methods.requestSendFile(fileName=file_name, mime=mime, size=size)
    
    # Contact methods

    @async_to_sync
    async def send_contact(self, object_guid:str, first_name:str, last_name:str, phone_number:str, user_guid:str, message_id:Optional[str] = None) -> dict:
        return await self.methods.sendContact(objectGuid=object_guid, firstName=first_name, lastName=last_name, phoneNumber=phone_number, userGuid=user_guid, messageId=message_id)
    
    @async_to_sync
    async def get_contacts(self, start_id:Optional[str] = None) -> dict:
        return await self.methods.getContacts(startId=start_id)
    
    @async_to_sync
    async def get_contacts_last_online(self, user_guids:list) -> dict:
        return await self.methods.getContactsLastOnline(userGuids=user_guids)
    
    @async_to_sync
    async def add_address_book(self, phone:str, first_name:str, last_name:str) -> dict:
        return await self.methods.addAddressBook(phone=phone, firstName=first_name, lastName=last_name)
    
    @async_to_sync
    async def delete_contact(self, object_guid:str) -> dict:
        return await self.methods.deleteContact(objectGuid=object_guid)
    
    @async_to_sync
    async def get_contacts_updates(self) -> dict:
        return await self.methods.getContactsUpdates()
    
    # Sticker methods

    @async_to_sync
    async def send_sticker(self, object_guid:str, emoji:Optional[str] = None, message_id:Optional[str] = None, sticker_data:Optional[str]=None) -> dict:
        return await self.methods.sendSticker(objectGuid=object_guid, emoji=emoji, messageId=message_id, stickerData=sticker_data)
    
    @async_to_sync
    async def get_my_sticker_sets(self) -> dict:
        return await self.methods.getMyStickerSets()
    
    @async_to_sync
    async def get_trend_sticker_sets(self, start_id:Optional[str] = None) -> dict:
        return await self.methods.getTrendStickerSets(startId=start_id)
    
    @async_to_sync
    async def search_stickers(self, search_text:str, start_id:Optional[str] = None) -> dict:
        return await self.methods.searchStickers(searchText=search_text, startId=start_id)
    
    @async_to_sync
    async def add_sticker(self, sticker_set_id:str) -> dict:
        return await self.methods.actionOnStickerSet(stickerSetId=sticker_set_id, action="Add")
    
    @async_to_sync
    async def remove_sticker(self, sticker_set_id:str) -> dict:
        return await self.methods.actionOnStickerSet(stickerSetId=sticker_set_id, action="Remove")
    
    @async_to_sync
    async def get_stickers_by_emoji(self, emoji:str) -> dict:
        return await self.methods.getStickersByEmoji(emoji=emoji)
    
    @async_to_sync
    async def get_stickers_by_set_ids(self, sticker_set_ids:list) -> dict:
        return await self.methods.getStickersBySetIDs(stickerSetIds=sticker_set_ids)
    
    # Gif methods

    @async_to_sync
    async def get_my_gif_set(self) -> dict:
        return await self.methods.getMyGifSet()
    
    @async_to_sync
    async def add_gif(self, object_guid:str, message_id:str) -> dict:
        return await self.methods.addToMyGifSet(objectGuid=object_guid, messageId=message_id)
    
    @async_to_sync
    async def remove_gif(self, file_id:str) -> dict:
        return await self.methods.removeFromMyGifSet(fileId=file_id)
    
    # Poll methods

    @async_to_sync
    async def send_poll(
        self,
        object_guid: str,
        question: str,
        options: list,
        allows_multiple_responses: bool = True,
        is_anonymous: bool = False,
        type: Literal["Quiz", "Regular"] = "Regular",
        message_id: Optional[str] = None,
        correct_option_index: Optional[int] = None,
        hint: Optional[str] = None
    ) -> dict:
        return await self.methods.sendPoll(objectGuid=object_guid, question=question, options=options,allowsMultipleResponses=allows_multiple_responses,isAnonymous=is_anonymous,type=type, messageId=message_id,hint=hint,correctOptionIndex=correct_option_index)
    
    @async_to_sync
    async def vote_poll(self, poll_id:str, selection_index:int) -> dict:
        return await self.methods.votePoll(pollId=poll_id, selectionIndex=selection_index)
    
    @async_to_sync
    async def get_poll_status(self, poll_id:str) -> dict:
        return await self.methods.getPollStatus(pollId=poll_id)
    
    @async_to_sync
    async def get_poll_option_voters(self, poll_id:str, selection_index:int, start_id:Optional[str] = None) -> dict:
        return await self.methods.getPollOptionVoters(pollId=poll_id, selectionIndex=selection_index, startId=start_id)
    
    # Live methods
    
    @async_to_sync
    async def send_live(self, object_guid:str, thumb_inline:str) -> dict:
        return await self.methods.sendLive(objectGuid=object_guid, thumbInline=thumb_inline)
    
    @async_to_sync
    async def add_live_comment(self, access_token:str, live_id:str, text:str) -> dict:
        return await self.methods.addLiveComment(accessToken=access_token, liveId=live_id, text=text)
    
    @async_to_sync
    async def get_live_status(self, access_token:str, live_id:str) -> dict:
        return await self.methods.getLiveStatus(accessToken=access_token, liveId=live_id)
    
    @async_to_sync
    async def getLiveComments(self, access_token:str, live_id:str) -> dict:
        return await self.methods.getLiveComments(accessToken=access_token, liveId=live_id)
    
    @async_to_sync
    async def getLivePlayUrl(self, access_token:str, live_id:str) -> dict:
        return await self.methods.getLivePlayUrl(accessToken=access_token, liveId=live_id)
    
    # Call methods

    @async_to_sync
    async def requestCall(self, object_guid:str, call_type:str) -> dict:
        return await self.methods.requestCall(objectGuid=object_guid, callType=call_type)
    
    @async_to_sync
    async def discard_call(self, call_id:str, duration:int, reason:str) -> dict:
        return await self.methods.discardCall(callId=call_id, duration=duration, reason=reason)
    
    # Setting methods
    
    @async_to_sync
    async def set_setting(self, show_my_last_online:Optional[bool]=None, show_my_phone_number:Optional[bool]=None, show_my_profile_photo:Optional[bool]=None, link_forward_message:Optional[bool]=None, can_join_chat_by:Optional[bool]=None) -> dict:
        return await self.methods.setSetting(showMyLastOnline=show_my_last_online, showMyPhoneNumber=show_my_phone_number, showMyProfilePhoto=show_my_profile_photo, linkForwardMessage=link_forward_message, canJoinChatBy=can_join_chat_by)
    
    @async_to_sync
    async def add_folder(self, folder_name:str, folder_id:str, exclude_chat_ids:list, exclude_chat_types:list, include_chat_ids:list, include_chat_types:list) -> dict:
        return await self.methods.addFolder(folderName=folder_name, folderId=folder_id, excludeChatIds=exclude_chat_ids, excludeChatTypes=exclude_chat_types, includeChatIds=include_chat_ids, includeChatTypes=include_chat_types)
    
    @async_to_sync
    async def get_folders(self, last_state:Optional[str] = None) -> dict:
        return await self.methods.getFolders(lastState=last_state)
    
    @async_to_sync
    async def get_suggested_folders(self) -> dict:
        return await self.methods.getSuggestedFolders()
    
    @async_to_sync
    async def delete_folder(self, folder_id:str) -> dict:
        return await self.methods.deleteFolder(folderId=folder_id)
    
    @async_to_sync
    async def update_profile(self, first_name:Optional[str] = None, last_name:Optional[str] = None, bio:Optional[str] = None, username:Optional[str] = None) -> dict:
        return await self.methods.updateProfile(firstName=first_name, lastname=last_name, bio=bio, username=username)
    
    @async_to_sync
    async def get_my_sessions(self) -> dict:
        return await self.methods.getMySessions()
    
    @async_to_sync
    async def terminate_session(self, session_key:str) -> dict:
        return await self.methods.terminateSession(sessionKey=session_key)
    
    @async_to_sync
    async def terminate_other_sessions(self) -> dict:
        return await self.methods.terminateOtherSessions()
    
    @async_to_sync
    async def check_two_step_passcode(self, password:str) -> dict:
        return await self.methods.checkTwoStepPasscode(password=password)
    
    @async_to_sync
    async def setup_two_step_verification(self, password:str, hint:str, recovery_email:str) -> dict:
        return await self.methods.setupTwoStepVerification(password=password, hint=hint, recoveryEmail=recovery_email)
    
    @async_to_sync
    async def request_recovery_email(self, password:str, recovery_email:str) -> dict:
        return await self.methods.requestRecoveryEmail(password=password, recoveryEmail=recovery_email)
    
    @async_to_sync
    async def verify_recovery_email(self, password:str, code:str) -> dict:
        return await self.methods.verifyRecoveryEmail(password=password, code=code)
    
    @async_to_sync
    async def turn_off_two_step(self, password:str) -> dict:
        return await self.methods.turnOffTwoStep(password=password)
    
    @async_to_sync
    async def change_password(self, password:str, new_password:str, new_hint:str) -> dict:
        return await self.methods.changePassword(password=password, newPassword=new_password, newHint=new_hint)
    
    @async_to_sync
    async def get_two_passcode_status(self) -> dict:
        return await self.methods.getTwoPasscodeStatus()
    
    @async_to_sync
    async def get_privacy_setting(self) -> dict:
        return await self.methods.getPrivacySetting()
    
    @async_to_sync
    async def get_blocked_users(self, start_id:Optional[str] = None) -> dict:
        return await self.methods.getBlockedUsers(startId=start_id)
    
    # Other methods

    @async_to_sync
    async def get_me(self) -> dict:
        return await self.methods.getMe()
    
    @async_to_sync
    async def transcribe_voice(self, object_guid:str, message_id:str) -> dict:
        return await self.methods.transcribeVoice(objectGuid=object_guid, messageId=message_id)
    
    @async_to_sync
    async def reset_contacts(self) -> dict:
        return await self.methods.resetContacts()
    
    @async_to_sync
    async def get_time(self) -> dict:
        return await self.methods.getTime()
    
    @async_to_sync
    async def get_abs_objects(self, object_guids:list) -> dict:
        return await self.methods.getAbsObjects(objectGuids=object_guids)
    
    @async_to_sync
    async def get_link_from_app_url(self, url:str) -> dict:
        return await self.methods.getLinkFromAppUrl(url=url)
    
    @async_to_sync
    async def search_global_objects(self, search_text:str, filters:Optional[list]=None) -> dict:
        return await self.methods.searchGlobalObjects(searchText=search_text, filters=filters)
    
    @async_to_sync
    async def search_global_messages(self, search_text:str) -> dict:
        return await self.methods.searchGlobalMessages(searchText=search_text)
    
    @async_to_sync
    async def check_join(self, object_guid:str, user_guid:str) -> Optional[bool]:
        return await self.methods.checkJoin(objectGuid=object_guid, userGuid=user_guid)
    
    @async_to_sync
    async def get_profile_link_items(self, object_guid:str) -> dict:
        return await self.methods.getProfileLinkItems(objectGuid=object_guid)
    
    @async_to_sync
    async def get_download_link(self, object_guid: str, message_id:Optional[str] = None, file_inline:Optional[dict]=None) -> Optional[str]:
        return await self.methods.getDownloadLink(objectGuid=object_guid, messageId=message_id, fileInline=file_inline)
    
    @async_to_sync
    async def download(self, object_guid: str, message_id:Optional[str] = None, save:bool=False, save_as:Optional[str] = None, file_inline:Optional[dict]=None) -> Optional[dict]:
        return await self.methods.download(objectGuid=object_guid, messageId=message_id, save=save, saveAs=save_as, fileInline=file_inline)
    
    @async_to_sync
    async def request(
        self,
        method: str,
        input: dict = {},
        tmp_session: bool = False,
        attempt: int = 0,
        max_attempt: int = 2
    ) -> dict:
        return await self.methods.request(method=method,input=input,tmpSession=tmp_session,attempt=attempt,maxAttempt=max_attempt)

    @async_to_sync
    async def play_voice(self, object_guid: str, file: str) -> None:
        await self.methods.playVoice(objectGuid=object_guid, file=file)
    
    def on_message(self, filters: Union[List[Filter], List[str], Filter, None] = None):
        def handler(func):
            self.methods.add_handler(
                func=func,
                filters=filters
            )
        return handler
    
    def run(self) -> None:
        self.methods.run()