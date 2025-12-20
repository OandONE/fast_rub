from enum import Enum

class ParseMode(str, Enum):
    MARKDOWN = "Markdown"
    HTML = "HTML"

class Style(str, Enum):
    BOLD = "bold"
    SPOIL = "spoil"
    UNDERLINE = "underline"
    STRIKE = "strike"
    COPY = "copy"
    CODE = "code"
    LINK = "link"
    MENTION = "mention"

class MetaData:
    """متا دادن متن به صورت بولد، اسپویل، آندرلاین و ..."""
    
    _TEMPLATES = {
        Style.BOLD: {ParseMode.MARKDOWN: "**#text**", ParseMode.HTML: "<b>#text</b>"},
        Style.SPOIL: {ParseMode.MARKDOWN: "||#text||", ParseMode.HTML: '<span class="tg-spoiler">#text</span>'},
        Style.UNDERLINE: {ParseMode.MARKDOWN: "__#text__", ParseMode.HTML: "<u>#text</u>"},
        Style.STRIKE: {ParseMode.MARKDOWN: "~~#text~~", ParseMode.HTML: "<s>#text</s>"},
        Style.COPY: {ParseMode.MARKDOWN: "`#text`", ParseMode.HTML: "<code>#text</code>"},
        Style.CODE: {ParseMode.MARKDOWN: "```#text```", ParseMode.HTML: "<pre>#text</pre>"},
        Style.LINK: {ParseMode.MARKDOWN: "[#text](#link)", ParseMode.HTML: '<a href="#link">#text</a>'},
        Style.MENTION: {ParseMode.MARKDOWN: "#text", ParseMode.HTML: '<mention objectId="#sender_id">#text</mention>'}
    }

    def __init__(self, parse_mode: ParseMode = ParseMode.MARKDOWN):
        self.parse_mode = parse_mode

    def format_text(self, text: str, style: Style, **kwargs) -> str:
        """متن را با استایل مشخص قالب‌بندی می‌کند"""
        try:
            template = self._TEMPLATES[style][self.parse_mode]
        except KeyError:
            raise ValueError(f"Unsupported style or parse mode: {style}, {self.parse_mode}")
        for k, v in kwargs.items():
            template = template.replace(f"#{k}", v)
        return template.replace("#text", text)

    def bold(self, text: str) -> str:
        return self.format_text(text, Style.BOLD)

    def spoil(self, text: str) -> str:
        return self.format_text(text, Style.SPOIL)

    def underline(self, text: str) -> str:
        return self.format_text(text, Style.UNDERLINE)

    def strike(self, text: str) -> str:
        return self.format_text(text, Style.STRIKE)

    def copy(self, text: str) -> str:
        return self.format_text(text, Style.COPY)

    def code(self, text: str) -> str:
        return self.format_text(text, Style.CODE)

    def link(self, text: str, link: str) -> str:
        return self.format_text(text, Style.LINK, link=link)

    def mention(self, text: str, sender_id: str) -> str:
        return self.format_text(text, Style.MENTION, sender_id=sender_id)
