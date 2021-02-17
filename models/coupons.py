
from sqlalchemy import Column, Integer, String, DateTime
from common.database import Base, NewBase


class Coupons(NewBase, Base):
    """优惠券"""
    __tablename__ = 'coupons'

    user_id = Column(Integer, nullable=False, index=True, comment='用户id')
    coupon_amount = Column(Integer, nullable=False, comment='优惠券金额')  # 单位是分
    coupon_type = Column(String(16), nullable=False, comment='优惠券类型')  # 1~10kg
    expiration_time = Column(DateTime, nullable=False, index=True, comment='过期时间')
    is_use = Column(Integer, nullable=False, default=0, comment='是否使用')  # 0/1 -> 未使用/使用

