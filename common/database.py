# -*- coding: UTF-8 -*-
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from common.settings import DefaultConfig


# 初始化
engine = create_engine(
        DefaultConfig.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True
)

# 创建DBSession类型
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class NewBase(object):
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    create_time = Column(DateTime, nullable=False, default=datetime.now)
    update_time = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

# 创建基类 用于继承
Base = declarative_base()

from models import users
from models import wallet
from models import address
from models import couriers
from models import order_info
from models import coupons
from models import wx_pay_msg


Base.metadata.create_all(engine)


# 获取数据库会话
def get_db():
    try:
        db = SessionLocal()
        yield db
    except:
        db.rollback()
    finally:
        db.close()
