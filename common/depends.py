from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from common.database import get_db
from common.extensions import redis_token
from cruds.courier_crud import get_courier


async def verify_token(token: str = Header(...)):
    if not redis_token.get(token):
        raise HTTPException(status_code=401, detail="token invalid")
    return token


async def is_auth_name(courier_id: int, db: Session = Depends(get_db)):
    db_courier = get_courier(db=db, courier_id=courier_id)
    if not db_courier:
        raise HTTPException(404, detail='courier not found')
    if not db_courier.is_auth:
        raise HTTPException(401, detail='骑手没有实名认证')
