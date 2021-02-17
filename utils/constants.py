# 短信验证码有效期，单位：秒
SMS_CODE_REDIS_EXPIRES = 5 * 60

# 发送短信60s区间
SMS_CODE_REDIS_INTERVAL = 60

# token过期时间
TOKEN_EXPIRES = 30 * 24 * 60 * 60

# session_key 过期时间
SESSION_KEY = 15 * 60

# 暂时不收佣金
INCOME_RATE = 1

# 发件人
MAIL_SENDER = 'abc@163.com'

# 收件人
RECEIVER = 'abc@qq.com'

MAIL_USERNAME = 'abc@163.com'
MAIL_PASSWORD = 'SOVRBJTQYGPTXKWY'
MAIL_HOST = 'smtp.163.com'

WHITE_LIST = [
    '/user/login',
    '/sms/code'
]

AVATAR = ''
