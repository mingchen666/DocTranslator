import request from '@/utils/request'

// 检查是否可用
export function checkOpenAI(params) {
    return request({
        url: `/api/check/openai`,
        method: 'POST',
        data: params
    });
}

// 检查是否可用
export function checkDocx(params) {
    return request({
        url: `/api/check/doc2x`,
        method: 'POST',
        data: params
    });
}

// 检查pdf是否是扫描件
export function checkPdf(file_path) {
    return request({
        url: `/api/check/pdf`,
        method: 'POST',
        data: { file_path }
    });
}

export function delFile(data) {
    return request({
        url: `/api/delFile`,
        method: 'POST',
        data: data
    });
}


export function transalteFile(params) {
    return request({
        url: `/api/translate`,
        method: 'POST',
        data: params
    });
}
// 进度查询
export function transalteProcess(params) {
    return request({
        url: `/api/process`,
        method: 'POST',
        data: params
    });
}

/**
 * 翻译
 */
export function translates(params) {
    return request({
        url: `/api/translates`,
        method: 'get',
        params
    });
}



export function delTranslate(id) {
    return request({
        url: `/api/translate/${id}`,
        method: 'delete'
    });
}

/**
 * 删除所有翻译文件记录
 */
export function delAllTranslate() {
    return request({
        url: '/api/translate/all',
        method: 'delete'
    });
}

/**
 * 下载所有翻译文件记录
 */
export function downAllTranslate() {
    return request({
        url: '/api/translate/download/all',
        method: 'get'
    });
}


/**
 * 获取文件统计
 */
export function getFinishCount() {
    return request({
        url: '/api/translate/finish/count',
        method: 'get'
    });
}

// doc2x 启动pdf翻译
export function doc2xStartService(data) {
    return request({
        url: '/api/doc2x/start',
        method: 'post',
        data
    });
}

// doc2x查询任务状态
export function doc2xQueryStatusService(data) {
    return request({
        url: '/api/doc2x/status',
        method: 'post',
        data: data
    });
}

