from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class ChangePasswordSchema(Schema):
    old_password = fields.Str(required=True, error_messages={
        "required": "原密码不能为空"
    })
    new_password = fields.Str(required=True, validate=[
        validate.Length(min=6, error="新密码至少6位")
    ], error_messages={
        "required": "新密码不能为空"
    })
    new_password_confirmation = fields.Str(required=True)

    @validates_schema
    def validate_password_confirmation(self, data, **kwargs):
        if data['new_password'] != data['new_password_confirmation']:
            raise ValidationError("两次输入的新密码不一致")


class EmailChangePasswordSchema(Schema):
    code = fields.Str(required=True, error_messages={
        "required": "验证码不能为空"
    })
    new_password = fields.Str(required=True, validate=validate.Length(min=6))
    new_password_confirmation = fields.Str(required=True)
