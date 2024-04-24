import asyncio
from typing import Callable
import json

from websockets.client import connect, WebSocketClientProtocol

from .project_types import Message, ChatMessage
from .constants import JSON_ID_KEY, JSON_PUBLIC_CHATS_KEY, JSON_CHAT_SRC_KEY, JSON_CHAT_DST_KEY, JSON_CHAT_MSG_KEY
from .utils import is_chat_message, is_authentication_message, make_error


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

    def send_group_chat_message(self, msg: str):
        async def task():
            await self._websocket.send(json.dumps({
                JSON_ID_KEY: Message.CHAT,
                JSON_CHAT_SRC_KEY: self.username,
                JSON_CHAT_DST_KEY: None,
                JSON_CHAT_MSG_KEY: msg,
            }))

        asyncio.get_event_loop().create_task(task())

    async def fetch_chat_messages(self):
        data = json.loads(await self._websocket.recv())

        if not is_authentication_message(data):
            raise make_error(data[JSON_ID_KEY])

        self.public_chats = data[JSON_PUBLIC_CHATS_KEY]

    def make_task(self, callback: Callable[[ChatMessage], None]):
        async def inner():
            while True:
                raw_data = str(await self._websocket.recv())
                print('Raw data:', raw_data)

                parsed_data = self._parse_message(raw_data)

                if is_chat_message(parsed_data):
                    chat = ChatMessage.from_data(parsed_data)
                    callback(chat)

        return inner

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
