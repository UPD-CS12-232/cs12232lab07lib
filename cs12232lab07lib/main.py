from dataclasses import dataclass
from enum import StrEnum
from typing import Any, TypeGuard, Callable
import json
from typing import TypedDict

from websockets.client import connect, WebSocketClientProtocol


class ChatMessageData(TypedDict):
    src: str
    dst: str | None
    msg: str


class AuthenticatedMessageData(TypedDict):
    msg: str
    public_chats: list[ChatMessageData]


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


JSON_ID_KEY = 'id'
JSON_PUBLIC_CHATS_KEY = 'public_chats'
JSON_CHAT_SRC_KEY = 'src'
JSON_CHAT_DST_KEY = 'dst'
JSON_CHAT_MSG_KEY = 'msg'

Data = dict[str, Any]


class Message(StrEnum):
    INCORRECT_FORMAT = 'INCORRECT_FORMAT'
    MISSING_JSON_KEYS = 'MISSING_JSON_KEYS'
    INVALID_CREDENTIALS = 'INVALID_CREDENTIALS'
    AUTHENTICATED = 'AUTHENTICATED'
    CHAT = 'CHAT'


class Session:
    @classmethod
    async def create(cls, username: str, password: str, endpoint: str):
        websocket = await connect(endpoint)
        await websocket.send(json.dumps({
            'username': username,
            'password': password,
        }))

        session = Session(username, endpoint, websocket)
        await session.fetch_chat_messages()

        return session

    def __init__(self, username: str, endpoint: str, websocket: WebSocketClientProtocol):
        self.username = username
        self.endpoint = endpoint
        self.public_chats = None
        self._websocket = websocket

    async def fetch_chat_messages(self):
        data = json.loads(await self._websocket.recv())

        if not self._is_authentication_message(data):
            raise self._make_error(data[JSON_ID_KEY])

        self.public_chats = data[JSON_PUBLIC_CHATS_KEY]

    def make_task(self, callback: Callable[[ChatMessage], None]):
        async def inner():
            while True:
                raw_data = str(await self._websocket.recv())
                print('Raw data:', raw_data)

                parsed_data = self._parse_message(raw_data)

                if self._is_chat_message(parsed_data):
                    chat = ChatMessage.from_data(parsed_data)
                    callback(chat)

        return inner

    def _parse_message(self, raw_data: str):
        try:
            parsed_data = json.loads(raw_data)
        except ValueError:
            raise self._make_error(Message.INCORRECT_FORMAT)

        if not isinstance(parsed_data, dict) or JSON_ID_KEY not in parsed_data:
            raise self._make_error(Message.INCORRECT_FORMAT)

        return parsed_data

    def _is_chat_message(self, data: Data) -> TypeGuard[ChatMessageData]:
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

    def _is_authentication_message(self, data: Data) -> TypeGuard[AuthenticatedMessageData]:
        if JSON_ID_KEY not in data:
            return False

        if data[JSON_ID_KEY] != Message.AUTHENTICATED:
            return False

        if not isinstance(data[JSON_PUBLIC_CHATS_KEY], list):
            return False

        return True

    def _make_error(self, msg_id: str):
        match msg_id:
            case Message.INCORRECT_FORMAT:
                return RuntimeError('Incorrect format')
            case Message.MISSING_JSON_KEYS:
                return RuntimeError('Missing JSON keys')
            case Message.INVALID_CREDENTIALS:
                return RuntimeError('Invalid credentials')

        return RuntimeError(f"Unknown message: {msg_id}")


async def authenticate(username: str, password: str, endpoint: str):
    return await Session.create(username, password, endpoint)
