import os


class Config:
    APP_ID = ''    # 小程序id
    APP_SECRET = ''
    MCH_ID = ''   # 商户号
    API_KEY = ''
    SELF_PWD = ''


class DevConfig(Config):
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    NOTIFY_URL = ''
    SELF_URL = ''
    REDIS_ENV = 'dev'
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = '6379'
    REDIS_PASSWORD = ''
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'SQLALCHEMY_DATABASE_URI',
        'mysql+pymysql://'
    )

class TestConfig(Config):
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    NOTIFY_URL = ''
    SELF_URL = ''
    REDIS_ENV = 'test'
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = '6379'
    REDIS_PASSWORD = ''
    CELERY_DB = 10
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'SQLALCHEMY_DATABASE_URI',
        'mysql+pymysql://'
    )


class ProdConfig(Config):
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    NOTIFY_URL = ''
    SELF_URL = ''
    REDIS_ENV = 'prod'
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = '6379'
    REDIS_PASSWORD = ''
    CELERY_DB = 9
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'SQLALCHEMY_DATABASE_URI',
        'mysql+pymysql://'
    )
    DEBUG = False


DefaultConfig = ProdConfig
