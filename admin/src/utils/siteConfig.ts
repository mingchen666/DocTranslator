/**
 * 站点项目域名（接口地址）配置。
 *
 * - manual：管理端「站点设置」里固定填写的域名/IP，所有请求都走它；
 * - auto：显式选择自动，请求前缀使用相对路径 /api，浏览器访问哪个地址就用哪个；
 * - legacy：沿用升级前的部署配置，继续使用 config.js 里的 window.ipConfig。
 *   升级站点没有保存过域名配置时默认落到这个模式，保证升级后行为不变。
 *
 * 项目 nginx 约定接口路径带双层 /api（浏览器 /api/api/xxx，nginx 剥掉一层后
 * 到后端 /api/xxx），因此这里返回的前缀本身以 /api 结尾，service.ts 再拼
 * /api/admin。
 */

const API_SUFFIX = "/api"
const CONFIG_PATH = "/api/common/site-config"

export function getLegacyPrefix(): string {
  const value = String((window as any).ipConfig || API_SUFFIX).trim().replace(/\/+$/, "")
  return value || API_SUFFIX
}

const legacyPrefix = getLegacyPrefix

function trimTrailingSlash(value: any): string {
  return String(value || "").trim().replace(/\/+$/, "")
}

const state = {
  domain_mode: "legacy",
  domain: "",
  project_url: "",
  legacy: true,
  configured: false
}

let apiPrefix = legacyPrefix()
let loadingPromise: Promise<void> | null = null

function applyConfig(payload: any) {
  if (!payload || typeof payload !== "object") {
    return
  }
  if (
    payload.domain_mode !== "auto" &&
    payload.domain_mode !== "manual" &&
    payload.domain_mode !== "legacy"
  ) {
    // 老后端/异常响应没有该字段时保持 legacy 行为，不要误切到相对地址。
    return
  }
  state.domain_mode = payload.domain_mode
  state.domain = payload.domain || ""
  state.project_url = trimTrailingSlash(payload.project_url)
  state.legacy = Boolean(payload.legacy)
  state.configured = Boolean(payload.configured)

  if (state.domain_mode === "manual" && state.project_url) {
    apiPrefix = `${state.project_url}${API_SUFFIX}`
  } else if (state.legacy || state.domain_mode === "legacy") {
    apiPrefix = legacyPrefix()
  } else {
    apiPrefix = API_SUFFIX
  }
}

/** 当前所有请求使用的接口前缀，例如 /api 或 http://1.2.3.4:35555/api */
export function getApiPrefix(): string {
  return apiPrefix
}

/** 项目对外访问地址；自动模式下返回当前浏览器访问地址 */
export function getProjectUrl(): string {
  if (state.domain_mode === "manual" && state.project_url) {
    return state.project_url
  }
  return window.location.origin
}

export function getSiteDomainConfig() {
  return { ...state, api_prefix: apiPrefix }
}

/** 启动时读取站点配置；失败时退回 config.js 配置，不阻塞管理端。 */
export function loadSiteConfig(): Promise<void> {
  if (loadingPromise) {
    return loadingPromise
  }
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), 5000)
  loadingPromise = fetch(`${legacyPrefix()}${CONFIG_PATH}`, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
    credentials: "omit",
    signal: controller.signal
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      return response.json()
    })
    .then((body) => {
      if (body && body.code !== undefined && body.code !== 200) {
        throw new Error(body.message || `业务错误 ${body.code}`)
      }
      applyConfig(body && body.data ? body.data : body)
    })
    .catch((error) => {
      console.warn("[site-config] 读取站点域名配置失败，沿用 config.js 配置:", error)
      applyConfig({ domain_mode: "auto", legacy: true })
    })
    .finally(() => {
      clearTimeout(timer)
      ;(window as any).__SITE_DOMAIN_CONFIG__ = getSiteDomainConfig()
    })
  return loadingPromise
}
