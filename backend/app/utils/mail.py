#========== utils/mail.py ==========
from flask_mail import Message
from app.extensions import mail

class MailService:
    @classmethod
    def send_verification(cls, email, code):
        """发送验证码邮件"""
        msg = Message(
            subject="验证码通知",
            recipients=[email],
            body=f"您的验证码是：{code}，30分钟内有效"
        )
        mail.send(msg)
