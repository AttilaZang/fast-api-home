import time

import jwt
import requests
import xmltodict
from datetime import datetime, timedelta
from random import Random
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import Response
from common.get_open_id import getOpenId
from common.settings import DefaultConfig
from common.general import generate_jwt, SECRET_KEY, ALGORITHM
from common.invitation_code import id2code
from common.logger import log
from common.wx_biz_data_crypt import WXBizDataCrypt
from common.wx_pay import WX_PayToolUtil
from handlers.public.websocket_room import Room
from models.address import Address
from models.coupons import Coupons
from models.order_info import OrderInfo
from models.wx_pay_msg import WxPayMsg
from schemas.user_schema import BindMobile, WxPay, AddrDelete
from common.extensions import redis_serv, redis_token, redis_cust
from models.users import Users
from schemas import user_schema
from utils.constants import TOKEN_EXPIRES, SESSION_KEY, INCOME_RATE


def datetime2unix(dt):
    return time.mktime(dt.timetuple())


def random_num(randomlenth=10):
    str = ''
    chars = '1234567890'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlenth):
        str += chars[random.randint(0, length)]
    str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    return str_time + str


def get_user(db: Session, user_id: int):
    return db.query(Users).filter(
        Users.id == user_id,
        Users.is_active == 1
    ).first()


def get_order(db: Session, order_id: int):
    db_order = db.query(OrderInfo).filter(OrderInfo.id == order_id).first()
    return db_order


def get_user_by_code(db: Session, code: str):
    return db.query(Users).filter(Users.code == code, Users.is_active == 1).first()


def get_user_by_openid(db: Session, open_id: str):
    return db.query(Users).filter(
        Users.openid == open_id
    ).first()


def get_user_by_mobile(db: Session, mobile: str):
    return db.query(Users).filter(
        Users.mobile == mobile,
        Users.is_active == 1
    ).first()


def update_user(db: Session, user: user_schema.UserEdit):
    db_user = get_user(db=db, user_id=user.id)
    if not db_user:
        log.logger.error('没有该用户')
        raise HTTPException(404, 'user not found')
    db_user.name = user.name
    db.commit()
    db.close()
    return {'err_no': 0, 'err_msg': '', 'data': 'success'}


def get_addr_list(db: Session, user_id: int):
    """用户地址列表"""
    try:
        addrs = db.query(Address).filter(
            Address.user_id == user_id,
            Address.is_delete == 0
        ).all()

        ret = []
        for addr in addrs:
            ret.append({
                'id': addr.id,
                'user_id': addr.user_id,
                'place': addr.place,
                'lng': float(addr.lng),
                'lat': float(addr.lat),
                'addr_type': addr.addr_type,
                'contacts': addr.contacts,
                'mobile': addr.mobile,
                'gender': addr.gender,
                'region': addr.region
            })
        return {'err_no': 0, 'err_msg': '', 'data': {'addr_list': ret}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def create_addr(db: Session, addr: user_schema.AddrCreate):
    """新增地址"""
    try:
        addr_dict = dict(addr)
        db_addr = Address(**addr_dict)
        db.add(db_addr)
        db.commit()
        return {'err_no': 0, 'err_msg': '', 'data': 'success'}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def get_addr(db: Session, addr_id: int):
    try:
        db_addr = db.query(Address).filter(
            Address.id == addr_id,
            Address.is_delete == 0
        ).first()
        return db_addr
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def update_addr(db: Session, addr: user_schema.AddrUpdate):
    """更新地址"""
    try:
        new_addr = dict(addr)
        addr_id = new_addr.pop('id')
        db.query(Address).filter(Address.id == addr_id).update(new_addr)
        db.commit()
        return {'err_no': 0, 'err_msg': '', 'data': 'success'}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def delete_addr(db: Session, addr: AddrDelete):
    """删除地址"""
    try:
        db.query(Address).filter(Address.id == addr.id).update({'is_delete': 1})
        db.commit()
        return {'err_no': 0, 'err_msg': '', 'data': 'success'}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def order_list(db: Session, user_id: int, status: int):
    """订单列表"""
    try:
        db_order = db.query(OrderInfo).filter(
            OrderInfo.user_id == user_id,
            OrderInfo.status == status
        ).all()

        ret = []
        for order in db_order:
            if status == 0:
                order_status = 0 if order.courier_id == -1 else 1  # 骑手接单时的状态码也是0，所以需要更改状态
            else:
                order_status = order.status
            ret.append({
                "order_id": order.id,
                "deliver_time": datetime2unix(order.deliver_time) if order.deliver_time else 0,  # 送达时间,返回时间戳
                "create_time": datetime2unix(order.create_time),  # 下单时间，返回时间戳
                "get_addr": order.get_addr,  # 取货地址
                "recv_addr": order.recv_addr,  # 收货地址
                "contacts": order.contacts,  # 联系人
                "mobile": order.mobile,  # 联系人电话
                "cost": order.cost / 100,  # 金额 单位是分
                "status": order_status,  # 状态码
                "out_trade_no": order.out_trade_no,  # 用户支付单号
                "courier_id": order.courier_id if order.courier_id else -1,  # -1 就是没有接单
                "is_commented": order.is_commented  # true/false
            })
        return {'err_no': 0, 'err_msg': '', 'user_order_list': ret}

    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def user_comment(db: Session, comment: user_schema.Comment):
    """用户评论"""
    try:
        db_order = db.query(OrderInfo).filter(OrderInfo.id == comment.order_id).first()
        db_order.score = comment.score
        db_order.is_anonymous = comment.is_anonymous
        db_order.is_commented = 1  # 已评价的更改状态
        db.commit()
        return {'err_no': 0, 'err_msg': '', 'data': 'success'}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def user_login(db: Session, js_code: str):
    """用户登录后检查是否绑定了手机号"""
    try:
        open_id, session_key = getOpenId(js_code)
        db_user = get_user_by_openid(db=db, open_id=open_id)
        if not db_user:
            new_user = Users(openid=open_id)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            redis_cust.set(f'session_key_{new_user.id}', session_key, ex=SESSION_KEY)
            user_info = {
                'id': new_user.id,
                'mobile': '',
                'token': ''
            }
            return {'err_no': 0, 'err_msg': '', 'data': {'user_info': user_info}}
        elif not db_user.mobile:
            redis_cust.set(f'session_key_{db_user.id}', session_key, ex=SESSION_KEY)
            user_info = {
                'id': db_user.id,
                'mobile': '',
                'token': ''
            }
            return {'err_no': 0, 'err_msg': '', 'data': {'user_info': user_info}}
        else:
            token = generate_jwt(user_id=db_user.id, mobile=db_user.mobile)
            redis_token.set(token, 1, ex=TOKEN_EXPIRES)
            user_info = {
                'id': db_user.id,
                'mobile': db_user.mobile,
                'token': token
            }
            return {'err_no': 0, 'err_msg': '', 'data': {'user_info': user_info}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def bind_mobile(db: Session, bind_mobile: BindMobile):
    """小程序登录后绑定手机号"""

    session_key_bytes = redis_cust.get(f'session_key_{bind_mobile.user_id}')
    if not session_key_bytes:
        log.logger.error('redis中没有合法的session_key')
        raise HTTPException(404, detail='session_key invalid')

    try:
        session_key_str = session_key_bytes.decode()
        pc = WXBizDataCrypt(DefaultConfig.APP_ID, session_key_str)
        ret = pc.decrypt(bind_mobile.encryptedData, bind_mobile.iv)
        mobile = ret.get('purePhoneNumber')
        db_user = get_user(db=db, user_id=bind_mobile.user_id)
        db_user.mobile = mobile  # 更新mobile

        # 给自己加一张优惠券
        db_coupons = Coupons(
            user_id=db_user.id,
            coupon_type='1~10kg',
            coupon_amount=99,  # 单位是分
            expiration_time=datetime.today() + timedelta(days=7)
        )
        db.add(db_coupons)

        # 获得邀请人信息
        code_user = get_user_by_code(db=db, code=bind_mobile.code)
        if code_user:
            db_user.inviter = code_user.id
            # 给邀请人加一张优惠券
            db_coupons = Coupons(
                user_id=code_user.id,
                coupon_type='1~10kg',
                coupon_amount=99,
                expiration_time=datetime.today() + timedelta(days=7)
            )
            db.add(db_coupons)

        db.commit()
        db.refresh(db_user)
        token = generate_jwt(user_id=db_user.id, mobile=db_user.mobile)
        redis_token.set(token, 1, ex=TOKEN_EXPIRES)
        user_info = {
            'id': db_user.id,
            'mobile': db_user.mobile,
            'token': token
        }
        return {'err_no': 0, 'err_msg': '', 'data': {'user_info': user_info}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def invitation_code(db: Session, user_id: int):
    """我的邀请码"""
    try:
        db_user = get_user(db=db, user_id=user_id)
        inviter_num = db.query(Users.id).filter(Users.inviter == user_id).count()
        if not db_user.code:
            code = id2code(user_id)
            db_user.code = code
            db.commit()
            db.refresh(db_user)

        inviter_info = {
            'code': db_user.code,
            'inviter_num': inviter_num  # 邀请的人数
        }
        return {'err_no': 0, 'err_msg': '', 'data': {'inviter_info': inviter_info}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def coupons_list(db: Session, user_id: int):
    """优惠券列表"""
    try:
        today = datetime.today()
        db_coupons = db.query(Coupons).filter(
            Coupons.user_id == user_id,
            Coupons.is_use == 0,
            Coupons.expiration_time >= today
        ).all()

        ret = []
        for coupons in db_coupons:
            ret.append({
                'id': coupons.id,
                'coupon_amount': coupons.coupon_amount / 100,  # 单位改成元
                'coupon_type': coupons.coupon_type,
                'expiration_time': str(coupons.expiration_time)
            })
        return {'err_no': 0, 'err_msg': '', 'data': {'coupons_list': ret, 'coupons_num': len(ret)}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def get_coupons_amount(db: Session, coupons_id: int):
    # 不能关闭session, 引用的更新不了字段
    try:
        coupon = db.query(Coupons).filter(
            Coupons.id == coupons_id).first()
        if not coupon:
            raise HTTPException(404, detail='coupon not found')
        if coupon.is_use == 1:
            raise HTTPException(400, detail='优惠券已被使用')
        return coupon
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)


def get_goods(goods_msg: user_schema.GoodsMsg, db: Session, request: Request):
    """用户下单取货"""
    weight2cost = {'1~10kg': 100, '10~20kg': 150, '20~30kg': 200}  # 单位是分
    # 获取附近1km的骑手
    near_person = redis_serv.georadius(name='courier', longitude=goods_msg.lng, latitude=goods_msg.lat, radius=1, unit='km')
    for i in range(100):
        if i == 30 or i == 60:
            time.sleep(1)
        room: Optional[Room] = request.get('room')  # 能这样获取到的原因是注册了中间件
        user_list = room.user_list
        online_user = [p for p in near_person if p.decode() in user_list]
        if online_user:
            break
    else:
        online_user = []

    if not online_user:
        # 退款
        _wx_refund(total_fee=str(goods_msg.cost), out_refund_no=goods_msg.out_trade_no)
        log.logger.error('附近没有骑手')
        raise HTTPException(400, detail='附近暂时没有骑手')

    if goods_msg.coupons_id != -1:
        coupons = get_coupons_amount(db=db, coupons_id=goods_msg.coupons_id)
        if coupons.user_id != goods_msg.user_id:
            raise HTTPException(400, '此优惠券不属于该用户')
        coupon_amount = coupons.coupon_amount
        if (coupon_amount + goods_msg.cost) != weight2cost.get(goods_msg.weight):
            log.logger.error('优惠券结算后的支付金额错误')
            raise HTTPException(400, detail='支付金额错误')
        cost = coupon_amount + goods_msg.cost  # 原价入库
        coupons.is_use = 1  # 优惠券被使用
    else:
        if goods_msg.cost != weight2cost.get(goods_msg.weight):
            log.logger.error('没有用优惠券的支付金额错误')
            raise HTTPException(400, detail='支付金额错误')
        cost = goods_msg.cost

    gender = "女士" if goods_msg.gender == 0 else "先生"
    # 生成order 并存表
    new_order = OrderInfo(
        weight=goods_msg.weight,
        cost=cost,
        order_num=random_num(),
        user_id=goods_msg.user_id,
        recv_addr=goods_msg.recv_addr,
        get_addr=goods_msg.get_addr,
        contacts=goods_msg.contacts + gender,
        mobile=goods_msg.mobile,
        take_info=goods_msg.take_info,
        coupons_id=goods_msg.coupons_id,
        out_trade_no=goods_msg.out_trade_no
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    new_order_id = new_order.id   # 重新赋值，关闭会话也可用

    data = {
        'order_id': new_order_id,
        'get_addr': goods_msg.get_addr,
        'recv_addr': goods_msg.recv_addr,
        'contacts': goods_msg.contacts + gender,  # 联系人 如：张先生/王女士
        'mobile': goods_msg.mobile,
        'weight': goods_msg.weight,
        'take_info': goods_msg.take_info,
        'coupons_id': goods_msg.coupons_id,
        'real_cost': cost * INCOME_RATE,  # 骑手端收到真实金额

    }

    redis_serv.set(f'order_id_{new_order_id}', 1)

    to_courier = []
    for c in online_user:
        to_courier.append({
            'from_user': c.decode(),  # 存在用户端下单了但是没有连socket 的情况
            'to_user': c.decode()  # courier_1
        })

    # 批量发送消息
    for i in range(120):
        if i in {30, 60, 90}:
            time.sleep(1)   # socket 重连机制是1s
        url = DefaultConfig.SELF_URL + '/room/batch/whisper/'
        res = requests.post(url, json={"to_courier": to_courier, 'data': data})
        if res.status_code == 200:
            break
    else:
        # 调用取消订单接口
        cancel_order(db=db, order_id=new_order_id, total_fee=str(goods_msg.cost),
                     out_trade_no=goods_msg.out_trade_no)
        # 使用的优惠券改成未用
        if goods_msg.coupons_id != -1:
            coupons = get_coupons_amount(db=db, coupons_id=int(goods_msg.coupons_id))
            coupons.is_use = 0
            db.commit()
        log.logger.error('websocket通知骑手失败')
        raise HTTPException(500, detail='通知骑手失败')
    db.close()
    return {'err_no': 0, 'err_msg': '', 'data': {'order_id': new_order_id}}


def cancel_order(db: Session, order_id: int, total_fee: str, out_trade_no: str):

    ret = redis_serv.delete(f'order_id_{order_id}')
    if ret == 0:
        log.logger.error('redis中没有订单')
        raise HTTPException(404, 'order not found')
    db_order = get_order(db=db, order_id=order_id)
    if not db_order:
        log.logger.error('订单表中没有该订单')
        raise HTTPException(404, 'order not found')
    db_order.status = -1
    coupons_id = db_order.coupons_id
    if coupons_id != -1:
        db_coupons = db.query(Coupons).filter(Coupons.id == coupons_id).first()
        db_coupons.is_use = 0
        total_fee = str(int(total_fee) - db_coupons.coupon_amount)  # 使用优惠券的时候传的还是原金额
    db.commit()
    db.close()
    # 退款
    wp = WX_PayToolUtil(APP_ID=DefaultConfig.APP_ID,
                        MCH_ID=DefaultConfig.MCH_ID,
                        API_KEY=DefaultConfig.API_KEY,
                        NOTIFY_URL=DefaultConfig.NOTIFY_URL
                        )
    return wp.get_refund_url(total_fee=total_fee, refund_fee=total_fee,
                             out_refund_no=out_trade_no)


def delivery_num(lng: float, lat: float, request: Request):
    near_person = redis_serv.georadius(name='courier', longitude=lng, latitude=lat, radius=500, unit='m')
    # 判断一下websocket中是否连着
    room: Optional[Room] = request.get('room')  # 能这样获取到的原因是注册了中间件
    user_list = room.user_list
    online_user = [p for p in near_person if p.decode() in user_list]
    return {'err_no:': 0, 'err_msg': '', 'data': {'num': len(online_user)}}


def _wx_pay(wx_pay: WxPay, db: Session, request: Request):
    try:
        db_user = get_user(db=db, user_id=wx_pay.user_id)
        openid = db_user.openid

        wp = WX_PayToolUtil(APP_ID=DefaultConfig.APP_ID,
                            MCH_ID=DefaultConfig.MCH_ID,
                            API_KEY=DefaultConfig.API_KEY,
                            NOTIFY_URL=DefaultConfig.NOTIFY_URL
                            )
        return wp.getPayUrl(openid=openid, goodsPrice=wx_pay.good_price, spbill_create_ip=request.client[0], db=db)
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def _wx_refund(total_fee: str, out_refund_no: str):
    try:
        wp = WX_PayToolUtil(APP_ID=DefaultConfig.APP_ID,
                            MCH_ID=DefaultConfig.MCH_ID,
                            API_KEY=DefaultConfig.API_KEY,
                            NOTIFY_URL=DefaultConfig.NOTIFY_URL
                            )
        return wp.get_refund_url(total_fee=total_fee, refund_fee=total_fee,
                                 out_refund_no=out_refund_no)
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)


def payback(msg_str: str, db: Session):
    try:
        log.logger.info("======= 进入了回调函数========")
        success_data = """<xml><return_code><![CDATA[SUCCESS]]></return_code>
                          <return_msg><![CDATA[OK]]></return_msg></xml>"""
        fail_data = """<xml><return_code><![CDATA[FAIL]]></return_code>
                    <return_msg><![CDATA[FAIL]]></return_msg></xml>"""

        xmlmsg = xmltodict.parse(msg_str)
        req_info = xmlmsg['xml'].get('req_info')
        if req_info:  # 退款成功的xml
            return Response(content=success_data, media_type="application/xml")
        else:  # 支付成功的xml
            return_code = xmlmsg['xml']['return_code']
            result_code = xmlmsg['xml']['result_code']

            if return_code == "SUCCESS" and result_code == "SUCCESS":
                total_fee = xmlmsg['xml']['total_fee']
                out_trade_no = xmlmsg['xml']['out_trade_no']
                pay_msg = db.query(WxPayMsg).filter(WxPayMsg.out_trade_no == out_trade_no).first()
                if not pay_msg:
                    return Response(content=fail_data, media_type="application/xml")
                if total_fee == pay_msg.total_fee:
                    log.logger.info('============= 微信支付回调成功 ===============')
                    pay_msg.status = 1
                    db.commit()
                    return Response(content=success_data, media_type="application/xml")
                else:
                    log.logger.info('============= 微信支付回调失败 ===============')
                    return Response(content=fail_data, media_type="application/xml")
            else:
                log.logger.info('============= 微信支付回调失败 ===============')
                return Response(content=fail_data, media_type="application/xml")

    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def login_verify_token(token: str, db: Session):
    try:
        decode_msg = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        db_user = get_user(db=db, user_id=decode_msg['user_id'])
        data = {
            "id": db_user.id,
            'mobile': db_user.mobile,
            "token": token
        }
        return {'err_no': 0, 'err_msg': '', 'data': {'user_info': data}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()
