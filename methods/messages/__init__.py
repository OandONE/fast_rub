
from .delete_message import DeleteMessage
from .edit_message_keypad import EditMessageKeypad
from .edit_message_text import EditMessageText
from .forward_message import ForwardMessage
from .send_contact import SendContact
from .send_location import SendLocation
from .send_poll import SendPoll
from .send_text import SendText

class Messages(
    DeleteMessage,
    EditMessageKeypad,
    EditMessageText,
    ForwardMessage,
    SendContact,
    SendLocation,
    SendPoll,
    SendText
):
    pass