import requests
from fastapi import HTTPException

from common.logger import log
from common.settings import DefaultConfig


def getOpenId(js_code):
    url = f'https://api.weixin.qq.com/sns/jscode2session?appid={DefaultConfig.APP_ID}&secret={DefaultConfig.APP_SECRET}&js_code={js_code}&grant_type=authorization_code'
    ret = requests.get(url=url)
    if ret.status_code != 200:
        raise HTTPException(500, detail='获取openid失败')
    ret_dict = ret.json()
    log.logger.info(ret_dict)
    openid = ret_dict.get('openid')
    session_key = ret_dict.get('session_key')
    return openid, session_key


class OpenidUtils:
    def __init__(self, jscode):
        self.url = 'https://api.weixin.qq.com/sns/jscode2session'
        self.appid = DefaultConfig.APP_ID
        self.secret = DefaultConfig.APP_SECRET
        self.jscode = jscode

    def get_openid_sessionkey(self):
        url = f'{self.url}?appid={self.appid}&secret={self.secret}&js_code={self.jscode}&grant_type=authorization_code'
        ret = requests.get(url)
        openid = ret.json()['openid']
        session_key = ret.json()['session_key']
        return openid, session_key


if __name__ == '__main__':
    """{'session_key': '0Cs/xaShjWkvfoRzu5/QZg==', 'openid': 'o5HRe5RBXMY56Dr9DZvOnFGFSA4M'}"""
    getOpenId(js_code='0618ALRj0jjQms1mD6Pj0iwGRj08ALRS')
