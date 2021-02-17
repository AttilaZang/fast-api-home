
from sqlalchemy import Column, Integer, String
from common.database import Base, NewBase


class WxPayMsg(NewBase, Base):
    """微信支付消息"""
    __tablename__ = 'wx_pay_msg'

    out_trade_no = Column(String(32), nullable=False, index=True, comment='商户单号')
    sign = Column(String(32), nullable=False, comment='支付签名')
    status = Column(Integer, nullable=False, default=0, comment='回调状态')  # 0->失败, 1->成功
    total_fee = Column(String(16), nullable=False, comment='支付的总金额')  # 因为回调函数给的是字符串


