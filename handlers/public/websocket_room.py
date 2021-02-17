import logging

from typing import Dict, List

from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.websockets import WebSocket


log = logging.getLogger(__name__)


class Room:

    def __init__(self):
        log.info('Creating new empty room')
        self._users: Dict[str, WebSocket] = {}

    def __len__(self) -> int:
        """Get the number of users in the room"""
        return len(self._users)

    @property
    def empty(self) -> bool:
        """Check if the room is empty"""
        return len(self._users) == 0

    @property
    def user_list(self) -> List[str]:
        """Return a list of IDs for connected users"""
        print('我就是user_list >>>>>>', self._users)
        print('我就是list_user_list >>>>>>', list(self._users))

        return list(self._users)

    def add_user(self, user_id: str, websocket: WebSocket):
        """Add a user websocket, keyed by corresponding user ID

        Raises:
            ValueError: If the `user_id` already exists within the room
        """
        if user_id in self._users:
            raise ValueError(f'User {user_id} is already exists within the room')
        log.info(f'Addiing user {user_id} to room')
        self._users[user_id] = websocket

    async def kick_user(self, user_id: str):
        """Forcibly disconnect a user from the room.
        We do not need to call `remove_user`, as this will be invoked automatically
        when the websocket connection is closed by the `RoomLive.on_disconnect` method.
        Raises:
            ValueError: If the `user_id` is not held within the room.
        """
        if user_id not in self._users:
            raise ValueError(f"User {user_id} is not in the room")
        log.info("Kicking user %s from room", user_id)
        await self._users[user_id].close()

    def remove_user(self, user_id: str):
        """Remove a user from the room.
        Raises:
            ValueError: if the `user_id` is not held within the room
        """
        if user_id not in self._users:
            raise ValueError(f'User {user_id} is not in the room')
        log.info(f"Removing user {user_id} from room")
        del self._users[user_id]

    async def whisper(self, from_user: str, to_user: str, msg: dict):
        """Send a private message from one user to another.

        Raises:
            ValueError: If either `from_user` or `to_user` are not present within the room
        """
        if from_user not in self._users:
            raise ValueError(f"Calling user {from_user} is not in the room")
        log.info(f"User {from_user} messageing user {to_user} -> {msg}")
        if to_user not in self._users:
            raise ValueError(f'{to_user} is not in the room')
        await self._users[to_user].send_json({'err_no:': 0, 'err_msg': '', 'data': {'msg': msg}})


    async def broadcast_message(self, user_id: str, msg: str):
        """Broadcast message to all connected users"""
        for websocket in self._users.values():
            await websocket.send_json({
                "type": "MESSAGE",
                "data": {"user_id": user_id, "msg": msg}
            })


class RoomEventMiddleware:
    """
    Middleware for providing a global :class:`~.Room` instance to both HTTP
    and WebSocket scopes.
    """

    def __init__(self, app: ASGIApp):  # 形参只能叫这个名字
        self._app = app
        self._room = Room()

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope['type'] in ('lifespan', 'http', 'websocket'):
            scope['room'] = self._room
        await self._app(scope, receive, send)



