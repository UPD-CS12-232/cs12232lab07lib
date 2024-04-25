from dataclasses import dataclass
from typing import TypedDict, Any
from enum import StrEnum


Data = dict[str, Any]


class Message(StrEnum):
    INCORRECT_FORMAT = 'INCORRECT_FORMAT'
    MISSING_JSON_KEYS = 'MISSING_JSON_KEYS'
    INVALID_CREDENTIALS = 'INVALID_CREDENTIALS'
    AUTHENTICATED = 'AUTHENTICATED'
    CHAT = 'CHAT'


class AuthenticatedMessage(TypedDict):
    msg: str
    public_chats: list[str]


class ChatMessageData(TypedDict):
    src: str
    dst: str | None
    msg: str


class AuthenticatedMessageData(TypedDict):
    msg: str
    chats: list[ChatMessageData]


@dataclass
class ChatMessage:
    src: str
    dst: str | None
    msg: str

    @classmethod
    def from_data(cls, data: ChatMessageData):
        return ChatMessage(
            src=data['src'],
            dst=data['dst'],
            msg=data['msg'],
        )

    def to_json(self):
        return {
            'src': self.src,
            'dst': self.dst,
            'msg': self.msg,
        }

