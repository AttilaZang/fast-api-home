from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, DECIMAL, Float, Date
from common.database import Base, NewBase


class OrderInfo(NewBase, Base):
    """订单信息"""
    __tablename__ = 'order_info'

    create_time = Column(DateTime, default=datetime.now)
    deliver_time = Column(DateTime)  # 送达时间
    deliver_day = Column(Date, comment='送达当天日期')  # 后面查询当天收益用
    weight = Column(String(16), nullable=False, comment='商品重量')  # 1~10kg
    cost = Column(Integer, nullable=False, comment='费用')  # 订单原价  单位是分
    order_num = Column(String(32), nullable=False, comment='订单编号')  # 时间戳 * 1000 + user_id + courier_id
    user_id = Column(Integer, nullable=False, index=True, comment='用户id')
    courier_id = Column(Integer, nullable=False, default=-1, index=True, comment='配送员id')  # -1代表没有人接单
    recv_addr = Column(String(128), nullable=False, comment='具体收货地址')  # 1号楼1单元101室
    get_addr = Column(String(128), nullable=False, comment='取货地址')  # 北京市朝阳区国贸3期
    contacts = Column(String(16), nullable=False, comment='订单联系人姓名')
    mobile = Column(String(16), nullable=False, comment='订单联系人手机号')
    take_info = Column(String(256), nullable=False, comment='取货信息')  # 中通快递，尾号1234，姓名臧先生/1号丰巢柜，取件码6789
    out_trade_no = Column(String(32), nullable=False, comment='支付商户单号')  # 用户支付完由商户生成的支付单号
    status = Column(Integer, nullable=False, default=0, comment='订单状态')    # /0代取单(待接单)/1进行中/2已完成
    comment = Column(Text, nullable=False, default="", comment="评价信息")
    score = Column(Integer, nullable=False, default=5, comment='满意度评分')
    is_commented = Column(Boolean, nullable=False, default=False, comment='是否评价了')
    is_anonymous = Column(Boolean, nullable=False, default=False, comment='是否匿名评价')
    user_delete = Column(Boolean, nullable=False, default=False, comment='用户是否删除')
    courier_delete = Column(Boolean, nullable=False, default=False, comment='配送员是否删除')
    coupons_id = Column(Integer, nullable=False, default=-1, comment='优惠券id')  # -1 代表没有使用优惠券


    __mapper_args__ = {
        "order_by": create_time.desc()
    }
