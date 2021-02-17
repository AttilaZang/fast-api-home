
import uvicorn
import secrets
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from handlers.customer import user_serv, user_addr
from handlers.courier import courier_serv, courier_order, courier_mine, background_management
from handlers.public import public_serv, websocket_api
from handlers.public.websocket_room import RoomEventMiddleware

SECRET_KEY = secrets.token_hex()

app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)  # 线上不能暴露接口文档
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.add_middleware(RoomEventMiddleware)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_headers=["*"], allow_methods=["*"]
)


app.debug = True


app.include_router(user_serv.router, prefix='/user')
app.include_router(user_addr.router, prefix='/user')
app.include_router(courier_serv.router, prefix='/courier')
app.include_router(courier_order.router, prefix='/courier')
app.include_router(courier_mine.router, prefix='/courier')
app.include_router(background_management.router, prefix='/courier')
app.include_router(public_serv.router)
app.include_router(websocket_api.router)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
