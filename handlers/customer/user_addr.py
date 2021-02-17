from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter
from common.depends import verify_token
from cruds import user_crud
from common.database import get_db
from schemas import user_schema
from schemas.user_schema import AddrDelete

router = APIRouter()


@router.get('/addr/list/', dependencies=[Depends(verify_token)])
def user_addr_list(*, user_id: int, db: Session = Depends(get_db)):
    """
    地址列表
    """
    return user_crud.get_addr_list(db=db, user_id=user_id)


@router.post('/addr/create/', dependencies=[Depends(verify_token)])
def addr_create(addr: user_schema.AddrCreate, db: Session = Depends(get_db)):
    """
    添加地址
    """
    return user_crud.create_addr(db=db, addr=addr)


@router.put('/addr/update/', dependencies=[Depends(verify_token)])
def addr_update(addr: user_schema.AddrUpdate, db: Session = Depends(get_db)):
    """
    更新地址
    """
    return user_crud.update_addr(db=db, addr=addr)


@router.delete('/addr/delete/', dependencies=[Depends(verify_token)])
def addr_delete(addr: AddrDelete, db: Session = Depends(get_db)):
    """
    删除地址
    """
    return user_crud.delete_addr(db=db, addr=addr)
