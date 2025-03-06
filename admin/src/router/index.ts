import { type RouteRecordRaw, createRouter } from "vue-router"
import { history, flatMultiLevelRoutes } from "./helper"
import routeSettings from "@/config/route"

const Layouts = () => import("@/layouts/index.vue")

/**
 * 常驻路由
 * 除了 redirect/403/404/login 等隐藏页面，其他页面建议设置 Name 属性
 */
export const constantRoutes: RouteRecordRaw[] = [
  {
    path: "/redirect",
    component: Layouts,
    meta: {
      hidden: true
    },
    children: [
      {
        path: ":path(.*)",
        component: () => import("@/views/redirect/index.vue")
      }
    ]
  },
  {
    path: "/403",
    component: () => import("@/views/error-page/403.vue"),
    meta: {
      hidden: true
    }
  },
  {
    path: "/404",
    component: () => import("@/views/error-page/404.vue"),
    meta: {
      hidden: true
    },
    alias: "/:pathMatch(.*)*"
  },
  {
    path: "/login",
    component: () => import("@/views/login/index.vue"),
    meta: {
      hidden: true
    }
  },
  {
    path: "/",
    component: Layouts,
    redirect: "/dashboard",
    children: [
      {
        path: "dashboard",
        component: () => import("@/views/dashboard/index.vue"),
        name: "Dashboard",
        meta: {
          title: "首页",
          svgIcon: "dashboard",
          affix: true
        }
      }
    ]
  },
  {
    path: "/customer",
    component: Layouts,
    children: [
      {
        path: "",
        component: () => import("@/views/customer/index.vue"),
        name: "customer",
        meta: {
          title: "用户管理",
          elIcon: "user",
          affix: true
        }
      }
    ]
  },
  {
    path: "/translate",
    component: Layouts,
    children: [
      {
        path: "",
        component: () => import("@/views/translate/index.vue"),
        name: "translate_list",
        meta: {
          title: "翻译任务",
          elIcon: "tickets",
          affix: true
        }
      }
    ]
  },
  {
    path: "/setting",
    component: Layouts,
    meta:{
      title:"系统设置",
      elIcon: "setting",
      affix: true
    },
    children: [
      {
        path: "api",
        component: () => import("@/views/setting/api.vue"),
        name: "setting_api",
        meta: {
          title: "API设置",
          elIcon: "key",
          affix: true
        }
      },
      {
        path: "other",
        component: () => import("@/views/setting/other.vue"),
        name: "setting_other",
        meta: {
          title: "其他设置",
          elIcon: "tools",
          affix: true
        }
      },
      {
        path: "site",
        component: () => import("@/views/setting/site.vue"),
        name: "setting_site",
        meta: {
          title: "站点设置",
          elIcon: "tools",
          affix: true
        }
      }
    ]
  }
]

/**
 * 动态路由
 * 用来放置有权限 (Roles 属性) 的路由
 * 必须带有 Name 属性
 */
export const dynamicRoutes: RouteRecordRaw[] = [
]

const router = createRouter({
  history,
  routes: routeSettings.thirdLevelRouteCache ? flatMultiLevelRoutes(constantRoutes) : constantRoutes
})
console.log(routeSettings.thirdLevelRouteCache ? flatMultiLevelRoutes(constantRoutes) : constantRoutes)
/** 重置路由 */
export function resetRouter() {
  // 注意：所有动态路由路由必须带有 Name 属性，否则可能会不能完全重置干净
  try {
    router.getRoutes().forEach((route) => {
      const { name, meta } = route
      if (name && meta.roles?.length) {
        router.hasRoute(name) && router.removeRoute(name)
      }
    })
  } catch {
    // 强制刷新浏览器也行，只是交互体验不是很好
    window.location.reload()
  }
}

export default router
