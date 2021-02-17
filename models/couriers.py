
from sqlalchemy import Column, Integer, String, Boolean, DECIMAL
from common.database import Base, NewBase


class Couriers(NewBase, Base):
    """配送员"""
    __tablename__ = 'couriers'

    mobile = Column(String(11), unique=True, index=True, comment='手机号')
    id_card_front = Column(String(256), nullable=False, default='', comment='身份证正面')  # 存链接， 图片存到oss中
    id_card_back = Column(String(256), nullable=False, default='', comment='身份证背面')
    real_pic = Column(String(256), nullable=False, default='', comment='本人照片')
    last_name = Column(String(16), nullable=False, default='未认证', comment='真实姓')
    first_name = Column(String(16), nullable=False, default='未认证', comment='真实名')
    is_auth = Column(Integer, nullable=False, default=0, comment='实名认证')  # 0/1/2 -> /为上传/待审核/已认证
    is_work = Column(Boolean, nullable=False, default=False, comment='是否接单')
    service_area = Column(String(64), comment='服务地址')
    lng = Column(DECIMAL(10, 6), comment='经度')
    lat = Column(DECIMAL(10, 6), comment='纬度')
    pwd = Column(String(64), comment='密码')



