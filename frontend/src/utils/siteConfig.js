/**
 * 站点项目域名（接口地址）配置。
 *
 * 三种模式：
 * - manual：管理端「站点设置」里固定填写的域名/IP，所有请求都走它；
 * - auto：显式选择自动，请求前缀使用相对路径 /api，浏览器访问哪个地址就用哪个；
 * - legacy：沿用升级前的部署配置，继续使用构建时的 VITE_API_URL。
 *   升级站点没有保存过域名配置时默认落到这个模式，保证升级后行为不变。
 *
 * 注意：项目现有 nginx 约定接口路径带双层 /api（浏览器 /api/api/xxx，nginx
 * 剥掉一层后到后端 /api/xxx），所以这里的前缀本身以 /api 结尾。
 */

const API_SUFFIX = '/api'
const CONFIG_PATH = '/api/common/site-config'

const LEGACY_API_PREFIX = String(import.meta.env.VITE_API_URL || API_SUFFIX)
  .trim()
  .replace(/\/+$/, '') || API_SUFFIX

const state = {
  domain_mode: 'legacy',
  domain: '',
  project_url: '',
  legacy: true,
  configured: false
}

let apiPrefix = LEGACY_API_PREFIX
let loadingPromise = null

function trimTrailingSlash(value) {
  return String(value || '').trim().replace(/\/+$/, '')
}

function applyConfig(payload) {
  if (!payload || typeof payload !== 'object') {
    return
  }
  if (
    payload.domain_mode !== 'auto' &&
    payload.domain_mode !== 'manual' &&
    payload.domain_mode !== 'legacy'
  ) {
    // 老后端/异常响应没有该字段时保持 legacy 行为，不要误切到相对地址。
    return
  }
  state.domain_mode = payload.domain_mode
  state.domain = payload.domain || ''
  state.project_url = trimTrailingSlash(payload.project_url)
  state.legacy = Boolean(payload.legacy)
  state.configured = Boolean(payload.configured)

  if (state.domain_mode === 'manual' && state.project_url) {
    apiPrefix = `${state.project_url}${API_SUFFIX}`
  } else if (state.legacy || state.domain_mode === 'legacy') {
    apiPrefix = LEGACY_API_PREFIX
  } else {
    apiPrefix = API_SUFFIX
  }
}

/** 当前所有请求使用的接口前缀，例如 /api 或 http://1.2.3.4:35555/api */
export function getApiPrefix() {
  return apiPrefix
}

/** 拼接完整接口地址；path 需要以 / 开头，例如 /api/translate/list */
export function apiUrl(path) {
  const normalized = String(path || '')
  return `${apiPrefix}${normalized.startsWith('/') ? normalized : `/${normalized}`}`
}

/** 项目对外访问地址；自动模式下返回当前浏览器访问地址 */
export function getProjectUrl() {
  if (state.domain_mode === 'manual' && state.project_url) {
    return state.project_url
  }
  if (typeof window !== 'undefined' && window.location) {
    return window.location.origin
  }
  return ''
}

export function getSiteDomainConfig() {
  return { ...state, api_prefix: apiPrefix }
}

/** 启动时读取站点配置；失败时退回构建时配置，不阻塞页面。 */
export function loadSiteConfig() {
  if (!loadingPromise) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 5000)
    loadingPromise = fetch(`${LEGACY_API_PREFIX}${CONFIG_PATH}`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      cache: 'no-store',
      credentials: 'omit',
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
        const payload = body && body.data ? body.data : body
        applyConfig(payload)
      })
      .catch((error) => {
        console.warn('[site-config] 读取站点域名配置失败，沿用部署配置:', error)
        applyConfig({ domain_mode: 'auto', legacy: true })
      })
      .finally(() => {
        clearTimeout(timer)
        if (typeof window !== 'undefined') {
          window.__SITE_DOMAIN_CONFIG__ = getSiteDomainConfig()
        }
      })
  }
  return loadingPromise
}
