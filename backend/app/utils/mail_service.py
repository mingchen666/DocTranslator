# services/email_service.py
from flask_mail import Message
from app.extensions import mail

class EmailService:
    @staticmethod
    def send_verification_code(email, code):
        msg = Message("验证码邮件", recipients=[email])
        msg.body = f"您的验证码是：{code}，有效期10分钟"
        mail.send(msg)
