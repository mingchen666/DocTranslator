import request from '@/utils/request'

// 注册时发送邮箱验证码
export function registerSendEmail(email) {
    return request({
        url: `/api/register/send`,
        method: 'POST',
        data: {email}
    });
}

export function register(params) {
    return request({
        url: `/api/register`,
        method: 'POST',
        data: params
    });
}

export function login(params) {
    return request({
        url: `/api/login`,
        method: 'POST',
        data: params
    });
}

// 忘记密码发送邮箱验证码
export function forgetSendEmail(email) {
    return request({
        url: `/api/find/send`,
        method: 'POST',
        data: {email}
    });
}

export function forget(data) {
    return request({
        url: `/api/find`,
        method: 'POST',
        data: data
    });
}