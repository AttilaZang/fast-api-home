from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, DateTime
from common.database import Base, NewBase


class Address(NewBase, Base):
    """用户地址"""
    __tablename__ = 'address'

    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    user_id = Column(Integer, nullable=False, comment='用户id')
    place = Column(String(64), nullable=False, comment='详细收货地址')  # 组合后的
    lng = Column(DECIMAL(10, 6), nullable=False, comment='经度')
    lat = Column(DECIMAL(10, 6), nullable=False, comment='纬度')
    addr_type = Column(String(16), comment='地址类型')  # 家/学校/公司大厦
    is_default = Column(Boolean, nullable=False, default=False, comment='默认地址')
    is_delete = Column(Boolean, nullable=False, default=False, comment='逻辑删除')
    contacts = Column(String(16), nullable=False, comment='联系人')
    mobile = Column(String(11), nullable=False, comment='联系电话')
    gender = Column(Integer, nullable=False, comment='性别')  # 0/1 -> 女士/先生
    region = Column(String(64), nullable=False, comment='地区')  # 北京市海淀区

    __mapper_args__ = {
        "order_by": update_time.desc()
    }

