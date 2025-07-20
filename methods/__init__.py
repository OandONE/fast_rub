from .chats import Chats
from .helper import Helper
from .messages import Messages
from .settings import Settings
from .users import Users
from .utilities import Utilities

class Methods(
    Chats,
    Helper,
    Messages,
    Settings,
    Users,
    Utilities
):
    pass