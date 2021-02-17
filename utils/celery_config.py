from common.settings import DefaultConfig


# 设置时区
CELERY_TIMEZONE = 'Asia/Shanghai'

# 启动时区设置
CELERY_ENABLE_UTC = True

# 并发的worker数量，默认服务器核数， 也是命令行-c指定的数目
CELERYD_CONCURRENCY = 4

# celery worker每次去redis取任务的数量，默认值就是4
CELERYD_PREFETCH_MULTIPLIER = 4

# 每个worker执行了多少次任务后就会死掉，避免内存泄漏
CELERYD_MAX_TASKS_PER_CHILD = 200

# 任务队列地址
BROKER_URL = f'redis://:{DefaultConfig.REDIS_PASSWORD}@{DefaultConfig.REDIS_HOST}:{DefaultConfig.REDIS_PORT}/{DefaultConfig.CELERY_DB}'

# celery任务执行结果的超时时间
CELERY_TASK_RESULT_EXPIRES = 2 * 60

# 单个任务的运行时间限制，否则会被杀死
CELERYD_TASK_TIME_LIMIT = 60

# 关闭限速
CELERY_DISABLE_RATE_LIMITS = True


