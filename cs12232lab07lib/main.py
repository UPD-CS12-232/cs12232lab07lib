from dataclasses import dataclass
from enum import StrEnum
from typing import Any, TypeGuard, Callable
import json

from websockets.sync.client import connect

from project_types import AuthenticatedMessage


JSON_ID_KEY = 'id'
JSON_PUBLIC_CHATS_KEY = 'public_chats'
JSON_CHAT_SRC_KEY = 'src'
JSON_CHAT_DST_KEY = 'dst'
JSON_CHAT_MSG_KEY = 'msg'

Data = dict[str, Any]


@dataclass
class ChatMessage:
    src: str
    dst: str | None
    msg: str


class Message(StrEnum):
    INCORRECT_FORMAT = 'INCORRECT_FORMAT'
    MISSING_JSON_KEYS = 'MISSING_JSON_KEYS'
    INVALID_CREDENTIALS = 'INVALID_CREDENTIALS'
    AUTHENTICATED = 'AUTHENTICATED'


class Session:
    def __init__(self, username: str, password: str, endpoint: str):
        with connect(endpoint) as websocket:
            websocket.send(json.dumps({
                'username': username,
                'password': password,
            }))

            data = json.loads(websocket.recv())

            if not self._is_authentication_message(data):
                raise self._make_error(data)

            self._websocket = websocket
            self._public_chats = data[JSON_PUBLIC_CHATS_KEY]

            self.username = username

    async def wait_for_messages(self, callback: Callable[[ChatMessage], None]):
        while True:
            raw_data = str(self._websocket.recv())
            print(raw_data)

            parsed_data = self._parse_message(raw_data)

            if self._is_chat_message(parsed_data):
                callback(parsed_data)

    def _parse_message(self, raw_data: str):
        try:
            parsed_data = json.loads(raw_data)
        except ValueError:
            raise self._make_error(Message.INCORRECT_FORMAT)

        if not isinstance(parsed_data, dict) or JSON_ID_KEY not in parsed_data:
            raise self._make_error(Message.INCORRECT_FORMAT)

        return parsed_data

    def _is_chat_message(self, data: Data) -> TypeGuard[ChatMessage]:
        if JSON_ID_KEY not in data:
            return False

        if data[JSON_ID_KEY] != Message.AUTHENTICATED:
            return False

        if not isinstance(data[JSON_CHAT_SRC_KEY], str):
            return False

        if not isinstance(data[JSON_CHAT_DST_KEY], str) and data[JSON_CHAT_DST_KEY] is not None:
            return False

        if not isinstance(data[JSON_CHAT_MSG_KEY], str):
            return False

        return True

    def _is_authentication_message(self, data: Data) -> TypeGuard[AuthenticatedMessage]:
        if JSON_ID_KEY not in data:
            return False

        if data[JSON_ID_KEY] != Message.AUTHENTICATED:
            return False

        if not isinstance(data[JSON_PUBLIC_CHATS_KEY], list):
            return False

        return True

    def _make_error(self, msg: str):
        match msg:
            case Message.INCORRECT_FORMAT:
                return RuntimeError('Incorrect format')
            case Message.MISSING_JSON_KEYS:
                return RuntimeError('Missing JSON keys')
            case Message.INVALID_CREDENTIALS:
                return RuntimeError('Invalid credentials')

        return RuntimeError(f"Unknown message: {msg}")


def authenticate(username: str, password: str, endpoint: str) -> Session:
    return Session(username, password, endpoint)


if __name__ == '__main__':
    endpoint = "ws://localhost:8000/ws"

    session = authenticate('testuser', 'testpass', endpoint)

    import asyncio

    async def async_main():
        def callback(msg: ChatMessage):
            print(f'received message: {msg}')

        x = 0

        while True:
            await session.wait_for_messages(callback)
            print(f'sleeping: {x}')
            await asyncio.sleep(1)
            x += 1

    asyncio.run(async_main())
