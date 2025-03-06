import request from '@/utils/request'

// 修改密码
export function changePassword(data) {
    return request({
        url: '/api/change',
        method: 'POST',
        data
    });
}

/**
 * 获取存储空间
 */
export function storage() {
    return request({
        url: '/api/storage',
        method: 'GET',
    });
}

/**
 * 登录用户基本信息
 */
export function authInfo() {
    return request({
        url: '/api/info',
        method: 'GET',
    });
}


/**
 * 获取环境配置信息
 */
export function getSetting() {
  return request({
      url: '/api/common/setting',
      method: 'GET',
  });
}