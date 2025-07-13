import { createApp } from 'vue'
//引入路由
import router from './router'
import './style.css'
import App from './App.vue'
import 'element-plus/dist/index.css'
import ElementPlus from 'element-plus';
import 'element-plus/theme-chalk/index.css';

import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'virtual:svg-icons-register'

import zhLocale from 'element-plus/es/locale/lang/zh-cn' 

import { createPinia } from 'pinia';
import { createPersistedState } from 'pinia-plugin-persistedstate';

const pinia = createPinia()
const app=createApp(App)
app.use(router)
app.use(ElementPlus,{ locale: zhLocale})


for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

pinia.use(createPersistedState())
app.use(pinia)
app.mount("#app")
