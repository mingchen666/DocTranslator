# app/schemas/validators.py
VALIDATION_RULES = {
    'register': {
        'email': {'required': True, 'type': 'email'},
        'password': {'required': True, 'min_length': 6},
        'code': {'required': True}
    },
    'find': {
        'code': {'required': True},
        'password': {
            'required': True,
            'min_length': 6,
            'confirmed': True
        }
    }
}

ERROR_MESSAGES = {
    'email_required': '邮箱不能为空',
    'password_required': '密码不能为空',
    'password_min': '密码长度至少6位',
    'code_required': '验证码不能为空',
    'password_confirmed': '两次输入密码不一致'
}