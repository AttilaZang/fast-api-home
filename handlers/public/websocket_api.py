
from typing import Optional, List, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.endpoints import WebSocketEndpoint
from starlette.requests import Request
from starlette.responses import FileResponse
from starlette.websockets import WebSocket
from common.logger import log
from handlers.public.websocket_room import Room

router = APIRouter()


class TaskList(BaseModel):
    to_courier: List[dict]
    data: dict


class SendData(BaseModel):
    from_user: str
    to_user: str
    msg: dict


@router.get('/websocket')
def home():
    return FileResponse('static/webSocketIndex.html')


@router.get('/user/list/')
async def list_users(request: Request):
    """
    查看所有在线人数
    """
    room: Optional[Room] = request.get('room')  # 能这样获取到的原因是注册了中间件
    if not room:
        return {'err_no:': 0, 'err_msg': '', 'data': {'user_list': []}}
    return {'err_no:': 0, 'err_msg': '', 'data': {'user_list': room.user_list}}


@router.get('/broadcast/message/')
async def broadcast_message(request: Request, user_id: str):
    """
    广播消息
    """
    room: Optional[Room] = request.get('room')
    if room is None:
        raise HTTPException(500, detail='Global `Room` instance unavailable!')
    try:
        await room.broadcast_message(user_id, msg='我是消息')
    except ValueError as e:
        log.logger.error(e)
        raise HTTPException(404, detail='消息发送失败')


@router.post('/users/kick/')
async def kick_user(request: Request, user_id: str):
    """
    从房间踢人
    """
    room: Optional[Room] = request.get('room')
    if room is None:
        raise HTTPException(500, detail='Global `Room` instance unavailable!')
    try:
        await room.kick_user(user_id)
        return {'err_no:': 0, 'err_msg': '', 'data': 'success'}
    except ValueError as e:
        log.logger.error(e)
        raise HTTPException(404, detail=f'No such user: {user_id}')


@router.post('/room/batch/whisper/')
async def batch_whisper(request: Request, task_list: TaskList):
    """批量发送"""
    success_list = []
    to_courier = task_list.to_courier
    room: Optional[Room] = request.get('room')
    if room is None:
        raise HTTPException(500, detail='Global `Room` instance unavailable!')
    try:
        for courier in to_courier:
            await room.whisper(courier['from_user'], courier['to_user'], msg=task_list.data)
            success_list.append(courier)
        return {'err_no:': 0, 'err_msg': '', 'data': 'success'}
    except Exception as e:
        if len(success_list) > 0:  # 通知列表中骑手，只要有通知成功的就算成功
            return {'err_no:': 0, 'err_msg': '', 'data': 'success'}
        else:
            log.logger.error(e)
            raise HTTPException(500, detail='消息发送失败')


@router.post('/room/whisper/')
async def room_whisper(request: Request, send_data: SendData):
    """私聊"""
    room: Optional[Room] = request.get('room')
    if room is None:
        raise HTTPException(404, detail='Global `Room` instance unavailable!')
    try:
        await room.whisper(send_data.from_user, send_data.to_user, send_data.msg)
        return {'err_no:': 0, 'err_msg': '', 'data': 'success'}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail='消息发送失败')


@router.websocket_route('/connection', name='ws')
class Roomlive(WebSocketEndpoint):
    """Live connection to the global :class`~.Room` instance,via WebSocket"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room: Optional[Room] = None
        self.user_id: Optional[str] = None

    @classmethod
    def get_next_user_id(cls):
        """Returns monotonically increasing numbered usernames in the form `user_[number]`"""
        user_id: str = f'user_{cls.count}'
        cls.count += 1
        return user_id

    async def on_connect(self, websocket: WebSocket):
        """
        建立新连接
        """
        log.logger.info('Connecting new user ...')

        identity = websocket.query_params['identity']
        identity_id = websocket.query_params['identity_id']

        room: Optional[Room] = self.scope.get('room')
        if room is None:
            raise RuntimeError(f"Global `Room` instance unavailable!")
        self.room = room
        self.user_id = f'{identity}_{identity_id}'
        print('我是user_id', self.user_id)
        await websocket.accept()
        await websocket.send_json(
            {"type": "ROOM_JOIN", "data": {"user_id": self.user_id}}
        )
        self.room.add_user(self.user_id, websocket)

    async def on_disconnect(self, _websocket: WebSocket, _close_code: int):
        """
        断开连接
        """
        if self.user_id is None:
            raise RuntimeError(
                "RoomLive.on_disconnect() called without a valid user_id"
            )
        self.room.remove_user(self.user_id)

    async def on_receive(self, _websocket: WebSocket, msg: Any):
        """
        接收消息
        """
        if self.user_id is None:
            raise RuntimeError("RoomLive.on_receive() called without a valid user_id")
        else:
            print(f'socket 发过来的消息{msg}')
            # log.logger.info(f'socket 发过来的消息{msg}')
