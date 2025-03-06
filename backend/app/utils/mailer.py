# app/services/mailer.py
from flask_mail import Message
from app.extensions import mail
from app.utils.mail_templates import (
    generate_register_email,
    generate_new_user_notification,
    generate_password_reset_email,
    generate_password_change_email
)

class EmailService:
    def send_register_verification(email: str, code: str):
        """发送注册验证邮件 [^1]"""
        msg = Message(
            subject="注册验证码",
            recipients=[email],
            html=f"""
            <h3>您的注册验证码是：{code}</h3>
            <p>验证码15分钟内有效</p>
            """
        )
        mail.send(msg)

    @staticmethod
    def send_password_reset(email: str, code: str):
        """发送密码重置邮件 [^2]"""
        msg = Message(
            subject="密码重置验证码",
            recipients=[email],
            html=f"""
            <h3>您的密码重置验证码是：{code}</h3>
            <p>验证码30分钟内有效</p>
            """
        )
        mail.send(msg)
    @staticmethod
    def send_register_verification666(email: str, user: dict, code: str):
        """发送注册验证邮件"""
        msg = Message(
            subject="注册验证码",
            recipients=[email],
            html=generate_register_email(user, code)
        )
        mail.send(msg)

    @staticmethod
    def send_new_user_alert(admin_emails: list, user: dict):
        """发送新用户通知"""
        msg = Message(
            subject="新用户注册通知",
            recipients=admin_emails,
            html=generate_new_user_notification(user)
        )
        mail.send(msg)

    @staticmethod
    def send_password_reset666(email: str, user: dict, code: str):
        """发送密码重置邮件"""
        msg = Message(
            subject="密码重置验证码",
            recipients=[email],
            html=generate_password_reset_email(user, code)
        )
        mail.send(msg)

    @staticmethod
    def send_password_change_notification(email: str, user: dict):
        """发送密码修改通知"""
        msg = Message(
            subject="密码修改通知",
            recipients=[email],
            html=generate_password_change_email(user)
        )
        mail.send(msg)