# -*- coding: utf-8 -*-
# @Author  : attilazang
# @File    : new_mail.py
# @Software: PyCharm
# @description : XXX


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


class SendEmail:

    def __init__(self, content):

        # 第三方 SMTP 服务
        self._smtp_host = "smtp.163.com"  # 设置 服务器
        self._smtp_port = 465  # 设置 端口

        self.frm = 'abc@163.com'
        self.pwd = 'SOVRBJTQYGPTXKWY'
        self.to = 'abc@qq.com'
        self.email_title = 'Home-Joy'
        # self.email_content = f'{mobile} 提交实名认证，请及时处理!!!'
        self.email_content = content

    def send_email(self):
        multi_part = MIMEMultipart()
        multi_part['From'] = self.frm
        multi_part['To'] = self.to
        multi_part['Subject'] = Header(self.email_title, "utf-8")

        # 添加 邮件 内容
        msg = self.email_content
        email_body = MIMEText(msg, 'plain', 'utf-8')
        multi_part.attach(email_body)

        # ssl 协议安全发送
        smtp_server = smtplib.SMTP_SSL(host=self._smtp_host, port=self._smtp_port)
        try:
            smtp_server.login(self.frm, self.pwd)
            smtp_server.sendmail(self.frm, self.to, multi_part.as_string())
        except smtplib.SMTPException as e:
            print("send fail", e)
        else:
            print("send success")
        finally:
            try:
                smtp_server.quit()
            except smtplib.SMTPException:
                print("quit fail")
            else:
                print("quit success")


if __name__ == '__main__':
    temp_send = SendEmail(13088888888)
    temp_send.send_email()
