from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from common.database import get_db
from common.depends import verify_token, is_auth_name
from cruds import courier_crud
from schemas.courier_schema import AlipayInfo, CashOut, CashOutRecord, CapitalDetail, PaymentAccount

router = APIRouter()

@router.get('/center/', dependencies=[Depends(verify_token), Depends(is_auth_name)])
def courier_info(*, courier_id: int, db: Session = Depends(get_db)):
    """
    骑手中心
    """
    return courier_crud.courier_center(db=db, courier_id=courier_id)


@router.get('/account/', dependencies=[Depends(verify_token), Depends(is_auth_name)])
def courier_account(*, courier_id: int, db: Session = Depends(get_db)):
    """
    骑手账户
    """
    return courier_crud.courier_account(db=db, courier_id=courier_id)


@router.post('/payment/account/', dependencies=[Depends(verify_token)])
def capital_detail(payment_account: PaymentAccount, db: Session = Depends(get_db)):
    """
    账号姓名、支付宝
    """
    return courier_crud.courier_payment_account(db=db, payment_account=payment_account)


@router.post('/add/alipay/', dependencies=[Depends(verify_token)])
def courier_account(alipay_info: AlipayInfo, db: Session = Depends(get_db)):
    """
    添加支付宝账号
    """
    return courier_crud.courier_add_alipay(db=db, alipay_info=alipay_info)


@router.post('/cash/out/', dependencies=[Depends(verify_token)])
def cash_out(cash_out: CashOut, db: Session = Depends(get_db)):
    """
    提现
    """
    return courier_crud.cash_out(db=db, cash_out=cash_out)


@router.post('/cash/out/record/', dependencies=[Depends(verify_token)])
def cash_out_record(cash_out_record: CashOutRecord, db: Session = Depends(get_db)):
    """
    提现记录
    """
    return courier_crud.cash_out_record(db=db, cash_out_record=cash_out_record)


@router.post('/capital/detail/', dependencies=[Depends(verify_token)])
def capital_detail(capital_detail: CapitalDetail, db: Session = Depends(get_db)):
    """
    资金明细
    """
    return courier_crud.courier_capital_detail(db=db, capital_detail=capital_detail)


@router.get('/info/', dependencies=[Depends(verify_token)])
def courier_info(courier_id: int, db: Session = Depends(get_db)):
    """
    骑手信息
    """
    return courier_crud.courier_info(courier_id=courier_id, db=db)
