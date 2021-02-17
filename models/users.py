# -*- coding: UTF-8 -*-

from common.database import Base, NewBase
from sqlalchemy import Column, Integer, String, Boolean


class Users(NewBase, Base):
    """用户"""
    __tablename__ = 'users'

    mobile = Column(String(11), unique=True, index=True, comment='手机号')
    openid = Column(String(64), unique=True, index=True, comment='用户唯一标识')
    code = Column(String(16), unique=True, comment='唯一邀请码')
    inviter = Column(Integer, index=True, comment='邀请人')
    is_active = Column(Boolean, default=True)


