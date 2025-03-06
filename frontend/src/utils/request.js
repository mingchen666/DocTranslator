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
    if (res.code === 401) {
  router.push('/login')
}
    // if the custom code is not 20000, it is judged as an error.
    // if (res.ret !== 0) {
    //   if (res.code === 401) {
    //     // to re-login
    //     ElMessage.confirm(res.message, i18n.t('common.tips'), {
    //       confirmButtonText:i18n.t('common.log_back_in'),
    //       cancelButtonText: i18n.t('common.return_before'),
    //       type: 'warning'
    //     }).then(() => {
    //       // store.dispatch('user/resetToken').then(() => {
    //       //   document.location.href='/login.html';
    //       // })
    //     }).catch(()=>{
    //       router.back()
    //     })
    //   } else {
    //     ElMessageBox({
    //       message: res.message || 'Error',
    //       type: 'error',
    //       duration: 5 * 1000
    //     })
    //   }
    //   return Promise.reject(new Error(res.message || 'Error'))
    // } else {
      return res
    // }
  },
  error => {
    console.log('err' + error) // for debug
    ElMessageBox({
      message: error.message,
      type: 'error',
      duration: 5 * 1000
    })
    return Promise.reject(error)
  }
)

export default service

