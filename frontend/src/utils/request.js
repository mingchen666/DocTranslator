import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import {store} from '@/store'
import router from '@/router'
import Qs from 'qs'
// import router from '@/router'
// import i18n from '@/lang/index' // i18n 国际化

// create an axios instance
const service = axios.create({
  baseURL: '/api', //  import.meta.env.VITE_API_URL   url = base url + request url
  withCredentials: true, // send cookies when cross-domain requests
  crossDomain: true,
  timeout: 30000, // request timeout
  transformRequest: [function(data) {
    if (data instanceof FormData) {
      return data
    } else {
      data = Qs.stringify(data, { arrayFormat: 'indices' })
      return data
    }
  }],
  paramsSerializer: (params) => {
    for (const param in params) {
      if (params[param] === '' || params[param] == null) {
        delete params[param]
      }
    }
    return Qs.stringify(params)
  }
})

// request interceptor
service.interceptors.request.use(
  config => {
    config.headers['token'] = store.token;
    config.headers['credentials']='include'
    config.headers['withCredentials']=true  // 携带凭据（如 Cookies）
      // config.headers['language'] = localStorage.getItem('language')||'zh';
      return config
  },
  error => {
    // do something with request error
    console.log(error) // for debug
    return Promise.reject(error)
  }
)

// response interceptor
service.interceptors.response.use(
  response => {
    const res = response.data
    // if (res?.code === 401) {
    //   router.push('/login')
    //   return Promise.reject(new Error('Unauthorized'))
    // }
    return res
  },
  error => {
    const { response } = error
    if (response) {
      switch (response.status) {
        case 401:
          ElMessage.error('身份过期，请重新登录')
          router.push('/login')
          break
        case 422:
          ElMessage.error('身份过期，请重新登录')
          router.push('/login')
          break  
        case 403:
          ElMessage.error('权限不足')
          break
        default:
          ElMessage.error('请求失败')
      }
    } else {
      ElMessage.error('网络连接异常')
    }
    return Promise.reject(error)
  }
)
// service.interceptors.response.use(
//   response => {

//     const res = response.data
  
//       return res
//   },
//   error => {
//     const { response } = error
//      if (response.code == 401) {
//       console.log(401);
//       router.push('/login')
// }
//     console.log('err' + error)
//     ElMessageBox({
//       message: error.message,
//       type: 'error',
//       duration: 5 * 1000
//     })
//     return Promise.reject(error)
//   }
// )

export default service

