# app/utils/mail_templates.py
from datetime import datetime

def generate_register_email(user: dict, code: str) -> str:
    """生成注册确认邮件HTML"""
    return f"""
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; background-color: #f7f7f7; }}
          .container {{ max-width: 600px; margin: 20px auto; padding: 20px; background: #fff; }}
          .header {{ background: #f0f0f0; padding: 20px; text-align: center; }}
          .code {{ font-size: 32px; color: #333; text-align: center; margin: 20px 0; }}
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>欢迎注册我们的服务</h1>
          </div>
          <div class="content">
            <p>尊敬的{user.get('name', '用户')}：</p>
            <p>您的注册验证码是：</p>
            <div class="code">{code}</div>
            <p>验证码有效期15分钟，请勿泄露给他人</p>
          </div>
        </div>
      </body>
    </html>
    """

def generate_new_user_notification(user: dict) -> str:
    """生成新用户注册通知邮件HTML"""
    return f"""
    <html>
      <style>
        .container {{ max-width: 600px; margin: 20px auto; padding: 20px; background: #fff; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ margin: 10px 0; }}
      </style>
      <body>
        <div class="container">
          <h2>系统通知：新用户注册</h2>
          <p>以下用户刚刚完成了注册：</p>
          <ul>
            <li>用户ID：{user.get('id', '')}</li>
            <li>邮箱：{user.get('email', '')}</li>
            <li>注册时间：{user.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</li>
          </ul>
        </div>
      </body>
    </html>
    """

def generate_password_reset_email(user: dict, code: str) -> str:
    """生成密码重置邮件HTML"""
    return f"""
    <html>
      <style>
        .container {{ max-width: 600px; margin: 20px auto; padding: 20px; background: #fff; }}
        .code {{ color: #007bff; font-size: 32px; text-align: center; }}
      </style>
      <body>
        <div class="container">
          <h2>密码重置验证码</h2>
          <p>您的密码重置验证码是：</p>
          <div class="code">{code}</div>
          <p>验证码有效期30分钟</p>
        </div>
      </body>
    </html>
    """

def generate_password_change_email(user: dict) -> str:
    """生成密码修改通知邮件HTML"""
    return f"""
    <html>
      <style>
        .container {{ max-width: 600px; margin: 20px auto; padding: 20px; background: #fff; }}
      </style>
      <body>
        <div class="container">
          <h2>密码修改通知</h2>
          <p>您的账户 {user.get('email', '')} 密码修改成功</p>
          <p>时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
      </body>
    </html>
    """