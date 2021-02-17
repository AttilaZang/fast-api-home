# -*- coding:utf-8 -*-
import os
import requests
import hashlib
import xmltodict
import time
import random
import string
from random import Random
from fastapi import HTTPException
from sqlalchemy.orm import Session
from common.settings import DefaultConfig
from models.wx_pay_msg import WxPayMsg


class WX_PayToolUtil():
    """ 微信支付工具 """

    def __init__(self, APP_ID, MCH_ID, API_KEY, NOTIFY_URL):
        self._APP_ID = APP_ID  # 小程序ID
        self._MCH_ID = MCH_ID  # # 商户号
        self._API_KEY = API_KEY
        self._NOTIFY_URL = NOTIFY_URL  # 异步通知
        self._UFDODER_URL = "https://api.mch.weixin.qq.com/pay/unifiedorder"  # 接口链接
        self._UNIFIED_ORDER_URL = 'https://api.mch.weixin.qq.com/secapi/pay/refund'

    def generate_sign(self, param):
        '''生成签名'''
        stringA = ''
        ks = sorted(param.keys())
        # 参数排序
        for k in ks:
            stringA += (k + '=' + param[k] + '&')
        # 拼接商户KEY
        stringSignTemp = stringA + "key=" + self._API_KEY
        # md5加密,也可以用其他方式
        hash_md5 = hashlib.md5(stringSignTemp.encode('utf8'))
        sign = hash_md5.hexdigest().upper()
        return sign

    # 自定义订单流水号
    def random_num(self, randomlenth=10):
        str = ''
        chars = '1234567890'
        length = len(chars) - 1
        random = Random()
        for i in range(randomlenth):
            str += chars[random.randint(0, length)]
        str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
        return str_time + str

    def getPayUrl(self, openid, goodsPrice, spbill_create_ip, db: Session):
        """向微信支付端发出请求，获取url"""

        nonce_str = ''.join(random.sample(string.ascii_letters + string.digits, 30))  # 生成随机字符串，小于32位
        params = {
            'appid': self._APP_ID,  # 小程序ID
            'mch_id': self._MCH_ID,  # 商户号
            'nonce_str': nonce_str,  # 随机字符串
            "body": '宅悦',  # 支付说明
            'out_trade_no': self.random_num(10),  # 生成的订单号
            'total_fee': str(goodsPrice),  # 标价金额，单位为`分`
            'spbill_create_ip': spbill_create_ip,  # 小程序不能获取客户ip，web用socekt实现
            'notify_url': self._NOTIFY_URL,
            'trade_type': "JSAPI",  # 支付类型
            "openid": openid,  # 用户id
        }
        # 生成签名
        params['sign'] = self.generate_sign(params)

        # python3一种写法
        param = {'root': params}
        xml = xmltodict.unparse(param)
        response = requests.post(self._UFDODER_URL, data=xml.encode('utf-8'), headers={'Content-Type': 'text/xml'})
        response.encoding = response.apparent_encoding  # 解析乱码
        # xml 2 dict
        msg = response.text
        xmlmsg = xmltodict.parse(msg)

        # 4. 获取prepay_id
        if xmlmsg['xml']['return_code'] == 'SUCCESS':
            if xmlmsg['xml']['result_code'] == 'SUCCESS':
                # 支付信息入库
                wx_pay_msg = WxPayMsg(
                    out_trade_no=params['out_trade_no'],
                    sign=params['sign'],
                    total_fee=params['total_fee']
                )
                db.add(wx_pay_msg)
                db.commit()
                db.close()

                prepay_id = xmlmsg['xml']['prepay_id']
                timeStamp = str(int(time.time()))
                data = {
                    "appId": self._APP_ID,
                    "nonceStr": nonce_str,
                    "package": "prepay_id=" + prepay_id,
                    "signType": 'MD5',
                    "timeStamp": timeStamp,

                }
                # 6. paySign签名
                paySign = self.generate_sign(data)
                data["paySign"] = paySign  # 加入签名
                data["out_trade_no"] = params['out_trade_no']
                # 7. 传给前端的签名后的参数
                return {'err_no:': 0, 'err_msg': '', 'data': {'pay_params': data}}


    def get_refund_url(self, total_fee, refund_fee, out_refund_no):
        nonce_str = ''.join(random.sample(string.ascii_letters + string.digits, 30))  # 生成随机字符串，小于32位
        params = {
            'appid': self._APP_ID,
            'mch_id': self._MCH_ID,
            'sign_type': 'MD5',
            'out_trade_no': out_refund_no,  # 商户订单号
            'out_refund_no': self.random_num(10),
            'total_fee': str(total_fee),
            'refund_fee': str(refund_fee),
            'notify_url': self._NOTIFY_URL,
            'nonce_str': nonce_str,
        }
        params['sign'] = self.generate_sign(params)
        import xmltodict
        data = xmltodict.unparse({'xml': params}, pretty=True, full_document=False).encode('utf-8')
        headers = {'Content-Type': 'application/xml'}
        ssh_keys_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'wx_ssh_keys')
        wx_apiclient_cert = os.path.join(ssh_keys_path, "wx_apiclient_cert.pem")
        wx_apiclient_key = os.path.join(ssh_keys_path, "wx_apiclient_key.pem")
        response = requests.post(self._UNIFIED_ORDER_URL, data=data, headers=headers,
                            cert=(wx_apiclient_cert, wx_apiclient_key), verify=True)  # 退款需要证书
        response.encoding = response.apparent_encoding  # 解析乱码
        msg = response.text
        xmlmsg = xmltodict.parse(msg)

        if xmlmsg['xml']['return_code'] == 'SUCCESS' and xmlmsg['xml']['result_code'] == 'SUCCESS':
            return {'err_no:': 0, 'err_msg': '', 'data': 'success'}
        else:
            print('退款失败', xmlmsg['xml'])
            raise HTTPException(500, detail='退款失败')



if __name__ == '__main__':
    # print(random_num(10))
    wx_p = WX_PayToolUtil(
        APP_ID=DefaultConfig.APP_ID,
        MCH_ID=DefaultConfig.MCH_ID,
        API_KEY=DefaultConfig.API_KEY,
        NOTIFY_URL=DefaultConfig.NOTIFY_URL)

    # ret = wx_p.getPayUrl(orderid='202006191131163871541180', openid='o5HRe5c8hQW9wDZOtI6Be6uMw7Y8', goodsPrice=1, spbill_create_ip='127.0.0.1')
    # print('我是ret >>>>', ret)

    ret = wx_p.get_refund_url(total_fee=100, refund_fee=100, out_refund_no='202007171557000518580375')
    print('我是ret >>>>', ret)



