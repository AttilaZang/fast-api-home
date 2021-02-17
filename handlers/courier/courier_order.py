
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from common.database import get_db
from common.depends import verify_token
from cruds import courier_crud
from schemas.courier_schema import StartDelivery, FinishDelivery

router = APIRouter()

@router.get('/order/list/', dependencies=[Depends(verify_token)])
def courier_order_list(*, courier_id: int, status: int, db: Session = Depends(get_db)):
    """
    订单列表
    """
    return courier_crud.courier_order_list(db=db, courier_id=courier_id, status=status)


@router.get('/order/info/', dependencies=[Depends(verify_token)])
def courier_order_info(*, order_id: int, db: Session = Depends(get_db)):
    """
    订单详情
    """
    return courier_crud.courier_order_info(db=db, order_id=order_id)


@router.get('/accept/order/', dependencies=[Depends(verify_token)])
def accept_order(*, courier_id: int, order_id: int, db: Session = Depends(get_db)):
    """
    接单并生成订单号
    """
    return courier_crud.courier_accept_order(db=db, courier_id=courier_id, order_id=order_id)


@router.post('/start/delivery/', dependencies=[Depends(verify_token)])
def courier_start_delivery(start_delivery: StartDelivery, db: Session = Depends(get_db)):
    """
    开始配送
    """
    return courier_crud.courier_start_delivery(db=db, start_delivery=start_delivery)


@router.post('/finish/delivery/', dependencies=[Depends(verify_token)])
def courier_finish_delivery(finish_delivery: FinishDelivery, db: Session = Depends(get_db)):
    """
    完成配送
    """
    return courier_crud.courier_finish_delivery(db=db, finish_delivery=finish_delivery)















