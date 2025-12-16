from random import (
    choices,
    randint
)
from time import time
from re import (
    finditer,
    sub,
    DOTALL
)
from base64 import b64encode
from io import BytesIO
from tempfile import NamedTemporaryFile
from mutagen import (
    mp3,
    File
)
from filetype import guess
from os import (
    system,
    chmod,
    remove
)
from .configs import Configs
from .reacrions import REACTION_MAP
from typing import Optional



class Utils:
    @staticmethod
    def randomTmpSession() -> str:
        return "".join(choices("abcdefghijklmnopqrstuvwxyz", k=32))

    @staticmethod
    def randomDeviceHash() -> str:
        return "".join(choices("0123456789", k=26))

    @staticmethod
    def randomRnd() -> str:
        return str(randint(-99999999, 99999999))

    @staticmethod
    def privateParse(private: str) -> Optional[str]:
        if private:
            if not private.startswith("-----BEGIN RSA PRIVATE KEY-----"):
                private = "-----BEGIN RSA PRIVATE KEY-----\n" + private

            if not private.endswith("-----END RSA PRIVATE KEY-----"):
                private += "\n-----END RSA PRIVATE KEY-----"

            return private.replace("\n", "\n").strip()

    @staticmethod
    def getState() -> int:
        return int(time()) - 150

    @staticmethod
    def phoneNumberParse(phoneNumber: str) -> str:
        if str(phoneNumber).startswith("0"):
            phoneNumber = phoneNumber[1:]
        elif str(phoneNumber).startswith("98"):
            phoneNumber = phoneNumber[2:]
        elif str(phoneNumber).startswith("+98"):
            phoneNumber = phoneNumber[3:]
        return phoneNumber

    @staticmethod
    def getChatTypeByGuid(objectGuid: str) -> str:
        for chatType in [("u0", "User"), ("g0", "Group"), ("c0", "Channel"), ("s0", "Service"), ("b0", "Bot")]:
            if objectGuid.startswith(chatType[0]):
                return chatType[1]
        return "Unknown"

    @staticmethod
    def isChatType(chatType: str) -> Optional[bool]:
        chatType = chatType.lower()
        for type in ["user", "group", "channel", "service", "bot"]:
            if type == chatType:
                return True

    @staticmethod
    def isMessageType(messageType: str) -> Optional[bool]:
        messageType = messageType.lower()
        for type in ["text", "image", "video", "gif", "video message", "voice", "music", "file"]:
            if type == messageType:
                return True
    
    @staticmethod
    def format_file(type_file: Optional[str] = None) -> Optional[str]:
        if not type_file:
            return None
        for type_,pass_ in {"File":"", "Image":".png", "Voice":".mp3", "Music":".mp3", "Gif":".mp4" , "Video":".mp4"}.items():
            if type_ == type_file:
                name_file = type_+pass_
                return name_file
        return None

    @staticmethod
    def getChatTypeByLink(link: str) -> Optional[str]:
        if "rubika.ir/joing" in link:
            return "Group"
        elif "rubika.ir/joinc" in link:
            return "Channel"

    @staticmethod
    def checkMetadata(text) -> tuple:
        if text is None:
            return [], ""

        real_text = sub(r"``|\*\*|__|~~|--|@@|##|", "", text)
        metadata = []
        conflict = 0
        mentionObjectIndex = 0
        result = []

        patterns = {
            "Mono": r"\`\`([^``]*)\`\`",
            "Bold": r"\*\*([^**]*)\*\*",
            "Italic": r"\_\_([^__]*)\_\_",
            "Strike": r"\~\~([^~~]*)\~\~",
            "Underline": r"\-\-([^__]*)\-\-",
            "Mention": r"\@\@([^@@]*)\@\@",
            "Spoiler": r"\#\#([^##]*)\#\#",
        }

        for style, pattern in patterns.items():
            for match in finditer(pattern, text):
                metadata.append((match.start(), len(match.group(1)), style))

        metadata.sort()

        for start, length, style in metadata:
            if not style == "Mention":
                result.append({
                    "type": style,
                    "from_index": start - conflict,
                    "length": length,
                })
                conflict += 4
            else:
                mentionObjects = [i.group(1) for i in finditer(r"\@\(([^(]*)\)", text)]
                mentionType = Utils.getChatTypeByGuid(objectGuid=mentionObjects[mentionObjectIndex]) or "Link"

                if mentionType == "Link":
                    result.append(
                        {
                            "from_index": start - conflict,
                            "length": length,
                            "link": {
                                "hyperlink_data": {
                                    "url": mentionObjects[mentionObjectIndex]
                                },
                                "type": "hyperlink",
                            },
                            "type": mentionType,
                        }
                    )
                else:
                    result.append(
                        {
                            "type": "MentionText",
                            "from_index": start - conflict,
                            "length": length,
                            "mention_text_object_guid": mentionObjects[mentionObjectIndex],
                            "mention_text_object_type": mentionType
                        }
                    )
                real_text = real_text.replace(f"({mentionObjects[mentionObjectIndex]})", "")
                conflict += 6 + len(mentionObjects[mentionObjectIndex])
                mentionObjectIndex += 1

        return result, real_text

    @staticmethod
    def checkMarkdown(text: str) -> tuple:
        """
        Parse basic Markdown styles and return metadata with plain text.
        Supports: **bold**, *italic*, __underline__, ~~strike~~, `mono`, ||spoiler||, [link](url)
        """
        if not text:
            return [], ""
        
        patterns = {
            "Pre": (r"```(.*?)```",),
            "Bold": (r"\*\*([^\*]+?)\*\*",),
            "Underline": (r"__([^_]+?)__",),
            "Strike": (r"~~([^~]+?)~~",),
            "Mono": (r"`([^`]+?)`",),
            "Spoiler": (r"\|\|([^|]+?)\|\|",),
            "Italic": (r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"(?<!_)_([^_\n]+?)_(?!_)"),
            "Link": (r"\[([^\]]+?)\]\(([^\)]+?)\)",),
            "Mention": (r"\@\@([^@@]+?)\@\@",),
        }
        
        all_matches = []
        mention_objects = [i.group(1) for i in finditer(r"\@\(([^(]*)\)", text)]
        mention_object_index = 0
        used_positions = set()

        for style, pattern_list in patterns.items():
            for pattern in pattern_list:
                for match in finditer(pattern, text, flags=DOTALL):
                    start, end = match.start(), match.end()
                    
                    if any(pos in used_positions for pos in range(start, end)):
                        continue
                    
                    if style == "Link":
                        link_text, link_url = match.groups()
                        all_matches.append({
                            "start": start,
                            "end": end,
                            "length": len(link_text),
                            "style": style,
                            "content": link_text,
                            "full_match": match.group(0),
                            "extra": link_url
                        })
                    elif style == "Pre":
                        content = match.group(1).strip() if match.group(1) else ""
                        all_matches.append({
                            "start": start,
                            "end": end,
                            "length": len(content),
                            "style": style,
                            "content": content,
                            "full_match": match.group(0),
                            "extra": None
                        })
                    else:
                        content = match.group(1)
                        all_matches.append({
                            "start": start,
                            "end": end,
                            "length": len(content),
                            "style": style,
                            "content": content,
                            "full_match": match.group(0),
                            "extra": None
                        })
                    
                    used_positions.update(range(start, end))
        all_matches.sort(key=lambda x: x["start"])
        metadata = []
        conflict = 0
        real_text_final = text

        for match in all_matches:
            current_index = match["start"] - conflict
            
            if match["style"] == "Link":
                metadata.append({
                    "type": "Link",
                    "from_index": current_index,
                    "length": match["length"],
                    "link_url": match["extra"]
                })
            elif match["style"] == "Mention":
                if mention_object_index < len(mention_objects):
                    object_id = mention_objects[mention_object_index]
                    metadata.append({
                        "type": "MentionText",
                        "from_index": current_index,
                        "length": match["length"],
                        "mention_text_object_guid": object_id,
                        "mention_text_user_id": object_id,
                        "mention_text_object_type": "group"
                    })
                    real_text_final = real_text_final.replace(f"({object_id})", "", 1)
                    conflict += 6 + len(object_id)
                    mention_object_index += 1
            else:
                if current_index >= 0 and current_index + match["length"] <= len(real_text_final):
                    metadata.append({
                        "type": match["style"],
                        "from_index": current_index,
                        "length": match["length"]
                    })

            conflict += len(match["full_match"]) - len(match["content"])
            real_text_final = real_text_final.replace(match["full_match"], match["content"], 1)

        return metadata, real_text_final

    @staticmethod
    def checkHTML(text) -> tuple:
        """
        Parse basic HTML tags and return metadata with plain text
        Supports: <b>, <strong>, <i>, <em>, <code>, <s>, <del>, <a href>, <u>, <span class="tg-spoiler">, <pre>
        Also supports mentions with: <a href="rubika://@username"> or objectId mentions
        """
        if text is None:
            return [], ""
        
        metadata = []
        conflict = 0
        result = []
        patterns = {
            "Pre": (r"<pre>([^<]+?)</pre>",),
            "Bold": (r"<b>([^<]+?)</b>", r"<strong>([^<]+?)</strong>"),
            "Italic": (r"<i>([^<]+?)</i>", r"<em>([^<]+?)</em>"),
            "Code": (r"<code>([^<]+?)</code>",),
            "Strike": (r"<s>([^<]+?)</s>", r"<del>([^<]+?)</del>"),
            "Underline": (r"<u>([^<]+?)</u>",),
            "Spoiler": (r'<span class="tg-spoiler">([^<]+?)</span>',),
            "Link": (r'<a href="([^"]+?)">([^<]+?)</a>',),
            "Mention": (r'<mention>([^<]+?)</mention>',),
        }
        
        mention_objects = [i.group(1) for i in finditer(r'<mention objectId="([^"]+)">([^<]+?)</mention>', text)]
        mention_object_index = 0
        
        all_matches = []
        used_positions = set()

        for style, pattern_list in patterns.items():
            for pattern in pattern_list:
                for match in finditer(pattern, text, flags=DOTALL):
                    start, end = match.start(), match.end()
                    
                    if any(pos in used_positions for pos in range(start, end)):
                        continue
                    
                    if style == "Link":
                        link_url, link_text = match.groups()
                        if link_url.startswith('rubika://'):
                            all_matches.append({
                                "start": start,
                                "end": end,
                                "length": len(link_text),
                                "style": "Mention",
                                "content": link_text,
                                "full_match": match.group(0),
                                "extra": link_url
                            })
                        else:
                            all_matches.append({
                                "start": start,
                                "end": end,
                                "length": len(link_text),
                                "style": style,
                                "content": link_text,
                                "full_match": match.group(0),
                                "extra": link_url
                            })
                    elif style == "Mention":
                        content = match.group(1)
                        all_matches.append({
                            "start": start,
                            "end": end,
                            "length": len(content),
                            "style": style,
                            "content": content,
                            "full_match": match.group(0),
                            "extra": None
                        })
                    elif style == "Pre":
                        content = match.group(1).strip() if match.group(1) else ""
                        all_matches.append({
                            "start": start,
                            "end": end,
                            "length": len(content),
                            "style": style,
                            "content": content,
                            "full_match": match.group(0),
                            "extra": None
                        })
                    else:
                        content = match.group(1)
                        all_matches.append({
                            "start": start,
                            "end": end,
                            "length": len(content),
                            "style": style,
                            "content": content,
                            "full_match": match.group(0),
                            "extra": None
                        })
                    
                    used_positions.update(range(start, end))

        all_matches.sort(key=lambda x: x["start"])
        real_text_final = text

        for match in all_matches:
            current_index = match["start"] - conflict
            if match["style"] == "Link":
                result.append({
                    "type": "Link",
                    "from_index": current_index,
                    "length": match["length"],
                    "link_url": match["extra"]
                })
            elif match["style"] == "Mention":
                if match.get("extra") and match["extra"].startswith('rubika://'):
                    result.append({
                        "type": "MentionText",
                        "from_index": current_index,
                        "length": match["length"],
                        "mention_text_object_guid": match["extra"].replace('rubika://', ''),
                        "mention_text_user_id": match["extra"].replace('rubika://', ''),
                        "mention_text_object_type": "user"
                    })
                elif mention_object_index < len(mention_objects):
                    object_id = mention_objects[mention_object_index]
                    result.append({
                        "type": "MentionText",
                        "from_index": current_index,
                        "length": match["length"],
                        "mention_text_object_guid": object_id,
                        "mention_text_user_id": object_id,
                        "mention_text_object_type": "group"
                    })
                    mention_object_index += 1
            else:
                if current_index >= 0 and current_index + match["length"] <= len(real_text_final):
                    result.append({
                        "type": match["style"],
                        "from_index": current_index,
                        "length": match["length"],
                    })

            conflict += len(match["full_match"]) - len(match["content"])
            real_text_final = real_text_final.replace(match["full_match"], match["content"], 1)

        return result, real_text_final

    @staticmethod
    def checkLink(url: str) -> Optional[bool]:
        for i in ["http:/", "https://"]:
            if url.startswith(i):
                return True

    @staticmethod
    def getMimeFromByte(data: bytes) -> str:
        mime = guess(data)
        return "pyrubi" if mime is None else mime.extension

    @staticmethod
    def generateFileName(mime: str) -> str:
        return "Pyrubi Library {}.{}".format(randint(1, 1000), mime)

    @staticmethod
    def getImageSize(data: bytes) -> tuple:
        try:
            from PIL import Image
        except ImportError:
            system("pip install pillow")
            from PIL import Image
        width, height = Image.open(BytesIO(data)).size
        return width, height

    @staticmethod
    def getImageThumbnail(data: bytes) -> str:
        try:
            from PIL import Image
        except ImportError:
            system("pip install pillow")
            from PIL import Image
        image = Image.open(BytesIO(data))
        width, height = image.size
        if height > width:
            new_height = 40
            new_width = round(new_height * width / height)
        else:
            new_width = 40
            new_height = round(new_width * height / width)
        image = image.resize((new_width, new_height), Image.LANCZOS)
        changed_image = BytesIO()
        image.save(changed_image, format="PNG")
        return b64encode(changed_image.getvalue()).decode("UTF-8")

    @staticmethod
    def getVideoData(data: bytes) -> tuple:
        try:
            from moviepy.editor import VideoFileClip
            with NamedTemporaryFile(delete=False, dir=".") as temp_video:
                temp_video.write(data)
                temp_path = temp_video.name
            chmod(temp_path, 0o777)
            try:
                from PIL import Image
            except ImportError:
                system("pip install pillow")
                from PIL import Image
            with VideoFileClip(temp_path) as clip:
                duration = clip.duration
                resolution = clip.size
                thumbnail = clip.get_frame(0)
                thumbnail_image = Image.fromarray(thumbnail)
                thumbnail_buffer = BytesIO()
                thumbnail_image.save(thumbnail_buffer, format="JPEG")
                thumbnail_b64 = b64encode(thumbnail_buffer.getvalue()).decode("UTF-8")
                clip.close()
            remove(temp_path)
            return thumbnail_b64, resolution, duration
        except ImportError:
            print("Can't get video data! Please install the moviepy library with: pip install moviepy")
            return Configs.defaultTumbInline, [900, 720], 1
        except:
            return Configs.defaultTumbInline, [900, 720], 1

    @staticmethod
    def getVoiceDuration(data: bytes) -> int:
        file = BytesIO()
        file.write(data)
        file.seek(0)
        return mp3.MP3(file).info.length

    @staticmethod
    def getMusicArtist(data: bytes) -> str:
        try:
            audio = File(BytesIO(data), easy=True)
            if audio and "artist" in audio:
                return audio["artist"][0]
            return "pyrubi"
        except Exception:
            return "pyrubi"
    
    @staticmethod
    def reaction_to_id(reaction: str) -> int:
        if len(reaction) != 1:
            raise ValueError("The reaction not has 1 len !")
        if not reaction in REACTION_MAP.keys():
            raise ValueError("The reaction is not valid !")
        return REACTION_MAP[reaction]


class Colors:
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BG_RESET = "\033[49m"
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
