import time

import requests
from celery import Celery

from utils.email_config import SendEmail
from .cloud_sms import send_code

celery = Celery('celery_task')
celery.config_from_object('utils.celery_config')


@celery.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):
    send_code(mobile, sms_code)


@celery.task(name='send_notice_mail')
def send_notice_mail(mobile):
    temp_send = SendEmail(f'{mobile} 提交实名认证，请及时处理!!!')
    temp_send.send_email()


@celery.task(name='cash_out_apply')
def cash_out_apply(courier_id):
    temp_send = SendEmail(f'跑男【{courier_id}】提交提现申请，请及时处理!!!')
    temp_send.send_email()


@celery.task(name='socket_to_user')
def socket_to_user(url, send_data):
    for i in range(100):
        if i == 30 or i == 60:
            time.sleep(1)
        res = requests.post(url, json=send_data)
        if res.status_code == 200:
            break
        # 骑手socket 存在断开重连的情况
        new_send_data = send_data
        new_send_data['from_user'] = new_send_data['to_user']
        res = requests.post(url, json=new_send_data)
        if res.status_code == 200:
            break

