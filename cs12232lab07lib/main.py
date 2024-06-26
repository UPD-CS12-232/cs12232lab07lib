import asyncio
from typing import Callable
import json

from websockets.client import connect, WebSocketClientProtocol

from .project_types import Message, ChatMessage
from .constants import (
    JSON_ID_KEY,
    JSON_CHATS_KEY,
    JSON_CHAT_SRC_KEY,
    JSON_CHAT_DST_KEY,
    JSON_CHAT_MSG_KEY,
)
from .utils import (
    is_chat_message,
    is_authentication_message,
    make_error,
)


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
        self.chats: list[ChatMessage] | None = None
        self._websocket = websocket

    def send_group_chat_message(self, msg: str):
        self._send_message(msg, None)

    def send_direct_message(self, msg: str, dest: str):
        self._send_message(msg, dest)

    def _send_message(self, msg: str, dest: str | None):
        async def task():
            await self._websocket.send(json.dumps({
                JSON_ID_KEY: Message.CHAT,
                JSON_CHAT_SRC_KEY: self.username,
                JSON_CHAT_DST_KEY: dest,
                JSON_CHAT_MSG_KEY: msg,
            }))

        asyncio.create_task(task())

    async def fetch_chat_messages(self):
        data = json.loads(await self._websocket.recv())

        if not is_authentication_message(data):
            raise make_error(data[JSON_ID_KEY])

        self.chats = [ChatMessage.from_data(chat_data) for chat_data in data[JSON_CHATS_KEY]]

    def make_task(self, on_chat_received: Callable[[ChatMessage], None]):
        async def task_loop():
            while True:
                raw_data = str(await self._websocket.recv())
                print('Raw data:', raw_data)

                if is_chat_message(parsed_data := self._parse_message(raw_data)):
                    on_chat_received(ChatMessage.from_data(parsed_data))

        return task_loop

    def _parse_message(self, raw_data: str):
        try:
            parsed_data = json.loads(raw_data)
        except ValueError:
            raise make_error(Message.INCORRECT_FORMAT)

        if not isinstance(parsed_data, dict) or JSON_ID_KEY not in parsed_data:
            raise make_error(Message.INCORRECT_FORMAT)

        return parsed_data


async def authenticate(username: str, password: str, endpoint: str):
    return await Session.create(username, password, endpoint)
