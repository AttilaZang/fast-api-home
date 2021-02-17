
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from common.database import get_db
from common.depends import verify_token, is_auth_name
from cruds import courier_crud
from schemas import courier_schema
from schemas.courier_schema import ResetPassword, PasswordLogin


router = APIRouter()


@router.post('/login/')
def courier_login(courier: courier_schema.CourierRegister, db: Session = Depends(get_db)):
    """
    登录和注册一个接口
    """
    return courier_crud.courier_login(courier=courier, db=db)


@router.post('/service/area/edit/', dependencies=[Depends(verify_token)])
def service_area(area: courier_schema.ServiceArea, db: Session = Depends(get_db)):
    """新增/修改服务地址"""
    return courier_crud.service_area_edit(area=area, db=db)


@router.get('/service/area/msg/', dependencies=[Depends(verify_token)])
def service_area(courier_id: int, db: Session = Depends(get_db)):
    """新增/修改服务地址"""
    return courier_crud.service_area_msg(courier_id=courier_id, db=db)


@router.post('/password/login/')
def password_login(pwd_login: PasswordLogin, db: Session = Depends(get_db)):
    """
    密码登录
    """
    return courier_crud.password_login(pwd_login=pwd_login, db=db)


@router.post('/reset/password/', dependencies=[Depends(verify_token)])
def reset_password(reset_pwd: ResetPassword, db: Session = Depends(get_db)):
    """
    重置密码
    """
    return courier_crud.reset_password(reset_pwd=reset_pwd, db=db)


@router.get('/logout/')
async def logout(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """
    骑手登出
    """
    return courier_crud.courier_logout(token=token, db=db)


@router.get('/verify/token/')
async def login_verify_token(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """验证token,退出app重新打开不用登陆"""
    return courier_crud.login_verify_token(token=token, db=db)


@router.post('/verify/name/', dependencies=[Depends(verify_token)])
def courier_register(courier: courier_schema.VerifyName, db: Session = Depends(get_db)):
    """
    实名认证
    """
    return courier_crud.verify_name(db=db, courier=courier)


@router.get('/verify/status/', dependencies=[Depends(verify_token)])
def verify_status(*, courier_id: int, db: Session = Depends(get_db)):
    """
    验证是否实名审核通过
    """
    return courier_crud.verify_status(db=db, courier_id=courier_id)


@router.put('/work/', dependencies=[Depends(verify_token), Depends(is_auth_name)])
def courier_work(courier_id: int, db: Session = Depends(get_db)):
    """
    切换工作状态
    """
    return courier_crud.work_status(db=db, courier_id=courier_id)








