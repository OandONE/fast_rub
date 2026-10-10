from typing import Literal
import random
import string

class FakeGenerator:
    @staticmethod
    def message_id() -> str:
        return "".join(random.choices("0123456789", k=19))

    @staticmethod
    def id(
        start: Literal["b", "u", "g"] = "b"
    ) -> str:
        return f"{start}{''.join(random.choices(string.ascii_lowercase, k=31))}"

    chat_id = id
    sender_id = id

    @staticmethod
    def guid(
        start: Literal["b", "u", "g", "c", "s"] = "b"
    ) -> str:
        return f"{start}{''.join(random.choices(string.ascii_lowercase, k=31))}"

