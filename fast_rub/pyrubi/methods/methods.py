from random import randint
from ..network import (
    Network,
    Socket
)
from ..crypto import Cryption
from ..utils import Utils
from random import choice
from time import sleep
from ..exceptions import (
    InvalidAuth,
    InvalidInput
)
import asyncio
from typing import (
    Optional,
    Union,
    Literal
)
from ...core.async_sync import *
from typing import Optional, Union, List
from ..filters import Filter

class Methods:
    def __init__(self, sessionData:dict, platform:str, apiVersion:int, proxy:Optional[str], timeOut:int, showProgressBar:bool) -> None:
        self.platform = platform.lower()
        if not self.platform in ["android", "web", "rubx", "rubikax", "rubino"]:
            print("The \"{}\" is not a valid platform. Choose these one -> (web, android, rubx)".format(platform))
            exit()
        self.apiVersion = apiVersion
        self.proxy = proxy
        self.timeOut = timeOut
        self.showProgressBar = showProgressBar
        self.sessionData = sessionData
        self.crypto = Cryption(
            auth=sessionData["auth"],
            private_key=sessionData["private_key"]
        ) if sessionData else Cryption(auth=Utils.randomTmpSession())
        self.network = Network(methods=self)
        self.socket = Socket(methods=self)

    # Authentication methods

    @async_to_sync
    async def sendCode(self, phoneNumber: str, passKey: Optional[str] = None, sendInternal: bool = False) -> dict:
        input:dict = {
            "phone_number": f"{phoneNumber}",
            "send_type": "Internal" if sendInternal else "SMS",
        }

        if passKey:
            input["pass_key"] = passKey

        return await self.network.request(
            method="sendCode",
            input=input,
            tmpSession=True
        )
    
    @async_to_sync
    async def signIn(self, phoneNumber, phoneCodeHash, phoneCode) -> dict:
        publicKey, privateKey = self.crypto.rsaKeyGenrate()

        data = await self.network.request(
            method="signIn",
            input={
                "phone_number": f"98{Utils.phoneNumberParse(phoneNumber)}",
                "phone_code_hash": phoneCodeHash,
                "phone_code": phoneCode,
			    "public_key": publicKey
            },
            tmpSession=True
        )
        
        data["private_key"] = privateKey

        return data

    @async_to_sync
    async def registerDevice(self, deviceModel) -> dict:
        return await self.network.request(
            method="registerDevice",
            input={
                "app_version": "WB_4.3.3" if self.platform == "web" else "MA_3.4.3",
                "device_hash": Utils.randomDeviceHash(),
                "device_model": deviceModel,
                "is_multi_account": False,
                "lang_code": "fa",
                "system_version": "Windows 11" if self.platform == "web" else "SDK 28",
                "token": "",
                "token_type": "Web" if self.platform == "web" else "Firebase"
            }
        )

    @async_to_sync
    async def logout(self) -> dict:
        return await self.network.request(method="logout")
    
    # Chats methods
    
    @async_to_sync
    async def getChats(self, startId:Optional[str]) -> dict:
        return await self.network.request(method="getChats", input={"start_id": startId})
    
    @async_to_sync
    async def getObjectByUsername(self, username: str) -> dict:
        return await self.network.request(method="getObjectByUsername",input={'username': username.replace("@","")})
    
    @async_to_sync
    async def getTopChatUsers(self) -> dict:
        return await self.network.request(method="getTopChatUsers")
    
    @async_to_sync
    async def removeFromTopChatUsers(self, objectGuid:str) -> dict:
        return await self.network.request(method="removeFromTopChatUsers", input={"user_guid": objectGuid})
    
    @async_to_sync
    async def getChatAds(self) -> dict:
        return await self.network.request(method="getChatAds", input={"state": Utils.getState()})

    @async_to_sync
    async def getChatsUpdates(self) -> dict:
        return await self.network.request(method="getChatsUpdates", input={"state": Utils.getState()})
    
    @async_to_sync
    async def joinChat(self, guidOrLink:str) -> dict:
        if Utils.checkLink(guidOrLink):
            method:str = "joinGroup" if Utils.getChatTypeByLink(link=guidOrLink) == "Group" else "joinChannelByLink"
        else:
            method:str = "joinChannelAction"

        return await self.network.request(
            method=method,
            input={"hash_link": guidOrLink.split("/")[-1]} if Utils.checkLink(guidOrLink) else {
                "channel_guid": guidOrLink,
                "action": "Join"
            }
        )

    @async_to_sync
    async def actionOnJoinRequest(self,objectGuid: str, userGuid: str, action: Literal["Accept", "Reject"]):
        object_type = Utils.getChatTypeByGuid(objectGuid)
        return await self.network.request(
            method="actionOnJoinRequest",
            input={
                "object_guid": objectGuid,
                "object_type": object_type,
                "user_guid": userGuid,
                "action": action
            }
        )

    @async_to_sync
    async def getJoinRequests(self, objectGuid: str):
        return await self.network.request(
            method="getJoinRequests",
            input={
                "object_guid": objectGuid
            }
        )
    
    @async_to_sync
    async def leaveChat(self, objectGuid:str) -> dict:
        input:dict = {f"{Utils.getChatTypeByGuid(objectGuid=objectGuid).lower()}_guid": objectGuid}

        if Utils.getChatTypeByGuid(objectGuid=objectGuid) == "Group": method:str = "leaveGroup"
        else:
            method:str = "joinChannelAction"
            input["action"] = "Leave"

        return await self.network.request(
            method=method,
            input=input
        )
    
    @async_to_sync
    async def removeChat(self, objectGuid:str) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        return await self.network.request(
            method=f"remove{chatType}",
            input={f"{chatType.lower()}_guid": objectGuid}
        )
    
    @async_to_sync
    async def getChatInfo(self, objectGuid:str) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        return await self.network.request(
            method=f"get{chatType}Info",
            input={f"{chatType.lower()}_guid": objectGuid}
        )
    
    @async_to_sync
    async def getChatInfoByUsername(self, username:str) -> dict:
        return await self.network.request(method="getObjectInfoByUsername", input={"username": username.replace("@", "")})
    
    @async_to_sync
    async def getChatLink(self, objectGuid:str) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        return await self.network.request(
            method=f"get{chatType}Link",
            input={f"{chatType.lower()}_guid": objectGuid}
        )
    
    @async_to_sync
    async def setChatLink(self, objectGuid:str) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        return await self.network.request(
            method=f"set{chatType}Link",
            input={f"{chatType.lower()}_guid": objectGuid}
        )
    
    @async_to_sync
    async def setChatAdmin(self, objectGuid:str, memberGuid:str, accessList:Optional[list], customTitle:Optional[str], action:str) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        input:dict = {
            f"{chatType.lower()}_guid": objectGuid,
            "member_guid": memberGuid,
            "action": action,
            "access_list": accessList or []
        }

        if customTitle: input["custom_title"] = customTitle

        return await self.network.request(
            method=f"set{chatType}Admin",
            input=input
        )
    
    @async_to_sync
    async def addChatMember(self, objectGuid:str, memberGuids:list) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        return await self.network.request(
            method=f"add{chatType}Members",
            input={
                f"{chatType.lower()}_guid": objectGuid,
                "member_guids": memberGuids
            }
        )
    
    @async_to_sync
    async def banChatMember(self, objectGuid:str, memberGuid:str, action:str) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        return await self.network.request(
            method=f"ban{chatType}Member",
            input={
                f"{chatType.lower()}_guid": objectGuid,
                "member_guid": memberGuid,
                "action": action
            }
        )
    
    @async_to_sync
    async def getBannedChatMembers(self, objectGuid:str, startId:Optional[str]) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        return await self.network.request(
            method=f"getBanned{chatType}Members",
            input={
                f"{chatType.lower()}_guid": objectGuid,
                "start_id": startId
            }
        )
    
    @async_to_sync
    async def getChatAllMembers(self, objectGuid:str, searchText:Optional[str], startId:Optional[str], justGetGuids:bool=False) -> Union[dict,list]:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        data = await self.network.request(
            method=f"get{chatType}AllMembers",
            input={
                f"{chatType.lower()}_guid": objectGuid,
                "search_text": searchText.replace("@", "") if searchText else searchText,
                "start_id": startId
            }
        )

        if justGetGuids: return [i["member_guid"] for i in data["in_chat_members"]]

        return data
    
    @async_to_sync
    async def getChatAdminMembers(self, objectGuid:str, startId:Optional[str], justGetGuids: bool = False) -> Union[dict,list]:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        data = await self.network.request(
            method=f"get{chatType}AdminMembers",
            input={
                f"{chatType.lower()}_guid": objectGuid,
                "start_id": startId
            }
        )
    
        if justGetGuids: return [i["member_guid"] for i in data["in_chat_members"]]

        return data

    @async_to_sync
    async def userIsAdmin(self, objectGuid: str, userGuid: str):
        nextStartId = None
        hasContinue = True
        while hasContinue:
            result = await self.getChatAdminMembers(objectGuid, nextStartId)
            if type(result) is dict: # for typing error
                hasContinue = result["has_continue"]
                nextStartId = result["next_start_id"]
                for user in result["in_chat_members"]:
                    if userGuid == user.member_guid:
                        return True
        return False
    
    @async_to_sync
    async def getChatAdminAccessList(self, objectGuid:str, memberGuid:str) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        return await self.network.request(
            method=f"get{chatType}AdminAccessList",
            input={
                f"{chatType.lower()}_guid": objectGuid,
                "member_guid": memberGuid
            }
        )
    
    @async_to_sync
    async def chatPreviewByJoinLink(self, link:str) -> dict:
        return await self.network.request(
            method="groupPreviewByJoinLink" if "joing" in link else "channelPreviewByJoinLink",
            input={"hash_link": link.split("/")[-1]}
        )
    
    @async_to_sync
    async def createChatVoiceChat(self, objectGuid:str) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        return await self.network.request(
            method=f"create{chatType}VoiceChat",
            input={f"{chatType.lower()}_guid": objectGuid}
        )
    
    @async_to_sync
    async def joinVoiceChat(self, objectGuid:str, myGuid:str, voiceChatId:str, sdp_offer_data:str) -> dict:
        return await self.network.request(
            method=f"join{Utils.getChatTypeByGuid(objectGuid=objectGuid)}VoiceChat",
            input={
                "chat_guid": objectGuid,
                "voice_chat_id": voiceChatId,
                "sdp_offer_data": sdp_offer_data,
                "self_object_guid": myGuid
            }
        )

    @async_to_sync
    async def setChatVoiceChatSetting(self, objectGuid:str, voideChatId:str, title:Optional[str], joinMuted:Optional[bool]) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        input:dict = {
            f"{chatType.lower()}_guid": objectGuid,
            "voice_chat_id": voideChatId,
            "updated_parameters": []
        }

        if title:
            input["title"] = title
            input["updated_parameters"].append("title")
        
        if joinMuted:
            input["join_muted"] = joinMuted
            input["updated_parameters"].append("join_muted")

        return await self.network.request(
            method=f"set{chatType}VoiceChatSetting",
            input=input
        )
    
    @async_to_sync
    async def getChatVoiceChatUpdates(self, objectGuid:str, voideChatId:str) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        return await self.network.request(
            method=f"get{chatType}VoiceChatUpdates",
            input={
                f"{chatType.lower()}_guid": objectGuid,
                "voice_chat_id": voideChatId,
                "state": Utils.getState()
            }
        )
    
    @async_to_sync
    async def getChatVoiceChatParticipants(self, objectGuid:str, voideChatId:str) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        return await self.network.request(
            method=f"get{chatType}VoiceChatParticipants",
            input={
                f"{chatType.lower()}_guid": objectGuid,
                "voice_chat_id": voideChatId,
            }
        )
    
    @async_to_sync
    async def setChatVoiceChatState(self, objectGuid:str, voideChatId:str, activity:str, participantObjectGuid:str) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        return await self.network.request(
            method=f"set{chatType}VoiceChatState",
            input={
                "chat_guid": objectGuid,
                "voice_chat_id": voideChatId,
                "action": activity,
                "participant_object_guid": participantObjectGuid
            }
        )
    
    @async_to_sync
    async def sendChatVoiceChatActivity(self, objectGuid:str, voideChatId:str, activity:str, participantObjectGuid:str) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        return await self.network.request(
            method=f"send{chatType}VoiceChatActivity",
            input={
                "chat_guid": objectGuid,
                "voice_chat_id": voideChatId,
                "activity": activity,
                "participant_object_guid": participantObjectGuid
            }
        )
    
    @async_to_sync
    async def leaveChatVoiceChat(self, objectGuid:str, voideChatId:str) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        return await self.network.request(
            method=f"leave{chatType}VoiceChat",
            input={
                f"{chatType.lower()}_guid": objectGuid,
                "voice_chat_id": voideChatId
            }
        )
    
    @async_to_sync
    async def discardChatVoiceChat(self, objectGuid:str, voideChatId:str) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        return await self.network.request(
            method=f"discard{chatType}VoiceChat",
            input={
                f"{chatType.lower()}_guid": objectGuid,
                "voice_chat_id": voideChatId
            }
        )
    
    @async_to_sync
    async def setActionChat(self, objectGuid:str, action:str) -> dict:
        return await self.network.request(
            method="setActionChat",
            input={
                "object_guid": objectGuid,
                "action": action
            }
        )
    
    @async_to_sync
    async def seenChats(self, seenList:dict) -> dict:
        return await self.network.request(method="seenChats", input={"seen_list": seenList})
    
    @async_to_sync
    async def seenChatMessages(self, objectGuid:str, minId:str, maxId:str) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        return await self.network.request(
            method=f"seen{chatType}Messages",
            input={
                f"{chatType.lower()}_guid": objectGuid,
                "min_id": minId,
                "max_id": maxId
            }
        )
    
    @async_to_sync
    async def sendChatActivity(self, objectGuid:str, activity:str) -> dict:
        return await self.network.request(
            method="sendChatActivity",
            input={
                "object_guid": objectGuid,
                "activity": activity
            }
        )
    
    @async_to_sync
    async def searchChatMessages(self, objectGuid:str, searchText:str) -> dict:
        return await self.network.request(
            method="searchChatMessages",
            input={
                "object_guid": objectGuid,
                "search_text": searchText,
                "type": "Hashtag" if searchText.startswith("#") else "Text"
            }
        )
    
    @async_to_sync
    async def uploadAvatar(self, objectGuid:str, mainFile:str, thumbnailFile:Optional[str]) -> Optional[dict]:
        uploadMainFileData = await self.network.upload(file=mainFile)

        if uploadMainFileData is not None and thumbnailFile is not None:
            uplo_ = await self.network.upload(file=thumbnailFile)
            if isinstance(uplo_,dict):
                return await self.network.request(
                    method="uploadAvatar",
                    input={
                        "object_guid": objectGuid,
                        "thumbnail_file_id": uplo_["id"] if thumbnailFile else uploadMainFileData["id"],
                        "main_file_id": uploadMainFileData["id"]
                    }
                )
        raise ValueError("Error ! Value invalid")
    
    @async_to_sync
    async def getAvatars(self, objectGuid:str) -> dict:
        return await self.network.request(method="getAvatars", input={"object_guid": objectGuid})
    
    @async_to_sync
    async def deleteAvatar(self, objectGuid:str, avatarId:str) -> dict:
        return await self.network.request(
            method="deleteAvatar",
            input={
                "object_guid": objectGuid,
                "avatar_id": avatarId
            }
        )
    
    @async_to_sync
    async def deleteChatHistory(self, objectGuid:str, lastMessageId:str) -> dict:
        return await self.network.request(
            method="deleteChatHistory",
            input={
                "object_guid": objectGuid,
                "last_message_id": lastMessageId
            }
        )
    
    @async_to_sync
    async def deleteUserChat(self, userGuid:str, lastDeletedMessageId) -> dict:
        return await self.network.request(
            method="deleteUserChat",
            input={
                "user_guid": userGuid,
                "last_deleted_message_id": lastDeletedMessageId
            }
        )
    
    @async_to_sync
    async def getPendingObjectOwner(self, objectGuid:str) -> dict:
        return await self.network.request(method="getPendingObjectOwner", input={"object_guid": objectGuid})
    
    @async_to_sync
    async def requestChangeObjectOwner(self, objectGuid:str, memberGuid:str) -> dict:
        return await self.network.request(
            method="requestChangeObjectOwner",
            input={
                "new_owner_user_guid": memberGuid,
                "object_guid": objectGuid
            }
        )
    
    @async_to_sync
    async def replyRequestObjectOwner(self, objectGuid:str, action:str) -> dict:
        return await self.network.request(
            method="replyRequestObjectOwner",
            input={
                "action": action, #Accept Reject
                "object_guid": objectGuid
            }
        )
    
    @async_to_sync
    async def cancelChangeObjectOwner(self, objectGuid:str) -> dict:
        return await self.network.request(method="cancelChangeObjectOwner", input={"object_guid": objectGuid})
    
    @async_to_sync
    async def getChatReaction(self, objectGuid:str, minId:str, maxId:str) -> dict:
        return await self.network.request(
            method="getChatReaction",
            input={
                f"object_guid": objectGuid,
                "min_id": minId,
                "max_id": maxId
            }
        )
    
    @async_to_sync
    async def reportObject(self, objectGuid:str, description:str) -> dict:
        return await self.network.request(
            method="reportObject",
            input={
                "object_guid": objectGuid,
                "report_description": description,
                "report_type": 100,
                "report_type_object": "Object"
            }
        )
    
    @async_to_sync
    async def setChatUseTime(self, objectGuid:str, time:int) -> dict:
        return await self.network.request(
            method="setChatUseTime",
            input={
                "object_guid": objectGuid,
                "time": time
            }
        )
    
    # User methods

    @async_to_sync
    async def setBlockUser(self, objectGuid:str, action:str) -> dict:
        return await self.network.request(
            method="setBlockUser",
            input={
                "user_guid": objectGuid,
                "action": action
            }
        )
    
    @async_to_sync
    async def checkUserUsername(self, username:str) -> dict:
        return await self.network.request(
            method="checkUserUsername",
            input={
                "username": username,
            }
        )
    
    # Group methods

    @async_to_sync
    async def addGroup(self, title:str, memberGuids:list) -> dict:
        return await self.network.request(
            method="addGroup",
            input={
                "title": title,
                "member_guids": memberGuids
            }
        )
    
    @async_to_sync
    async def getGroupDefaultAccess(self, objectGuid:str) -> dict:
        return await self.network.request(
            method=f"getGroupDefaultAccess",
            input={"group_guid": objectGuid}
        )
    
    @async_to_sync
    async def setChatDefaultAccess(self, objectGuid:str, accessList:list) -> dict:
        chatType:str = Utils.getChatTypeByGuid(objectGuid=objectGuid)

        return await self.network.request(
            method=f"setGroupDefaultAccess",
            input={
                f"group_guid": objectGuid,
                "access_list": accessList
            }
        )
    
    @async_to_sync
    async def getGroupMentionList(self, objectGuid:str, searchMention:str) -> dict:
        return await self.network.request(
            method="getGroupMentionList",
            input={
                "group_guid": objectGuid,
                "search_mention": searchMention
            }
        )
    
    @async_to_sync
    async def editGroupInfo(
            self,
            objectGuid:str,
            title:Optional[str],
            description:Optional[str],
            slowMode:Optional[int],
            eventMessages:Optional[bool],
            chatHistoryForNewMembers:Optional[bool],
            reactionType:Optional[str], #Selected Disabled All
            selectedReactions:Optional[list[str]]
        ) -> dict:

        input:dict = {
            "group_guid": objectGuid,
            "updated_parameters": []
        }

        if title:
            input["title"] = title
            input["updated_parameters"].append("title")

        if description:
            input["description"] = description
            input["updated_parameters"].append("description")

        if slowMode:
            input["slow_mode"] = slowMode
            input["updated_parameters"].append("slow_mode")

        if not eventMessages is None:
            input["event_messages"] = eventMessages
            input["updated_parameters"].append("event_messages")

        if not chatHistoryForNewMembers is None:
            input["chat_history_for_new_members"] = "Visible" if chatHistoryForNewMembers else "Hidden"
            input["updated_parameters"].append("chat_history_for_new_members")

        if reactionType:
            if selectedReactions:
                input["chat_reaction_setting"] = {"reaction_type": reactionType,"selected_reactions":selectedReactions}
            else:
                input["chat_reaction_setting"] = {"reaction_type": reactionType}
            input["updated_parameters"].append("chat_reaction_setting")


        return await self.network.request(
            method="editGroupInfo",
            input=input
        )
    
    # Channel methods

    @async_to_sync
    async def addChannel(self, title:str, description:Optional[str], memberGuids:Optional[list], private:bool) -> dict:
        input:dict = {
            "title": title,
            "description": description,
            "member_guids": memberGuids or [],
            "channel_type": "Private" if private else "Public"
        }
        
        return await self.network.request(
            method="addChannel",
            input=input
        )
    
    @async_to_sync
    async def editChannelInfo(
            self,
            objectGuid:str,
            title:Optional[str],
            description:Optional[str],
            username:Optional[str],
            private:Optional[bool],
            signMessages:Optional[bool],
            reactionType:Optional[str], #Selected Disabled All
            selectedReactions:Optional[list]
        ) -> dict:

        input:dict = {
            "channel_guid": objectGuid,
            "updated_parameters": []
        }

        if selectedReactions: input["chat_reaction_setting"]["selected_reactions"] = selectedReactions

        if title:
            input["title"] = title
            input["updated_parameters"].append("title")

        if description:
            input["description"] = description
            input["updated_parameters"].append("description")

        if not private is None:
            input["channel_type"] = "Private" if private else "Public"
            input["updated_parameters"].append("channel_type")

        if not signMessages is None: 
            input["sign_messages"] = signMessages
            input["updated_parameters"].append("sign_messages")
        
        if reactionType:
            if selectedReactions:
                input["chat_reaction_setting"] = {"reaction_type": reactionType,"selected_reactions":selectedReactions}
            else:
                input["chat_reaction_setting"] = {"reaction_type": reactionType}
            input["updated_parameters"].append("chat_reaction_setting")

        if username:
            await self.updateChannelUsername(
                objectGuid=objectGuid,
                username=username
            )

        return await self.network.request(
            method="editChannelInfo",
            input=input
        )
    
    @async_to_sync
    async def checkChannelUsername(self, username:str) -> dict:
        return await self.network.request(
            method="checkChannelUsername",
            input={
                "username": username,
            }
        )
    
    @async_to_sync
    async def updateChannelUsername(self, objectGuid:str, username:str) -> dict:
        return await self.network.request(
            method="updateChannelUsername",
            input={
                "channel_guid": objectGuid,
                "username": username
            }
        )
    
    @async_to_sync
    async def getChannelSeenCount(self, objectGuid:str, minId:str, maxId:str) -> dict:
        return await self.network.request(
            method="getChannelSeenCount",
            input={
                "channel_guid": objectGuid,
                "min_id": minId,
                "max_id": maxId
            }
        )
    
    # Message methods
    @async_to_sync
    async def sendText(self, objectGuid:str, text:str, messageId:Optional[str]) -> dict:
        metadata = Utils.checkMetadata(text)

        input = {
            "object_guid": objectGuid,
            "rnd": str(randint(10000000, 999999999)),
            "text": metadata[1],
            "reply_to_message_id": messageId,
        }

        if metadata[0] != []: input["metadata"] = {"meta_data_parts": metadata[0]}

        return await self.network.request(method="sendMessage", input=input)

    
    
    @async_to_sync
    async def sendMessage(
        self,
        objectGuid: str,
        text: Optional[str] = None,
        mesageId: Optional[str] = None,
        # file
        file: Optional[str] = None,
        fileName: Optional[str] = None,
        typeFile: Literal["Image", "Video", "Gif", "VideoMessage","Music", "Voice","File"] = "File",
        isSpoil: bool = False,
        customThumbInline: Optional[str] = None,
        time: Optional[int] = None,
        performer: Optional[str] = None,
        # poll
        question: Optional[str] = None,
        options: Optional[list] = None,
        typePoll: Literal["Regular", "Quiz"] = "Regular",
        isAnonymous: bool = True,
        correctOptionIndex: Optional[int] = None,
        allowsMultipleAnswers: bool = False,
        hint: Optional[str] = None,
        # location
        latitude: Optional[int] = None,
        longitude: Optional[int] = None,
        # contact
        firstName: Optional[str] = None,
        lastName: Optional[str] = None,
        phoneNumber: Optional[str] = None,
        userGuid: Optional[str] = None
    ) -> Optional[dict]:
        if file:
            return await self.baseSendFileInline(
                objectGuid=objectGuid,
                file=file,
                text=text,
                messageId=mesageId,
                fileName=fileName,
                type=typeFile,
                isSpoil=isSpoil,
                customThumbInline=customThumbInline,
                time=time,
                performer=performer
            )
        elif (not question is None) and (not options is None):
            return await self.sendPoll(
                objectGuid=objectGuid,
                question=question,
                options=options,
                allowsMultipleResponses=allowsMultipleAnswers,
                isAnonymous=isAnonymous,
                type=typePoll,
                messageId=mesageId,
                correctOptionIndex=correctOptionIndex,
                hint=hint
            )
        elif (not latitude is None) and (not longitude is None):
            return await self.sendLocation(
                objectGuid=objectGuid,
                latitude=latitude,
                longitude=longitude,
                messageId=mesageId
            )
        elif firstName and lastName and phoneNumber and userGuid:
            return await self.sendContact(
                objectGuid=objectGuid,
                firstName=firstName,
                lastName=lastName,
                phoneNumber=phoneNumber,
                messageId=mesageId,
                userGuid=userGuid
            )
        elif not text is None:
            return await self.sendText(
                objectGuid=objectGuid,
                text=text,
                messageId=mesageId
            )
        raise ValueError("Please Write The Args !")
    
    @async_to_sync
    async def baseSendFileInline(
        self,
        objectGuid: str,
        file: str,
        text: Optional[str] = None,
        messageId: Optional[str] = None,
        fileName: Optional[str] = None,
        type: Literal["Image", "Video", "Gif", "VideoMessage","Music", "Voice","File"] = "File",
        isSpoil: bool = False,
        customThumbInline: Optional[str] = None,
        time: Optional[int] = None,
        performer: Optional[str] = None
    ) -> Optional[dict]:
        upload_data = await self.network.upload(file=file, fileName=fileName)
        if isinstance(upload_data,dict):
            uploadData:dict = dict(upload_data)
            if not uploadData:
                return
            
            input:dict = {
                "file_inline": {
                    "dc_id": uploadData["dc_id"],
                    "file_id": uploadData["id"],
                    "file_name": uploadData["file_name"],
                    "size": uploadData["size"],
                    "mime": uploadData["mime"],
                    "access_hash_rec": uploadData["access_hash_rec"],
                    "type": type,
                    "is_spoil": isSpoil
                },
                "object_guid": objectGuid,
                "rnd": Utils.randomRnd(),
                "reply_to_message_id": messageId
            }

            if type in ["Image", "Video", "Gif", "VideoMessage"]:
                customThumbInline = Utils.getImageThumbnail(
                    customThumbInline
                    if isinstance(customThumbInline, bytes)
                    else (await self.network.httpx_client.request("GET", customThumbInline)).content
                    if Utils.checkLink(customThumbInline)
                    else open(customThumbInline, "rb").read()
                ) if customThumbInline else None

                videoData=[]
                if not type == "Image":
                    videoData:list = list(Utils.getVideoData(uploadData["file"]))
                    input["file_inline"]["time"] = videoData[2] * 1000

                fileSize:list = list(Utils.getImageSize(uploadData["file"])) if type == "Image" else videoData[1]
                input["file_inline"]["width"] = fileSize[0]
                input["file_inline"]["height"] = fileSize[1]

                if type == "VideoMessage":
                    input["file_inline"]["type"] = "Video"
                    input["file_inline"]["is_round"] = True

                input["file_inline"]["thumb_inline"] = customThumbInline or (Utils.getImageThumbnail(uploadData["file"]) if type == "Image" else videoData[0])

            if type in ["Music", "Voice"]:
                input["file_inline"]["time"] = (time or Utils.getVoiceDuration(uploadData["file"])) * (1000 if type == "Voice" else 1)

                if type == "Music":
                    input["file_inline"]["music_performer"] = performer or Utils.getMusicArtist(uploadData["file"])

            metadata:list = list(Utils.checkMetadata(text))
            if metadata[1]: input["text"] = metadata[1]
            if metadata[0]: input["metadata"] = {"meta_data_parts": metadata[0]}

            return await self.network.request(
                method="sendMessage",
                input=input
            )

    
    @async_to_sync
    async def sendFile(self, objectGuid:str, file:str, messageId:Optional[str], text:Optional[str], fileName:Optional[str] = None) -> Optional[dict]:
        if fileName is None:
            fileName = Utils.format_file("File")
        return await self.baseSendFileInline(
            objectGuid=objectGuid,
            file=file,
            text=text,
            messageId=messageId,
            fileName=fileName,
            type="File"
        )
    
    @async_to_sync
    async def sendImage(self, objectGuid:str, file:str, messageId:Optional[str], text:Optional[str], isSpoil:bool, thumbInline:Optional[str], fileName:Optional[str] = None) -> Optional[dict]:
        if fileName is None:
            fileName = Utils.format_file("Image")
        return await self.baseSendFileInline(
            objectGuid=objectGuid,
            file=file,
            text=text,
            messageId=messageId,
            fileName=fileName,
            type="Image",
            isSpoil=isSpoil,
            customThumbInline=thumbInline
        )
    
    @async_to_sync
    async def sendVideo(self, objectGuid:str, file:str, messageId:Optional[str], text:Optional[str], isSpoil:bool, thumbInline:Optional[str], fileName:Optional[str] = None) -> Optional[dict]:
        if fileName is None:
            fileName = Utils.format_file("Video")
        return await self.baseSendFileInline(
            objectGuid=objectGuid,
            file=file,
            text=text,
            messageId=messageId,
            fileName=fileName,
            type="Video",
            isSpoil=isSpoil,
            customThumbInline=thumbInline
        )
    
    @async_to_sync
    async def sendVideoMessage(self, objectGuid:str, file:str, messageId:Optional[str], text:Optional[str], thumbInline:Optional[str], fileName:Optional[str] = None) -> Optional[dict]:
        if fileName is None:
            fileName = Utils.format_file("Video")
        return await self.baseSendFileInline(
            objectGuid=objectGuid,
            file=file,
            text=text,
            messageId=messageId,
            fileName=fileName,
            type="VideoMessage",
            customThumbInline=thumbInline
        )
    
    @async_to_sync
    async def sendGif(self, objectGuid:str, file:str, messageId:Optional[str], text:Optional[str], thumbInline:Optional[str], fileName:Optional[str] = None) -> Optional[dict]:
        if fileName is None:
            fileName = Utils.format_file("Gif")
        return await self.baseSendFileInline(
            objectGuid=objectGuid,
            file=file,
            text=text,
            messageId=messageId,
            fileName=fileName,
            type="Gif",
            customThumbInline=thumbInline
        )
    
    @async_to_sync
    async def sendMusic(self, objectGuid:str, file:str, messageId:Optional[str], text:Optional[str], performer:Optional[str], fileName:Optional[str] = None) -> Optional[dict]:
        if fileName is None:
            fileName = Utils.format_file("Music")
        return await self.baseSendFileInline(
            objectGuid=objectGuid,
            file=file,
            text=text,
            messageId=messageId,
            fileName=fileName,
            type="Music",
            performer=performer
        )
    
    @async_to_sync
    async def sendVoice(self, objectGuid:str, file:str, time:int, messageId:Optional[str] = None, text:Optional[str] = None, fileName:Optional[str] = None) -> Optional[dict]:
        if fileName is None:
            fileName = Utils.format_file("Voice")
        return await self.baseSendFileInline(
            objectGuid=objectGuid,
            file=file,
            text=text,
            messageId=messageId,
            fileName=fileName,
            type="Voice",
            time=time
        )
    
    @async_to_sync
    async def sendLocation(self, objectGuid:str, latitude:int, longitude:int, messageId:Optional[str]) -> dict:
        return await self.network.request(
            method="sendMessage",
            input={
                "location": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "object_guid":objectGuid,
                "rnd": Utils.randomRnd(),
                "reply_to_message_id": messageId
            }
        )
    
    @async_to_sync
    async def sendMessageAPICall(self, objectGuid:str, text:str, messageId:str, buttonId:str) -> dict:
        return await self.network.request(
            method="sendMessageAPICall",
            input={
                "text": text,
                "object_guid": objectGuid,
                "message_id": messageId,
                "aux_data": {"button_id": buttonId}
            }
        )
    
    @async_to_sync
    async def editMessage(self, objectGuid, text, messageId) -> dict:
        metadata = Utils.checkMetadata(text)
        data = {
            "object_guid": objectGuid,
            "text": metadata[1],
            "message_id": messageId,
        }
        if metadata[0] != []:
            data["metadata"] = {"meta_data_parts": metadata[0]}
        return await self.network.request("editMessage", data)
    
    @async_to_sync
    async def actionOnMessageReaction(self, objectGuid:str, messageId:str, reactionId:Union[int,str], action:str) -> dict:
        if type(reactionId) is str:
            reactionId = Utils.reaction_to_id(reactionId)
        return await self.network.request(
            method="actionOnMessageReaction",
            input={
                "action": action, #Add OR Remove
                "object_guid": objectGuid,
                "message_id": messageId,
                "reaction_id": reactionId
            }
        )

    @async_to_sync
    async def setPinMessage(self, objectGuid:str, messageId:str, action:str) -> dict:
        return await self.network.request(
            method="setPinMessage",
            input={
                "object_guid": objectGuid,
                "message_id": messageId,
                "action": action
            }
        )

    @async_to_sync
    async def resendMessage(self, objectGuid: Optional[str] = None, messageId: Optional[str] = None, toObjectGuid:Optional[str] = None, replyToMessageId:Optional[str] = None, text:Optional[str] = None, fileInline: Optional[dict] = None) -> dict:
        messageData = {}
        if not fileInline:
            if objectGuid:
                messageData:dict = await self.getMessagesById(objectGuid=objectGuid, messageIds=[messageId])
            else:
                raise ValueError("You Shoud Write The 'fileInline' or (objectGuid, messageId) Args")
        
        if not text and not messageData:
            raise ValueError("You Shoud Write The 'text' or (objectGuid, messageId) Args")
        text_: str = text or messageData["messages"][0]["text"]
        metadata = Utils.checkMetadata(text_)
        input = {
            "is_mute": False,
            "object_guid": toObjectGuid,
            "rnd": Utils.randomRnd(),
            "reply_to_message_id": replyToMessageId,
            "text": metadata[1]
        }

        fileInline_:dict = fileInline or messageData["messages"][0]["file_inline"]
        if fileInline_:
            input["file_inline"] = fileInline_

        if not fileInline_:
            location:dict = messageData["messages"][0].get("location")
            if location:
                input["location"] = location
                del input["location"]["map_view"]
                del input["text"]

            contact:dict = messageData["messages"][0].get("message_contact")
            if contact:
                input["message_contact"] = contact
                del input["text"]

            sticker:dict = messageData["messages"][0].get("sticker")
            if sticker:
                input["sticker"] = sticker
                del input["text"]

            if messageData["messages"][0].get("metadata"):
                input["metadata"] = {"meta_data_parts": messageData["messages"][0]["metadata"]}
                
        elif metadata[0] != []:
            input["metadata"] = {"meta_data_parts": metadata[0]}

        return await self.network.request(method="sendMessage", input=input)

    @async_to_sync
    async def forwardMessages(self, objectGuid:str, messageIds:list, toObjectGuid:str) -> dict:
        return await self.network.request(
            method="forwardMessages",
            input={
                "from_object_guid": objectGuid,
                "message_ids": messageIds,
                "to_object_guid": toObjectGuid,
                "rnd": Utils.randomRnd(),
            }
        )
    
    @async_to_sync
    async def deleteMessages(self, objectGuid:str, messageIds:list, deleteForAll: bool = True) -> dict:
        return await self.network.request(
            method="deleteMessages",
            input={
                "object_guid": objectGuid,
                "message_ids": messageIds,
                "type": "Global" if deleteForAll else "Local"
            }
        )

    @async_to_sync
    async def autoDelete(self, objectGuid: str, messageId: str, time: int, deleteForAll: bool = True):
        await asyncio.sleep(time)
        return await self.deleteMessages(
            objectGuid=objectGuid,
            messageIds=[messageId],
            deleteForAll=deleteForAll
        )
    
    @async_to_sync
    async def getMessagesInterval(self, objectGuid:str, middleMessageId:str) -> dict:
        return await self.network.request(
            method="getMessagesInterval",
            input={
                "object_guid": objectGuid,
                "middle_message_id": middleMessageId
            }
        )
    
    @async_to_sync
    async def getMessages(self, objectGuid:str, maxId:Optional[str], filterType:Optional[str], limit:int) -> dict:
        input:dict = {
            "object_guid": objectGuid,
            "sort": "FromMax",
            "max_id": maxId,
            "limit": limit
        }
        
        if filterType: input["filter_type"] = filterType

        return await self.network.request(
            method="getMessages",
            input=input
        )
    
    @async_to_sync
    async def getMessagesUpdates(self, objectGuid:str) -> dict:
        return await self.network.request(
            method="getMessagesUpdates",
            input={
                "object_guid": objectGuid,
                "state": Utils.getState(),
            }
        )
    
    @async_to_sync
    async def getMessagesById(self, objectGuid: str, messageIds: Union[list, str]) -> dict:
        if type(messageIds) is str:
            messageIds = [messageIds]
        return await self.network.request(
            method="getMessagesByID",
            input={
                "object_guid": objectGuid,
                "message_ids": messageIds,
            }
        )
    
    @async_to_sync
    async def getMessageShareUrl(self, objectGuid:str, messageId:str) -> dict:
        return await self.network.request(
            method="getMessageShareUrl",
            input={
                "object_guid": objectGuid,
                "message_id": messageId,
            }
        )
    
    @async_to_sync
    async def clickMessageUrl(self, objectGuid:str, messageId:str, linkUrl:str) -> dict:
        return await self.network.request(
            method="clickMessageUrl",
            input={
                "object_guid": objectGuid,
                "message_id": messageId,
                "link_url": linkUrl
            }
        )
    
    @async_to_sync
    async def searchGlobalMessages(self, searchText:str) -> dict:
        return await self.network.request(
            method="search_text",
            input={
                "search_text": searchText,
                "type": "Text",
            }
        )
    
    @async_to_sync
    async def requestSendFile(self, fileName:str, mime:str, size:int) -> dict:
        return await self.network.request(
            method="requestSendFile",
            input={
                "file_name": fileName,
                "mime": mime,
                "size": str(size)
            }
        )
    
    # Contact methods
    
    @async_to_sync
    async def sendContact(self, objectGuid:str, firstName:str, lastName:str, phoneNumber:str, userGuid:str, messageId:Optional[str]) -> dict:
        return await self.network.request(
            method="sendMessage",
            input={
                "message_contact":{
                    "first_name": firstName,
                    "last_name": lastName or "",
                    "phone_number": phoneNumber,
                    "user_guid": userGuid
                },
                "object_guid":objectGuid,
                "rnd": Utils.randomRnd(),
                "reply_to_message_id": messageId
            }
        )

    @async_to_sync
    async def getContacts(self, startId:Optional[str]) -> dict:
        return await self.network.request(method="getContacts", input={"start_id": startId})
    
    @async_to_sync
    async def getContactsLastOnline(self, userGuids:list) -> dict:
        return await self.network.request(method="getContactsLastOnline", input={"user_guids": userGuids})

    @async_to_sync
    async def addAddressBook(self, phone:str, firstName:str, lastName:str) -> dict:
        return await self.network.request(
            method="addAddressBook",
            input={
                "phone": f"98{Utils.phoneNumberParse(phone)}",
                "first_name": firstName,
                "last_name": lastName
            }
        )
    
    @async_to_sync
    async def deleteContact(self, objectGuid:str) -> dict:
        return await self.network.request(method="deleteContact", input={"user_guid": objectGuid})
    
    @async_to_sync
    async def getContactsUpdates(self) -> dict:
        return await self.network.request(method="getContactsUpdates", input={"state": Utils.getState()})
    
    # Sticker methods

    @async_to_sync
    async def sendSticker(self, objectGuid:str, emoji:Optional[str], messageId:Optional[str], stickerData:Optional[str]) -> dict:
        data = {
            "sticker": (stickerData or choice((await self.getStickersByEmoji(emoji))["stickers"])) if emoji else None,
            "object_guid": objectGuid,
            "rnd": Utils.randomRnd(),
            "reply_to_message_id": messageId,
        }
        
        return await self.network.request("sendMessage", data)

    @async_to_sync
    async def getMyStickerSets(self) -> dict:
        return await self.network.request(method="getMyStickerSets")
    
    @async_to_sync
    async def getTrendStickerSets(self, startId:Optional[str]) -> dict:
        return await self.network.request(method="getTrendStickerSets", input={"start_id": startId})
    
    @async_to_sync
    async def searchStickers(self, searchText:str, startId:Optional[str]) -> dict:
        return await self.network.request(
            method="searchStickers",
            input={
                "search_text": searchText,
                "start_id": startId
            }
        )
    
    @async_to_sync
    async def actionOnStickerSet(self, stickerSetId:str, action:str) -> dict:
        return await self.network.request(
            method="actionOnStickerSet",
            input={
                "sticker_set_id": stickerSetId,
                "action": action
            }
        )
    
    @async_to_sync
    async def getStickersByEmoji(self, emoji:str) -> dict:
        return await self.network.request(
            method="getStickersByEmoji",
            input={
                "emoji_character": emoji,
                "suggest_by": "All"
            }
        )
    
    @async_to_sync
    async def getStickersBySetIDs(self, stickerSetIds:list) -> dict:
        return await self.network.request(method="getStickersBySetIDs", input={"sticker_set_ids": stickerSetIds})
    
    # Gif methods

    @async_to_sync
    async def getMyGifSet(self) -> dict:
        return await self.network.request(method="getMyGifSet")

    @async_to_sync
    async def addToMyGifSet(self, objectGuid:str, messageId:str) -> dict:
        return await self.network.request(
            method="addToMyGifSet",
            input={
                "message_id": messageId,
                "object_guid": objectGuid
            }
        )
    
    @async_to_sync
    async def removeFromMyGifSet(self, fileId:str) -> dict:
        return await self.network.request(method="removeFromMyGifSet", input={"file_id": fileId})
    
    # Poll methods

    @async_to_sync
    async def sendPoll(
        self,
        objectGuid: str,
        question: str,
        options: list,
        allowsMultipleResponses: bool = True,
        isAnonymous: bool = False,
        type: Literal["Quiz", "Regular"] = "Regular",
        messageId: Optional[str] = None,
        correctOptionIndex: Optional[int] = None,
        hint: Optional[str] = None
    ) -> dict:
        if not type in ['Quiz', 'Regular']:
            raise ValueError('type poll invalid ! type shoud is "Quiz" or "Regular".')
        if len(options) > 2:
            raise IndexError("Len for options is low ! Minimum for options is 2.")
        data = {
            'object_guid': objectGuid,
            'question': question,
            'options': options,
            'allows_multiple_answers': allowsMultipleResponses,
            'is_anonymous': isAnonymous,
            'reply_to_message_id': messageId,
            'type': type,
            'rnd': Utils.randomRnd(),
        }
        if type == 'Quiz':
            data['correct_option_index'] = correctOptionIndex
            data['explanation'] =  hint
        return await self.network.request(
            method="createPoll",
            input=data
        )
    
    @async_to_sync
    async def votePoll(self, pollId:str, selectionIndex:int) -> dict:
        return await self.network.request(
            method="votePoll",
            input={
                "poll_id": pollId,
                "selection_index": selectionIndex
            }
        )
    
    @async_to_sync
    async def getPollStatus(self, pollId:str) -> dict:
        return await self.network.request(method="getPollStatus", input={"poll_id": pollId})
    
    @async_to_sync
    async def getPollOptionVoters(self, pollId:str, selectionIndex:int, startId:Optional[str] = None) -> dict:
        return await self.network.request(
            method="getPollOptionVoters",
            input={
                "poll_id": pollId,
                "selection_index": selectionIndex,
                "start_id": startId
            }
        )
    
    # Live methods

    @async_to_sync
    async def sendLive(self, objectGuid:str, thumbInline:Union[bytes,str]) -> dict:
        if isinstance(thumbInline,bytes):
            by = thumbInline
        elif isinstance(thumbInline,str):
            if Utils.checkLink(thumbInline):
                by = (await self.network.httpx_client.request("GET", thumbInline)).content
                if not isinstance(by, bytes):
                    raise ValueError("Error !")
            else:
                with open(thumbInline,"rb") as file:
                    by = file.read()
        else:
            raise ValueError("thumbInline is byte or str !")
        return await self.network.request(
            method="sendLive",
            input={
                "thumb_inline": Utils.getImageThumbnail(by),
                "device_type": "Software",
                "object_guid": objectGuid,
                "rnd": Utils.randomRnd()
            }
        )
    
    @async_to_sync
    async def addLiveComment(self, accessToken:str, liveId:str, text:str) -> dict:
        return await self.network.request(
            method="addLiveComment",
            input={
                "access_token": accessToken,
                "live_id": liveId,
                "text": text
            }
        )
    
    @async_to_sync
    async def getLiveStatus(self, accessToken:str, liveId:str) -> dict:
        return await self.network.request(
            method="getLiveStatus",
            input={
                "access_token": accessToken,
                "live_id": liveId,
                "type": "LiveViewer"
            }
        )
    
    @async_to_sync
    async def getLiveComments(self, accessToken:str, liveId:str) -> dict:
        return await self.network.request(
            method="getLiveComments",
            input={
                "access_token": accessToken,
                "live_id": liveId,
            }
        )
    
    @async_to_sync
    async def getLivePlayUrl(self, accessToken:str, liveId:str) -> dict:
        return await self.network.request(
            method="getLivePlayUrl",
            input={
                "access_token": accessToken,
                "live_id": liveId
            }
        )
    
    # Call methods

    @async_to_sync
    async def requestCall(self, objectGuid:str, callType:str) -> dict:
        return await self.network.request(
            method="requestCall",
            input={
                "call_type": callType,
                "library_versions": ["2.7.7","2.4.4"],
                "max_layer": 92,
                "min_layer": 65,
                "sip_version": 1,
                "support_call_out": True,
                "user_guid": objectGuid
            }
        )
    
    @async_to_sync
    async def discardCall(self, callId:str, duration:int, reason:str) -> dict:
        return await self.network.request(
            method="discardCall",
            input={
                "call_id": callId,
                "duration": duration,
                "reason": reason #Missed OR Disconnect
            }
        )
    
    # Setting methods

    @async_to_sync
    async def setSetting(
            self,
            showMyLastOnline:Optional[bool],
            showMyPhoneNumber:Optional[bool],
            showMyProfilePhoto:Optional[bool],
            linkForwardMessage:Optional[bool],
            canJoinChatBy:Optional[bool]
        ) -> dict:

        input:dict = {
            "settings": {},
            "update_parameters": []
        }

        if not showMyLastOnline is None:
            input["settings"]["show_my_last_online"] = "Everybody" if showMyLastOnline else "Nobody"
            input["update_parameters"].append("show_my_last_online")

        if not showMyPhoneNumber is None:
            input["settings"]["show_my_phone_number"] = "Everybody" if showMyPhoneNumber else "Nobody"
            input["update_parameters"].append("show_my_phone_number")

        if not showMyProfilePhoto is None:
            input["settings"]["show_my_profile_photo"] = "Everybody" if showMyProfilePhoto else "MyContacts"
            input["update_parameters"].append("show_my_profile_photo")

        if not linkForwardMessage is None:
            input["settings"]["link_forward_message"] = "Everybody" if linkForwardMessage else "Nobody"
            input["update_parameters"].append("link_forward_message")

        if not canJoinChatBy is None:
            input["settings"]["can_join_chat_by"] = "Everybody" if canJoinChatBy else "MyContacts"
            input["update_parameters"].append("can_join_chat_by")

        return await self.network.request(
            method="setSetting",
            input=input
        )
    
    @async_to_sync
    async def addFolder(
            self,
            folderName:str,
            folderId:str,
            excludeChatIds:list,
            excludeChatTypes:list,
            includeChatIds:list,
            includeChatTypes:list
        ) -> dict:

        return await self.network.request(
            method="addFolder",
            input={
                "exclude_object_guids": excludeChatIds,
                "include_object_guids": excludeChatTypes,
                "exclude_chat_types": includeChatIds,
                "include_chat_types": includeChatTypes,
                "folder_id": folderId,
                "is_add_to_top": True,
                "name": folderName
            }
        )
    
    @async_to_sync
    async def getFolders(self, lastState:Optional[str]) -> dict:
        return await self.network.request(method="getFolders", input={"last_state": lastState})
    
    @async_to_sync
    async def getSuggestedFolders(self) -> dict:
        return await self.network.request(method="getSuggestedFolders")
    
    @async_to_sync
    async def deleteFolder(self, folderId:str) -> dict:
        return await self.network.request(method="deleteFolder", input={"folder_id": folderId})
    
    @async_to_sync
    async def updateProfile(self, firstName:Optional[str], lastname:Optional[str], bio:Optional[str], username:Optional[str]) -> dict:
        input:dict = {
            "first_name": firstName,
            "last_name": lastname,
            "bio": bio,
            "updated_parameters": []
        }

        if firstName:input["updated_parameters"].append("first_name")
        if lastname: input["updated_parameters"].append("last_name")
        if bio: input["updated_parameters"].append("bio")

        if username:
            response:dict = await self.network.request(method="updateUsername", input={"username": username})
            if not input["updated_parameters"]:
                return response

        return await self.network.request(
            method="updateProfile",
            input=input
        )
    
    @async_to_sync
    async def getMySessions(self) -> dict:
        return await self.network.request(method="getMySessions")
    
    @async_to_sync
    async def terminateSession(self, sessionKey:str) -> dict:
        return await self.network.request(method="terminateSession", input={"session_key": sessionKey})
    
    @async_to_sync
    async def terminateOtherSessions(self):
            return await self.network.request("terminateOtherSessions")
    
    @async_to_sync
    async def checkTwoStepPasscode(self, password:str) -> dict:
        return await self.network.request(method="checkTwoStepPasscode", input={"password": password})
    
    @async_to_sync
    async def setupTwoStepVerification(self, password:str, hint:str, recoveryEmail:str) -> dict:
        return await self.network.request(
            method="setupTwoStepVerification",
            input={
                "password": password,
                "hint": hint,
                "recovery_email": recoveryEmail
            }
        )
    
    @async_to_sync
    async def requestRecoveryEmail(self, password:str, recoveryEmail:str) -> dict:
        return await self.network.request(
            method="requestRecoveryEmail",
            input={
                "password": password,
                "recovery_email": recoveryEmail
            }
        )
    
    @async_to_sync
    async def verifyRecoveryEmail(self, password:str, code:str) -> dict:
        return await self.network.request(
            method="verifyRecoveryEmail",
            input={
                "password": password,
                "code": code
            }
        )
    
    @async_to_sync
    async def turnOffTwoStep(self, password:str) -> dict:
        return await self.network.request(method="turnOffTwoStep", input={"password": password})
    
    @async_to_sync
    async def changePassword(self, password:str, newPassword:str, newHint:str) -> dict:
        return await self.network.request(
            method="changePassword",
            input={
                "password": password,
                "new_password": newPassword,
                "new_hint": newHint
            }
        )
    
    @async_to_sync
    async def getTwoPasscodeStatus(self) -> dict:
        return await self.network.request(method="getTwoPasscodeStatus")
    
    @async_to_sync
    async def getPrivacySetting(self) -> dict:
        return await self.network.request(method="getPrivacySetting")
    
    @async_to_sync
    async def getBlockedUsers(self, startId:Optional[str]) -> dict:
        return await self.network.request(method="getBlockedUsers", input={"start_id": startId})
    
    # Other methods

    @async_to_sync
    async def getMe(self) -> dict:
        data:dict = await self.network.request(method="getUserInfo")
        data.update(self.sessionData)
        return data
    
    @async_to_sync
    async def transcribeVoice(self, objectGuid:str, messageId:str) -> dict:
        response = await self.network.request(
            method="transcribeVoice",
            input={
                "object_guid": objectGuid,
                "message_id": messageId
            }
        )
        
        if response["status"] != "OK":
            return response
        
        while True:
            sleep(0.5)
            result = await self.network.request(
                method="getTranscription",
                input={
                    "message_id": messageId,
                    "transcription_id": response["transcription_id"]
                }
            )
            
            if result["status"] != "OK":
                continue

            return result
    
    @async_to_sync
    async def resetContacts(self) -> dict:
        return await self.network.request("resetContacts")
    
    @async_to_sync
    async def getTime(self) -> dict:
        return await self.network.request("getTime")

    @async_to_sync
    async def getAbsObjects(self, objectGuids:list) -> dict:
        return await self.network.request(method="getAbsObjects", input={"object_guids": objectGuids})
    
    @async_to_sync
    async def getLinkFromAppUrl(self, url:str) -> dict:
        return await self.network.request(method="getLinkFromAppUrl", input={"app_url": url})
    
    @async_to_sync
    async def searchGlobalObjects(self, searchText:str, filters:Optional[list]) -> dict:
        input:dict = {"search_text": searchText}
        if filters: input["filter_types"] = filters

        return await self.network.request(method="searchGlobalObjects", input=input)
    
    @async_to_sync
    async def checkJoin(self, objectGuid:str, userGuid:str) -> Optional[bool]:
        userUsername: str = (await self.getChatInfo(userGuid))["user"].get("username")

        if userGuid in (await self.getChatAllMembers(objectGuid=objectGuid, searchText=userUsername, startId=None, justGetGuids=True)):
            return True
        
        if userUsername:
            return False
        
        return None
    
    @async_to_sync
    async def getProfileLinkItems(self, objectGuid:str) -> dict:
        return await self.network.request(method="getProfileLinkItems", input={"object_guid": objectGuid})
    
    @async_to_sync
    async def getDownloadLink(self, objectGuid: str, messageId:Optional[str], fileInline:Optional[dict]) -> Optional[str]:
        if not fileInline:
            msg = await self.getMessagesById(objectGuid=objectGuid, messageIds=[messageId])
            fileInline = msg["messages"][0]["file_inline"]
        if fileInline:
            return f'https://messenger{fileInline["dc_id"]}.iranlms.ir/InternFile.ashx?id={fileInline["file_id"]}&ach={fileInline["access_hash_rec"]}'
    
    @async_to_sync
    async def download(self,save:bool, objectGuid: str, messageId:Optional[str] = None, saveAs:Optional[str] = None, fileInline:Optional[dict] = None) -> Optional[dict]:
        if fileInline is None:
            msg = await self.getMessagesById(objectGuid=objectGuid, messageIds=[messageId])
            fileInline = msg["messages"][0]["file_inline"]
        if not fileInline is None:
            downloading = await self.network.download(
                accessHashRec=fileInline["access_hash_rec"],
                fileId=fileInline["file_id"],
                dcId=fileInline["dc_id"],
                size=fileInline["size"], 
                fileName=fileInline["file_name"]
            )

            if downloading:
                downloadedData:bytes = downloading

                if save or saveAs:
                    with open(saveAs or fileInline["file_name"], "wb") as file:
                        file.write(downloadedData)

                fileInline["file"] = downloadedData

                return fileInline

    @async_to_sync
    async def request(
        self,
        method: str,
        input: dict = {},
        tmpSession: bool = False,
        attempt: int = 0,
        maxAttempt: int = 2
    ) -> dict:
        return await self.network.request(method=method,input=input,tmpSession=tmpSession,attempt=attempt,maxAttempt=maxAttempt)

    @async_to_sync
    async def playVoice(self, objectGuid:str, file: str) -> None:
        try:
            from aiortc import RTCPeerConnection, RTCSessionDescription
            from aiortc.contrib.media import MediaPlayer
            voiceChatId: str = ((await self.getChatInfo(objectGuid))["chat"])["group_voice_chat_id"]

            if not voiceChatId:
                voiceChatId:str = (await self.createChatVoiceChat(objectGuid=objectGuid))["group_voice_chat_update"]["voice_chat_id"]

            rtcConnection = RTCPeerConnection()
            player: MediaPlayer = MediaPlayer(file)
            rtcConnection.addTrack(player.audio)
            spdOffer = await rtcConnection.createOffer()
            await rtcConnection.setLocalDescription(spdOffer)

            answerSdp = (await self.joinVoiceChat(
                objectGuid=objectGuid,
                myGuid=self.sessionData["user"]["user_guid"],
                voiceChatId=voiceChatId,
                sdp_offer_data=spdOffer.sdp
            ))["sdp_answer_data"]
            
            await self.setChatVoiceChatState(
                objectGuid=objectGuid,
                voideChatId=voiceChatId,
                activity="Unmute",
                participantObjectGuid=self.sessionData["user"]["user_guid"]
            )

            remoteDescription = RTCSessionDescription(answerSdp, "answer")
            await rtcConnection.setRemoteDescription(remoteDescription)

            def onEnded():
                asyncio.create_task(rtcConnection.close())

            player.audio.on("ended", onEnded)

            async def keepAlive():
                while rtcConnection.connectionState != "closed":
                    try:
                        sending_code = await self.sendChatVoiceChatActivity(
                            objectGuid=objectGuid,
                            voideChatId=voiceChatId,
                            activity="Speaking",
                            participantObjectGuid=self.sessionData["user"]["user_guid"]
                        )
                        if sending_code["status"] != "OK":
                            print({"status": sending_code["status"], "method": "sendChatVoiceChatActivity"})
                            break
                        
                        if (await self.getChatVoiceChatUpdates(
                            objectGuid=objectGuid,
                            voideChatId=voiceChatId
                        ))["status"] != "OK":
                            print({"status": sending_code["status"], "method": "getChatVoiceChatUpdates"})
                            break

                        await asyncio.sleep(8)
                    except (InvalidInput, InvalidAuth) as e:
                        print(e)
                        break
                    except Exception as e:
                        print(e)
                        continue
                
            keepalive_task = asyncio.create_task(keepAlive())

            try:
                while rtcConnection.connectionState != "closed":
                    await asyncio.sleep(1)
            finally:
                keepalive_task.cancel()
                await rtcConnection.close()

            asyncio.create_task(rtcConnection.close())

        except ImportError:
            print("The aiortc library is not installed!")

    def add_handler(self, func, filters: Union[List[Filter], List[str], Filter, None] = None) -> None:
        self.socket.addHandler(
            func=func,
            filters=filters
        )
        return func
        
    def run(self) -> None:
        self.socket.connect()