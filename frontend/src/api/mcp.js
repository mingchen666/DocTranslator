import request from '@/utils/request'

export function getMcpKeys() {
  return request({
    url: '/api/mcp/keys',
    method: 'get',
    params: { scope: 'user' }
  })
}

export function createMcpKey(data) {
  return request({
    url: '/api/mcp/key',
    method: 'post',
    data,
    headers: { 'Content-Type': 'application/json' },
    transformRequest: [(data) => JSON.stringify(data)]
  })
}

export function getMcpKeyDetail(id) {
  return request({
    url: `/api/mcp/key/${id}`,
    method: 'get'
  })
}

export function updateMcpKey(id, data) {
  return request({
    url: `/api/mcp/key/${id}`,
    method: 'post',
    data,
    headers: { 'Content-Type': 'application/json' },
    transformRequest: [(data) => JSON.stringify(data)]
  })
}

export function deleteMcpKey(id) {
  return request({
    url: `/api/mcp/key/${id}`,
    method: 'delete'
  })
}

export function regenerateMcpKey(id) {
  return request({
    url: `/api/mcp/key/${id}/regenerate`,
    method: 'post',
    headers: { 'Content-Type': 'application/json' },
    transformRequest: [(data) => JSON.stringify(data)]
  })
}
