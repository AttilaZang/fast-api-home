import base64
import hashlib
import re
import time
import jwt
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import func, extract, and_
from sqlalchemy.orm import Session
from common.extensions import redis_serv, redis_token, redis_code
from common.general import generate_jwt, SECRET_KEY, ALGORITHM
from common.logger import log
from common.settings import DefaultConfig
from models.couriers import Couriers
from models.order_info import OrderInfo
from models.wallet import Wallet, Bill, Capital
from schemas import courier_schema
from schemas.courier_schema import AlipayInfo, CashOut, CashOutRecord, CapitalDetail, ResetPassword, PasswordLogin, \
    FinishDelivery, StartDelivery, Transfer, CheckMsg, CourierCheck, CourierTransfer, PaymentAccount
from utils.alioss_client import AliOssClient
from utils.celery_tasks import send_notice_mail, cash_out_apply, socket_to_user
from utils.constants import AVATAR, TOKEN_EXPIRES, INCOME_RATE


def pwd2sha256(pwd):
    h = hashlib.sha256()
    h.update(bytes(pwd, encoding='utf-8'))
    return h.hexdigest()


def add_courier_redis(lng, lat, courier_id):
    redis_serv.geoadd('courier', lng, lat, f'courier_{courier_id}')


def remove_courier_redis(courier_id):
    redis_serv.zrem('courier', f'courier_{courier_id}')


def get_wallet_by_courier(db: Session, courier_id: int):
    wallet = db.query(Wallet).filter(Wallet.courier_id == courier_id).first()
    return wallet


def get_order(db: Session, order_id: int):
    db_order = db.query(OrderInfo).filter(OrderInfo.id == order_id).first()
    return db_order


def get_courier(db: Session, courier_id: int):
    db_courier = db.query(Couriers).filter(Couriers.id == courier_id).first()
    return db_courier


def get_courier_by_mobile(db: Session, mobile: str):
    db_courier = db.query(Couriers).filter(Couriers.mobile == mobile).first()
    return db_courier


def create_courier(db: Session, courier: courier_schema.CourierRegister):
    try:
        name = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', courier.mobile)
        db_courier = Couriers(mobile=courier.mobile, last_name=name, first_name=name)
        db.add(db_courier)
        db.flush()
        # 给用户创建一个钱包
        new_wallet = Wallet(courier_id=db_courier.id)
        db.add(new_wallet)
        db.commit()
        db.refresh(db_courier)
        return db_courier
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def verify_name(db: Session, courier: courier_schema.VerifyName):
    """实名认证"""
    db_courier = get_courier(db=db, courier_id=courier.courier_id)
    if not db_courier:
        raise HTTPException(400, 'courier not found')

    id_card_front = courier.id_card_front
    id_card_back = courier.id_card_back
    id_card_hand = courier.id_card_hand

    front_file_name = f"idCard/{courier.mobile}_front.jpg"
    back_file_name = f"idCard/{courier.mobile}_back.jpg"
    hand_file_name = f"idCard/{courier.mobile}_hand.jpg"

    try:
        pic_front = base64.b64decode(id_card_front)
        pic_back = base64.b64decode(id_card_back)
        pic_hand = base64.b64decode(id_card_hand)

        aoc = AliOssClient()
        url_front, _ = aoc.put_object(front_file_name, pic_front)
        url_back, _ = aoc.put_object(back_file_name, pic_back)
        url_real, _ = aoc.put_object(hand_file_name, pic_hand)

        db_courier.id_card_front = url_front
        db_courier.id_card_back = url_back
        db_courier.real_pic = url_real
        db_courier.is_auth = 1  # 待审核
        db.commit()

        # 异步发送邮件
        send_notice_mail.delay(courier.mobile)
        return {'err_no': 0, 'err_msg': '', 'data': 'success'}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def verify_status(db: Session, courier_id: int):
    """认证状态"""

    db_courier = get_courier(db=db, courier_id=courier_id)
    if not db_courier:
        log.logger.error('数据库中没有该骑手信息')
        raise HTTPException(404, 'courier not found')
    db.close()
    return {'err_no': 0, 'err_msg': '', 'data': {'is_auth': db_courier.is_auth}}


def work_status(db: Session, courier_id: int):
    """切换工作状态"""
    try:
        db_courier = get_courier(db=db, courier_id=courier_id)

        if db_courier.is_work == 0:
            db_courier.is_work = 1
            # 把该跑男加入接单池
            add_courier_redis(float(db_courier.lng), float(db_courier.lat), courier_id)
        else:
            db_courier.is_work = 0
            remove_courier_redis(db_courier.id)
        db.commit()
        return {'err_no': 0, 'err_msg': '', 'data': {'is_work': db_courier.is_work}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def courier_center(db: Session, courier_id: int):
    """骑手中心"""
    try:
        wallet = get_wallet_by_courier(db=db, courier_id=courier_id)
        if not wallet:
            return {'err_no': 0, 'err_msg': '', 'data': {'balance': 0.00}}
        return {'err_no': 0, 'err_msg': '', 'data': {'balance': wallet.balance}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def courier_account(db: Session, courier_id: int):
    """我的账户"""
    try:
        wallet = get_wallet_by_courier(db=db, courier_id=courier_id)
        cost = db.query(func.sum(OrderInfo.cost)).filter(
            OrderInfo.courier_id == courier_id,
            OrderInfo.deliver_day == str(datetime.today().date())
        ).first()  # first是聚合后的第一条
        print('我是cost--->', cost)
        account_info = {
            'balance': wallet.balance,  # 账户余额
            'today_profit': int(float(cost[0]) * INCOME_RATE) if cost[0] else 0,  # 今日收益，单位是分, 需要乘以系数
            'total_profit': wallet.total_profit,  # 总收益，单位是分
            'is_bind': wallet.is_bind
        }
        return {'err_no': 0, 'err_msg': '', 'data': {'account_info': account_info}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def courier_payment_account(payment_account: PaymentAccount, db: Session):
    try:
        db_wallet = get_wallet_by_courier(courier_id=payment_account.courier_id, db=db)
        info = {
            'alipay': db_wallet.alipay,
            'name': db_wallet.name
        }
        return {'err_no': 0, 'err_msg': '', 'data': {'payment_account': info}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def courier_add_alipay(db: Session, alipay_info: AlipayInfo):
    """添加支付宝账号"""
    try:
        wallet = get_wallet_by_courier(db=db, courier_id=alipay_info.courier_id)
        if not wallet:
            raise HTTPException(404, detail='wallet not fount')
        wallet.name = alipay_info.name
        wallet.alipay = alipay_info.account
        wallet.is_bind = True
        db.commit()
        return {'err_no': 0, 'err_msg': '', 'data': 'success'}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def courier_start_delivery(db: Session, start_delivery: StartDelivery):
    """开始配送"""

    db_order = get_order(db=db, order_id=start_delivery.order_id)
    if not db_order:
        log.logger.error('没有该订单，无法配送')
        raise HTTPException(status_code=404, detail='order not found')
    db_order.status = 1
    db.commit()
    db.close()
    return {'err_no': 0, 'err_msg': '', 'data': 'success'}


def courier_finish_delivery(db: Session, finish_delivery: FinishDelivery):
    """完成配送"""
    db_order = db.query(OrderInfo).filter(
        OrderInfo.id == finish_delivery.order_id,
        OrderInfo.status == 1
    ).first()
    db_wallet = db.query(Wallet).filter(Wallet.courier_id == finish_delivery.courier_id).first()
    if not all([db_order, db_wallet]):
        log.logger.error('没有该订单，无法完成配送')
        raise HTTPException(status_code=404, detail='order or wallet not found')

    db_order.status = 2
    db_order.deliver_time = datetime.now()
    db_order.deliver_day = datetime.today().date()
    # 更新总收益、账户余额并添加资金明细， 金额的 80%
    db_wallet.total_profit = db_wallet.total_profit + db_order.cost * INCOME_RATE
    db_wallet.balance = db_wallet.balance + db_order.cost * INCOME_RATE
    new_capital = Capital(
        courier_id=finish_delivery.courier_id,
        order_id=finish_delivery.order_id,
        income=db_order.cost * INCOME_RATE
    )
    db.add(new_capital)
    db.commit()

    # 通知用户完成配送
    send_data = {
        'from_user': f'courier_{finish_delivery.courier_id}',
        'to_user': f'user_{db_order.user_id}',
        'msg': {'accept_status': 2, 'courier_id': int(finish_delivery.courier_id),
                'order_id': finish_delivery.order_id}  # 完成配送
    }
    # 用celery 发送socket 消息
    url = DefaultConfig.SELF_URL + '/room/whisper/'
    socket_to_user.delay(url, send_data)
    db.close()
    return {'err_no': 0, 'err_msg': '', 'data': 'success'}


def courier_order_list(db: Session, courier_id: int, status: int = None):
    """订单列表"""
    try:
        db_order = db.query(OrderInfo).filter(
            OrderInfo.courier_id == courier_id,
            OrderInfo.courier_delete == 0,
            OrderInfo.status == status
        ).all()

        # 已完成的订单会有送单时长
        diff = True if status == 2 else False

        order_list = []
        for order in db_order:
            order_list.append({
                "id": order.id,
                'cost': order.cost,  # 单位是分
                "get_addr": order.get_addr,
                "recv_addr": order.recv_addr,
                "take_info": order.take_info,
                "contacts": order.contacts,
                "mobile": order.mobile,
                "diff_time": str(order.deliver_time - order.create_time) if diff else ''
            })

        return {'err_no': 0, 'err_msg': '', 'data': {'order_list': order_list}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def courier_order_info(db: Session, order_id: int):
    """订单详情"""

    db_order = get_order(db=db, order_id=order_id)
    if not db_order:
        log.logger.error('没有该订单，无法查看详情')
        raise HTTPException(status_code=404, detail='order not found')

    order_info = {
        "id": db_order.id,
        "get_addr": db_order.get_addr,
        "recv_addr": db_order.recv_addr,
        "take_info": db_order.take_info,
        "contacts": db_order.contacts,
        "mobile": db_order.mobile,
        "weight": db_order.weight,
        "cost": db_order.cost,  # 单位是分
        "order_num": db_order.order_num,
        "create_time": db_order.create_time
    }
    db.close()
    return {'err_no': 0, 'err_msg': '', 'data': {'order_info': order_info}}


def cash_out(db: Session, cash_out: CashOut):
    """提现，暂时是手动提现"""

    wallet = db.query(Wallet).filter(Wallet.courier_id == cash_out.courier_id).first()
    if not wallet:
        log.logger.error('该骑手没有钱包，无法提现')
        raise HTTPException(400, detail='wallet not found')

    if cash_out.balance > wallet.balance:
        log.logger.error('该骑手余额不足，无法提现')
        raise HTTPException(400, detail='余额不足')

    bill_num = str(time.time() * 1000).split('.')[0] + str(cash_out.courier_id)
    db_bill = Bill(courier_id=cash_out.courier_id, bill_num=bill_num, amount=cash_out.balance)
    db.add(db_bill)
    # 减余额
    wallet.balance -= cash_out.balance
    db.commit()

    # 异步发送邮件
    cash_out_apply.delay(cash_out.courier_id)
    db.close()
    return {'err_no': 0, 'err_msg': '', 'data': 'success'}


def cash_out_record(db: Session, cash_out_record: CashOutRecord):
    """提现记录"""
    try:
        bill = db.query(Bill).filter(
            Bill.courier_id == cash_out_record.courier_id
        ).all()

        ret = []
        sum_amount = 0
        for b in bill:
            year = b.update_time.year  # int, 2020
            month = b.update_time.month  # int, 6
            if year == cash_out_record.year and month == cash_out_record.month:
                ret.append({
                    'id': b.id,
                    'amount': b.amount,
                    'status': b.status,  # 0/1 -> 等待打款/已完成
                    'update_time': b.update_time
                })

            if b.status == 1:
                sum_amount += b.amount

        return {'err_no': 0, 'err_msg': '', 'data': {'list': ret, 'sum_amount': sum_amount}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def courier_capital_detail(db: Session, capital_detail: CapitalDetail):
    """资金明细"""
    try:
        db_capital = db.query(Capital).filter(and_(
            Capital.courier_id == capital_detail.courier_id,
            extract('year', Capital.create_time) == capital_detail.year,
            extract('month', Capital.create_time) == capital_detail.month
        )).all()

        ret = []
        sum_income = 0
        for capital in db_capital:
            # 本月收入累加
            sum_income += capital.income
            ret.append({
                'id': capital.id,
                'income': capital.income,
                'create_time': capital.create_time
            })

        return {'err_no': 0, 'err_msg': '', 'data': {'list': ret, 'sum_income': sum_income}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def courier_accept_order(db: Session, courier_id: int, order_id: int):
    """骑手接收订单"""

    order_ret = redis_serv.delete(f'order_id_{order_id}')
    if order_ret == 0:
        return {'err_no': 0, 'err_msg': '', 'data': {'status': 0}}  # 代表此单已被抢

    order_info = get_order(db=db, order_id=order_id)
    if not order_info:
        log.logger.error('没有该订单，无法接单')
        raise HTTPException(404, detail='order not found')

    user_id = order_info.user_id
    order_info.courier_id = courier_id
    # 给用户发送接单通知
    send_data = {
        'from_user': f'courier_{courier_id}',
        'to_user': f'user_{user_id}',
        'msg': {'accept_status': 1, 'courier_id': int(courier_id), 'order_id': order_info.id}  # 配送中
    }
    db.commit()
    # 用celery 给用户发消息
    url = DefaultConfig.SELF_URL + '/room/whisper/'
    socket_to_user.delay(url, send_data)
    db.close()
    return {'err_no': 0, 'err_msg': '', 'data': {'status': 1}}  # 1代表抢到了


def courier_info(db: Session, courier_id: int):
    """骑手信息"""
    try:
        db_courier = get_courier(db=db, courier_id=courier_id)
        courier_order = db.query(OrderInfo).filter(
            OrderInfo.courier_id == courier_id,
            OrderInfo.status == 2
        ).all()
        sum_score = 0
        for order in courier_order:
            sum_score += order.score

        evaluation = 0 if len(courier_order) == 0 else int(20 * sum_score / len(courier_order))
        ret = {
            'name': f'{db_courier.last_name}师傅',
            'mobile': db_courier.mobile,
            'order_num': f'{len(courier_order)}单',
            'evaluation': f'{evaluation}%好评'
        }
        return {'err_no': 0, 'err_msg': '', 'data': {'courier_info': ret}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def reset_password(reset_pwd: ResetPassword, db: Session):
    """重置密码"""
    if reset_pwd.pwd != reset_pwd.repwd:
        log.logger.error('两次密码不一致')
        raise HTTPException(400, detail='两次密码不一致')
    elif re.match("^(?:(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])).*$", reset_pwd.pwd) == None:
        log.logger.error('密码缺少【大写，小写，数字】中的一种或多种')
        raise HTTPException(400, detail='密码必须包含大小写字母和数字')
    else:
        pwd_result = pwd2sha256(reset_pwd.pwd)
        db_courier = get_courier(courier_id=reset_pwd.courier_id, db=db)
        if not db_courier:
            log.logger.error('没有该骑手信息')
            raise HTTPException(404, 'courier not found')
        db_courier.pwd = pwd_result
        db.commit()
        db.close()
    return {'err_no': 0, 'err_msg': '', 'data': 'success'}


def courier_login(courier: courier_schema.CourierRegister, db: Session):
    """骑手登录"""
    v_code = redis_code.get(f'sms_courier_{courier.mobile}')

    if not v_code:
        log.logger.error('验证码过期')
        raise HTTPException(status_code=400, detail='sms_code has expired')
    elif courier.sms_code != int(v_code.decode()):
        log.logger.error('验证码不合法')
        raise HTTPException(status_code=400, detail='sms_code is invalid!')

    try:
        db_courier = get_courier_by_mobile(db=db, mobile=courier.mobile)
        if db_courier:
            token = generate_jwt(courier_id=db_courier.id, mobile=db_courier.mobile)
            redis_token.set(token, 1, ex=TOKEN_EXPIRES)
            data = {
                "id": db_courier.id,
                "name": db_courier.last_name + db_courier.first_name,
                "mobile": db_courier.mobile,
                "avatar": AVATAR,
                "token": token
            }
            return {'err_no': 0, 'err_msg': '', 'data': {'courier_info': data}}
        courier_msg = create_courier(db=db, courier=courier)
        token = generate_jwt(courier_id=courier_msg.id, mobile=courier_msg.mobile)
        redis_token.set(token, 1, ex=TOKEN_EXPIRES)
        data = {
            "id": courier_msg.id,
            "name": courier_msg.last_name + courier_msg.first_name,
            "mobile": courier_msg.mobile,
            "avatar": AVATAR,
            "token": token
        }
        return {'err_no': 0, 'err_msg': '', 'data': {'courier_info': data}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def courier_logout(token: str, db: Session):
    ret = redis_token.delete(token)
    if ret == 0:
        raise HTTPException(404, detail='token not found')
    token_msg = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    courier_id = token_msg.get('courier_id')
    # 无论什么工作状态都改成休息中
    db_courier = get_courier(db=db, courier_id=courier_id)
    db_courier.is_work = 0
    # 从redis 中删除跑男信息
    remove_courier_redis(courier_id)
    db.commit()
    db.close()
    return {'err_no': 0, 'err_msg': '', 'data': 'success'}


def password_login(pwd_login: PasswordLogin, db: Session):
    """骑手密码登录"""
    db_courier = get_courier_by_mobile(mobile=pwd_login.mobile, db=db)
    if not db_courier:
        log.logger.error('骑手不存在')
        raise HTTPException(404, 'courier not found')

    pwd_result = pwd2sha256(pwd_login.pwd)
    if pwd_result == db_courier.pwd:
        token = generate_jwt(courier_id=db_courier.id, mobile=db_courier.mobile)
        redis_token.set(token, 1, ex=TOKEN_EXPIRES)
        data = {
            "id": db_courier.id,
            "name": db_courier.last_name + db_courier.first_name,
            "mobile": db_courier.mobile,
            "avatar": AVATAR,
            "token": token
        }
        db.close()
        return {'err_no': 0, 'err_msg': '', 'data': {'courier_info': data}}
    else:
        log.logger.error('登录密码错误')
        raise HTTPException(401, detail='密码错误')


def login_verify_token(token: str, db: Session):
    try:
        decode_msg = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        db_courier = get_courier(db=db, courier_id=decode_msg['courier_id'])
        data = {
            "id": db_courier.id,
            "name": db_courier.last_name + db_courier.first_name,
            "mobile": db_courier.mobile,
            "avatar": AVATAR,
            "token": token
        }
        return {'err_no': 0, 'err_msg': '', 'data': {'courier_info': data}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def service_area_edit(area: courier_schema.ServiceArea, db: Session):
    """新增/修改服务地址"""
    db_courier = get_courier(courier_id=area.courier_id, db=db)
    if not db_courier:
        log.logger.error('该骑手不存在')
        raise HTTPException(404, detail='courier not found')
    try:
        db_courier.lng = area.lng
        db_courier.lat = area.lat
        db_courier.service_area = area.service_area
        db.commit()
        db.refresh(db_courier)
        area = {
            'id': db_courier.id,
            'service_area': db_courier.service_area,
            'lng': db_courier.lng,
            'lat': db_courier.lat
        }
        return {'err_no': 0, 'err_msg': '', 'data': {'service_area': area}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def service_area_msg(courier_id: int, db: Session):
    """服务地址列表"""

    db_courier = get_courier(courier_id=courier_id, db=db)
    if not db_courier:
        log.logger.error('该骑手不存在')
        raise HTTPException(404, detail='courier not found')
    try:
        area = {
            'id': db_courier.id,
            'service_area': db_courier.service_area,
            'lng': db_courier.lng,
            'lat': db_courier.lat
        }
        return {'err_no': 0, 'err_msg': '', 'data': {'service_area': area}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def transfer(transfer_msg: Transfer, db: Session):
    """
    给骑手转账
    1. 减去 Wallet 表中 balance
    2. 修改 Bill 表中 status
    """
    if pwd2sha256(transfer_msg.self_pwd) != DefaultConfig.SELF_PWD:
        raise HTTPException(401, detail='管理员密码错误')
    try:
        db_bill = db.query(Bill).filter(Bill.id == transfer_msg.bill_id).first()
        db_bill.status = 1
        db.commit()
        return {'err_no': 0, 'err_msg': '', 'data': 'success'}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def pass_check(check_msg: CheckMsg, db: Session):
    """
    通过骑手提交的实名请求
    1. 修改courier 表中的 is_auth 与 name 字段
    """
    if pwd2sha256(check_msg.self_pwd) != DefaultConfig.SELF_PWD:
        raise HTTPException(401, detail='管理员密码错误')
    try:
        db_courier = get_courier(courier_id=check_msg.courier_id, db=db)
        db_courier.last_name = check_msg.last_name
        db_courier.first_name = check_msg.first_name
        db_courier.is_auth = 2
        db.commit()
        return {'err_no': 0, 'err_msg': '', 'data': 'success'}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def check_list(courier_check: CourierCheck, db: Session):
    """
    找到courier 表中所有提交实名认证审核的人员
    """
    if pwd2sha256(courier_check.self_pwd) != DefaultConfig.SELF_PWD:
        raise HTTPException(401, detail='管理员密码错误')
    try:
        db_couriers = db.query(Couriers).filter(Couriers.is_auth == 1).all()
        ret = []
        for courier in db_couriers:
            ret.append({
                'courier_id': courier.id,
                'id_card_front': courier.id_card_front,
                'id_card_back': courier.id_card_back,
                'real_pic': courier.real_pic,
                'last_name': courier.last_name,
                'first_name': courier.first_name
            })
        return {'err_no': 0, 'err_msg': '', 'data': {'list': ret}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


def transfer_list(courier_transfer: CourierTransfer, db: Session):
    """
    找到所有申请提现的记录
    bill 表中status=0 的所有记录
    """
    if pwd2sha256(courier_transfer.self_pwd) != DefaultConfig.SELF_PWD:
        raise HTTPException(401, detail='管理员密码错误')
    try:
        db_bills = db.query(Bill).filter(Bill.status == 0).all()
        db_wallet_dict = {w.courier_id: w.alipay for w in db.query(Wallet).all()}
        ret = []
        for bill in db_bills:
            ret.append({
                'bill_id': bill.id,
                'courier_id': bill.courier_id,
                'amount': bill.amount,
                'alipay': db_wallet_dict[bill.courier_id]
            })
        return {'err_no': 0, 'err_msg': '', 'data': {'list': ret}}
    except Exception as e:
        log.logger.error(e)
        raise HTTPException(500, detail=e)
    finally:
        db.close()


