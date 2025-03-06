// 通过vue-router插件实现模块路由配置
import { createRouter, createWebHashHistory, createWebHistory } from 'vue-router'
/* Layout */
import Layout from '@/pages/layout/index.vue'
import NotFound from '@/components/notFound.vue'

//配置路由
const constantRoute = [
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: '/',
        component: () => import('@/pages/trans/index.vue'),
        name: 'home',
        meta: {
          title: '首页',
          noCache: true
        }
      }
    ]
  },
  {
    path: '/corpus',
    component: Layout,
    redirect: '/corpus/index', // 重定向
    children: [
      {
        path: 'index',
        component: () => import('@/pages/corpus/index.vue'),
        name: 'corpus',
        meta: {
          title: '语料库',
          noCache: true
        }
      },
      {
        path: 'square',
        component: () => import('@/pages/corpus/square.vue'),
        name: 'square',
        meta: {
          title: '广场',
          noCache: true
        }
      }
    ]
  },
  // 登录注册
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/login/index.vue')
  },
  // 忘记密码
  {
    path: '/forget',
    name: 'forget',
    component: () => import('@/pages/password/forget.vue')
  },
  // 重置密码
  {
    path: '/reset',
    name: 'reset',
    component: () => import('@/pages/password/reset.vue')
  },
  // 404 路由，放在最后
  {
    path: '/404',
    name: '404',
    component: () => import('@/components/notFound.vue'),
    hidden: true
  },
  {
    path: '/:pathMatch(.*)',
    redirect: '/404',
    hidden: true
  }
]

// 创建路由器
let router = createRouter({
  // 路由模式hash
  // history: createWebHashHistory(),
  history: createWebHistory(),
  routes: constantRoute
})

// 添加全局前置守卫
router.beforeEach((to, from, next) => {
  next() // 如果存在，正常导航
})

export default router
