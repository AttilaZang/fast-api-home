import random
import re

from fastapi import APIRouter, HTTPException
from starlette.responses import FileResponse
from utils.celery_tasks import send_sms_code
from common.extensions import redis_code
from utils.constants import SMS_CODE_REDIS_EXPIRES, SMS_CODE_REDIS_INTERVAL

router = APIRouter()


def send_code(mobile: str, identity: str):
    sms_code = '%06d' % random.randint(0, 999999)
    pipe = redis_code.pipeline()
    pipe.set(f'sms_{identity}_{mobile}', sms_code, ex=SMS_CODE_REDIS_EXPIRES)
    pipe.set(f'send_flag_{identity}_{mobile}', 1, ex=SMS_CODE_REDIS_INTERVAL)  # 60s内不允许重发
    pipe.execute()

    # 用阿里云发送验证码（celery发送）
    send_sms_code.delay(mobile, sms_code)
    return {'err_no:': 0, 'err_msg': '', 'data': 'success'}


@router.get('/sms/code/')
async def sms_code(*, identity: str, mobile: str):
    """
    :param: identity: user/courier
    :param: mobile: 13088888888
    :return:
    """
    if not re.match(r'^1[3-9]\d{9}$', mobile):
        return HTTPException(status_code=400, detail='mobile is Invalid')
    flag = redis_code.get(f'send_flag_{identity}_{mobile}')
    if flag:
        return HTTPException(status_code=400, detail='request too frequently')
    return send_code(mobile=mobile, identity=identity)


@router.get('/')
def home():
    return FileResponse('static/index.html')


@router.get('/user/agreement/')
def user_agreement():
    return FileResponse('static/userAgreement.html')


@router.get('/privacy/policy/')
def privacy_policy():
    return FileResponse('static/privacyPolicy.html')


@router.get('/faq/')
def faq():
    return FileResponse('static/FAQ.html')


@router.get('/test/android/app/')
def test_android_app():
    return FileResponse('apps/test_homejoy.apk', filename='宅悦骑士测试.apk')


@router.get('/prod/android/app/')
def prod_android_app():
    return FileResponse('apps/prod_homejoy.apk', filename='宅悦骑士.apk')
