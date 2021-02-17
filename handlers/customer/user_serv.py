
from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter, HTTPException, Request
from common.depends import verify_token
from common.extensions import redis_token
from cruds import user_crud
from common.database import get_db
from schemas import user_schema
from schemas.user_schema import WxPay, WxRefund

router = APIRouter()


@router.post('/login/')
def user_login(login: user_schema.Login, db: Session = Depends(get_db)):
    """
    检查是否绑定了手机号
    """
    return user_crud.user_login(db=db, js_code=login.js_code)


@router.post('/bind/mobile/')
def bind_mobile(bind_mobile: user_schema.BindMobile, db: Session = Depends(get_db)):
    """
    绑定手机号（创建用户）
    """
    return user_crud.bind_mobile(db=db, bind_mobile=bind_mobile)


@router.get('/logout/')
async def logout(token: str = Depends(verify_token)):
    """
    退出登录
    """
    ret = redis_token.delete(token)
    if ret == 0:
        raise HTTPException(404, 'token not found')
    return {'err_no': 0, 'err_msg': '', 'data': 'success'}


@router.get('/verify/token/')
async def login_verify_token(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """验证token,小程序打开不用登陆"""
    return user_crud.login_verify_token(token=token, db=db)


@router.get('/delivery/num/', dependencies=[Depends(verify_token)])
def delivery_num(*, lng: float, lat: float, request: Request):
    """
    获取附近1km骑手数量x
    """
    return user_crud.delivery_num(lng=lng, lat=lat, request=request)


@router.post('/get/goods/', dependencies=[Depends(verify_token)])
def get_goods(goods_msg: user_schema.GoodsMsg, request: Request, db: Session = Depends(get_db)):
    """
    取货
    """
    return user_crud.get_goods(goods_msg=goods_msg, db=db, request=request)


@router.get('/cancel/order/', dependencies=[Depends(verify_token)])
def cancel_order(order_id: int, total_fee: str, out_trade_no: str, db: Session = Depends(get_db)):
    """
    取消订单, 需要申请退款, 并退优惠券(如有)
    """
    return user_crud.cancel_order(db=db, order_id=order_id, total_fee=total_fee, out_trade_no=out_trade_no)


@router.get('/order/list/', dependencies=[Depends(verify_token)])
def completed_order_list(user_id: int, status: int, db: Session = Depends(get_db)):
    """
    已完成的订单列表
    """
    return user_crud.order_list(db=db, user_id=user_id, status=status)


@router.post('/comment/', dependencies=[Depends(verify_token)])
def user_comment(comment: user_schema.Comment, db: Session = Depends(get_db)):
    """
    用户评论
    """
    return user_crud.user_comment(db=db, comment=comment)


@router.get('/coupons/list/', dependencies=[Depends(verify_token)])
def coupons_list(*, user_id: int, db: Session = Depends(get_db)):
    """
    优惠券列表
    """
    return user_crud.coupons_list(db=db, user_id=user_id)


@router.get('/invitation/code/', dependencies=[Depends(verify_token)])
def invitation_code(user_id: int, db: Session = Depends(get_db)):
    """
    我的邀请码
    """
    return user_crud.invitation_code(db=db, user_id=user_id)


@router.post('/wx/pay/', dependencies=[Depends(verify_token)])
def _wx_pay(wx_pay: WxPay, request: Request, db: Session = Depends(get_db)):
    """
    微信支付
    """
    return user_crud._wx_pay(wx_pay=wx_pay, request=request, db=db)


@router.post('/wx/refund/', dependencies=[Depends(verify_token)])
def _wx_refund(wx_refund: WxRefund):
    """
    微信退款
    """
    return user_crud._wx_refund(total_fee=str(wx_refund.total_fee), out_refund_no=wx_refund.out_refund_no)


@router.post('/payback')
async def payback(request: Request, db: Session = Depends(get_db)):
    """
    微信回调函数
    """
    msg = await request.body()
    msg_str = msg.decode()
    return user_crud.payback(msg_str=msg_str, db=db)


