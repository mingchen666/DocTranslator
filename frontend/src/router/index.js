import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/pages/layout/index.vue'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'
//配置路由
const constantRoute = [
  {
    path: '/',
    component: Layout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '/',
        component: () => import('@/pages/trans/index.vue'),
        name: 'home',
        meta: {
          title: '首页',
          noCache: true,

        }
      },
      {
        path: '/profile',
        component: () => import('@/pages/profile/index.vue'),
        name: 'profile',
        meta: {
          title: '个人中心',
          noCache: true,
          requiresAuth: true
        }
      }
    ]
  },
  {
    path: '/corpus',
    component: Layout,
    redirect: '/corpus/index', // 重定向
    meta: { requiresAuth: true },
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
    meta: { guestOnly: true },
    component: () => import('@/pages/login/index.vue')
  },
  // 忘记密码
  {
    path: '/forget',
    name: 'forget',
    meta: { guestOnly: true },
    component: () => import('@/pages/password/forget.vue')
  },
  // 重置密码
  {
    path: '/reset',
    name: 'reset',
    meta: { guestOnly: true },
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
  history: createWebHistory(),
  routes: constantRoute
})

// 添加全局前置守卫
// 路由拦截逻辑
router.beforeEach((to) => {
  const userStore = useUserStore()
  // 检查是否需要登录
  if (to.meta.requiresAuth) {
    // 未登录状态
    if (!userStore.token) {
      // 跳转到登录页，并携带原路径
      return {
        name: 'login',
        query: {
          redirect: to.fullPath // 保存原始目标路径
        }
      }
    }
  }

  // 已登录状态访问登录页
  // if (to.name === 'login' && userStore.token) {
  //   ElMessage.warning('您已登录')
  //   return '/' // 跳转到首页
  // }
  // 其他情况正常放行
  return true
})

export default router
