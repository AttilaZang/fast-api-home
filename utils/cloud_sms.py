from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

accessKeyId = ''
accessSecret = ''


def send_code(mibile, code):
    client = AcsClient(accessKeyId, accessSecret, 'cn-hangzhou')

    request = CommonRequest()
    request.set_accept_format('json')
    request.set_domain('dysmsapi.aliyuncs.com')
    request.set_method('POST')
    request.set_protocol_type('https')
    request.set_version('2017-05-25')
    request.set_action_name('SendSms')

    request.add_query_param('RegionId', "cn-hangzhou")
    request.add_query_param('PhoneNumbers', mibile)
    request.add_query_param('SignName', "宅悦")
    request.add_query_param('TemplateCode', "SMS_194640637")
    request.add_query_param('TemplateParam', "{\"code\": %s}" % code)

    response = client.do_action(request)
    print(str(response, encoding='utf-8'))


if __name__ == '__main__':
    send_code(13088888888, 666666)
