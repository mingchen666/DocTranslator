import request from '@/utils/request'

//术语-广场列表
export function comparison_share(params) {
  return request({
      url: `/api/comparison/share`,
      method: 'get',
      params: params
  });
}

//提示语-广场列表
export function prompt_share(params) {
  return request({
      url: `/api/prompt/share`,
      method: 'get',
      params: params
  });
}

//添加到我的术语
export function comparison_copy(id){
  return request({
      url: `/api/comparison/copy/${id}`,
      method: 'POST'
  });
}

//添加到我的提示语
export function prompt_copy(id){
  return request({
      url: `/api/prompt/copy/${id}`,
      method: 'POST'
  });
}

//收藏术语
export function comparison_fav(id){
  return request({
      url: `/api/comparison/fav/${id}`,
      method: 'POST'
  });
}

//收藏提示语
export function prompt_fav(id){
  return request({
      url: `/api/prompt/fav/${id}`,
      method: 'POST'
  });
}