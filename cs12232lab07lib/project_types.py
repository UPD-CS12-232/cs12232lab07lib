from typing import TypedDict


class AuthenticatedMessage(TypedDict):
    msg: str
    public_chats: list[str]
