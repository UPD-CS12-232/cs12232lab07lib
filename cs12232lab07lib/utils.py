from typing import TypeGuard

from .constants import JSON_ID_KEY, JSON_CHAT_SRC_KEY, JSON_CHAT_DST_KEY, JSON_CHAT_MSG_KEY, JSON_PUBLIC_CHATS_KEY
from .project_types import Data, ChatMessageData, Message, AuthenticatedMessageData


def is_chat_message(data: Data) -> TypeGuard[ChatMessageData]:
    if JSON_ID_KEY not in data:
        return False

    if data[JSON_ID_KEY] != Message.CHAT:
        return False

    if not isinstance(data[JSON_CHAT_SRC_KEY], str):
        return False

    if not isinstance(data[JSON_CHAT_DST_KEY], str) and data[JSON_CHAT_DST_KEY] is not None:
        return False

    if not isinstance(data[JSON_CHAT_MSG_KEY], str):
        return False

    return True


def is_authentication_message(data: Data) -> TypeGuard[AuthenticatedMessageData]:
    if JSON_ID_KEY not in data:
        return False

    if data[JSON_ID_KEY] != Message.AUTHENTICATED:
        return False

    if not isinstance(data[JSON_PUBLIC_CHATS_KEY], list):
        return False

    return True


def make_error(msg_id: str):
    match msg_id:
        case Message.INCORRECT_FORMAT:
            return RuntimeError('Incorrect format')
        case Message.MISSING_JSON_KEYS:
            return RuntimeError('Missing JSON keys')
        case Message.INVALID_CREDENTIALS:
            return RuntimeError('Invalid credentials')

    return RuntimeError(f"Unknown message: {msg_id}")
