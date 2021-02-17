
import redis
from common.settings import DefaultConfig


if DefaultConfig.REDIS_ENV != "prod":
    serv_pool = redis.ConnectionPool(host=DefaultConfig.REDIS_HOST, port=DefaultConfig.REDIS_PORT,
                                     password=DefaultConfig.REDIS_PASSWORD, db=15)
    cust_pool = redis.ConnectionPool(host=DefaultConfig.REDIS_HOST, port=DefaultConfig.REDIS_PORT,
                                     password=DefaultConfig.REDIS_PASSWORD, db=14)
    code_pool = redis.ConnectionPool(host=DefaultConfig.REDIS_HOST, port=DefaultConfig.REDIS_PORT,
                                     password=DefaultConfig.REDIS_PASSWORD, db=13)
    order_pool = redis.ConnectionPool(host=DefaultConfig.REDIS_HOST, port=DefaultConfig.REDIS_PORT,
                                      password=DefaultConfig.REDIS_PASSWORD, db=12)
    token_pool = redis.ConnectionPool(host=DefaultConfig.REDIS_HOST, port=DefaultConfig.REDIS_PORT,
                                      password=DefaultConfig.REDIS_PASSWORD, db=11)
    redis_serv = redis.Redis(connection_pool=serv_pool)
    redis_cust = redis.Redis(connection_pool=cust_pool)
    redis_code = redis.Redis(connection_pool=code_pool)
    redis_order = redis.Redis(connection_pool=order_pool)
    redis_token = redis.Redis(connection_pool=token_pool)

else:
    serv_pool = redis.ConnectionPool(host=DefaultConfig.REDIS_HOST, port=DefaultConfig.REDIS_PORT,
                                     password=DefaultConfig.REDIS_PASSWORD, db=15)
    cust_pool = redis.ConnectionPool(host=DefaultConfig.REDIS_HOST, port=DefaultConfig.REDIS_PORT,
                                     password=DefaultConfig.REDIS_PASSWORD, db=14)
    code_pool = redis.ConnectionPool(host=DefaultConfig.REDIS_HOST, port=DefaultConfig.REDIS_PORT,
                                     password=DefaultConfig.REDIS_PASSWORD, db=13)
    order_pool = redis.ConnectionPool(host=DefaultConfig.REDIS_HOST, port=DefaultConfig.REDIS_PORT,
                                      password=DefaultConfig.REDIS_PASSWORD, db=12)
    token_pool = redis.ConnectionPool(host=DefaultConfig.REDIS_HOST, port=DefaultConfig.REDIS_PORT,
                                      password=DefaultConfig.REDIS_PASSWORD, db=11)
    redis_serv = redis.Redis(connection_pool=serv_pool)
    redis_cust = redis.Redis(connection_pool=cust_pool)
    redis_code = redis.Redis(connection_pool=code_pool)
    redis_order = redis.Redis(connection_pool=order_pool)
    redis_token = redis.Redis(connection_pool=token_pool)


