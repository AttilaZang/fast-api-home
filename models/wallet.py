from datetime import datetime
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Boolean
from common.database import Base, NewBase


class Wallet(NewBase, Base):
    """钱包"""
    __tablename__ = 'wallet'

    courier_id = Column(Integer, nullable=False, index=True, comment='配送员id')
    balance = Column(Integer, default=0, comment='账户余额')  # 单位是分
    is_bind = Column(Boolean, nullable=False, default=False, comment='是否绑定支付宝账号')
    alipay = Column(String(32), nullable=False, default="", comment='支付宝账号')
    name = Column(String(16), nullable=False, default="", comment='收款人姓名')
    total_profit = Column(DECIMAL(10, 2), default=0, comment='总收益')


class Bill(NewBase, Base):
    """账单"""
    __tablename__ = 'bill'

    create_time = Column(DateTime, nullable=False, default=datetime.now)
    courier_id = Column(Integer, nullable=False, index=True, comment='配送员id')
    bill_num = Column(String(32), nullable=False, comment='流水号')  # unix 时间戳 * 1000+ courier_id
    amount = Column(Integer, nullable=False, comment='提取金额')  # 单位是分
    status = Column(Integer, nullable=False, default=0, comment='提现状态')   # 0/1 -> 等待打款/已完成

    __mapper_args__ = {
        "order_by": create_time.desc()
    }


class Capital(NewBase, Base):
    """资金"""
    __tablename__ = 'capital'
    courier_id = Column(Integer, nullable=False, index=True, comment='配送员id')
    order_id = Column(Integer, nullable=False, comment='订单id')
    income = Column(Integer, nullable=False, comment='跑腿收入')  # 单位是分