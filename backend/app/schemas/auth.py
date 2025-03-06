from marshmallow import Schema, fields, validate, validates, ValidationError, validates_schema
from flask import current_app


class SendCodeSchema(Schema):
    email = fields.Email(required=True, error_messages={
        "required": "Email is required",
        "invalid": "Invalid email format"
    })

    @validates("email")
    def validate_email_domain(self, value):
        allowed_domains = current_app.config.get('ALLOWED_EMAIL_DOMAINS', [])
        if allowed_domains:
            domain = value.split('@')[-1]
            if domain not in allowed_domains:
                raise ValidationError("Email domain not allowed")


class RegisterSchema(Schema):
    email = fields.Email(required=True, error_messages={
        "required": "邮箱不能为空",
        "invalid": "邮箱格式不正确"
    })
    password = fields.String(
        required=True,
        validate=validate.Length(min=6),
        error_messages={
            "required": "密码不能为空",
            "too_short": "密码长度至少6位"
        }
    )
    code = fields.String(required=True, error_messages={"required": "验证码不能为空"})
class LoginSchema(Schema):
    email = fields.Email(required=True, error_messages={
        "required": "邮箱不能为空",
        "invalid": "邮箱格式不正确"
    })
    password = fields.String(required=True, error_messages={
        "required": "密码不能为空"
    })

class FindSendSchema(Schema):
    email = fields.Email(required=True, error_messages={
        "required": "邮箱不能为空",
        "invalid": "邮箱格式不正确"
    })

class FindResetSchema(Schema):
    email = fields.Email(required=True)
    code = fields.String(required=True)
    password = fields.String(required=True, validate=lambda x: len(x) >= 6)
    password_confirmation = fields.String(required=True)

    @validates_schema
    def validate_passwords(self, data, **kwargs):
        if data['password'] != data['password_confirmation']:
            raise ValidationError("两次密码不一致", "password_confirmation")
