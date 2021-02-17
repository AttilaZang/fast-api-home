
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import FileResponse
from common.database import get_db
from cruds import courier_crud
from schemas.courier_schema import Transfer, CheckMsg, CourierCheck, CourierTransfer

router = APIRouter()


@router.get('/background/')
def background():
    return FileResponse('static/backgroundManagement.html')


@router.get('/check/html/')
def check_html():
    return FileResponse('static/verifyName.html')


@router.get('/transfer/html/')
def check_html():
    return FileResponse('static/billTransfer.html')


@router.post('/check/list/')
def courier_check_list(courier_check: CourierCheck, db: Session = Depends(get_db)):
    """
    找到courier 表中所有提交实名认证审核的人员
    """
    return courier_crud.check_list(courier_check=courier_check, db=db)


@router.post('/transfer/list/')
def courier_transfer_list(courier_transfer: CourierTransfer, db: Session = Depends(get_db)):
    """
    找到所有申请提现的记录
    """
    return courier_crud.transfer_list(courier_transfer=courier_transfer, db=db)


@router.post('/transfer/')
def courier_transfer(transfer_msg: Transfer, db: Session = Depends(get_db)):
    """
    给提现的骑手转账
    1. 修改 Wallet 表中balance
    2. 修改 Bill 表中 status
    """
    return courier_crud.transfer(transfer_msg=transfer_msg, db=db)


@router.post('/pass/check/')
def courier_pass_check(check_msg: CheckMsg, db: Session = Depends(get_db)):
    """
    用户通过实名认证审核
    1. 修改courier 表中的 is_auth 与 name 字段
    """
    return courier_crud.pass_check(check_msg=check_msg, db=db)