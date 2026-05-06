import { request } from "@/utils/service"

export function getAdminMcpKeys(params?: { scope?: string; customer_id?: string }) {
  return request({
    url: "/mcp/keys",
    method: "get",
    params
  })
}

export function createAdminMcpKey(data: any) {
  return request({
    url: "/mcp/key",
    method: "post",
    data
  })
}

export function getAdminMcpKeyDetail(id: string) {
  return request({
    url: `/mcp/key/${id}`,
    method: "get"
  })
}

export function updateAdminMcpKey(id: string, data: any) {
  return request({
    url: `/mcp/key/${id}`,
    method: "post",
    data
  })
}

export function deleteAdminMcpKey(id: string) {
  return request({
    url: `/mcp/key/${id}`,
    method: "delete"
  })
}

export function regenerateAdminMcpKey(id: string) {
  return request({
    url: `/mcp/key/${id}/regenerate`,
    method: "post"
  })
}

export function searchCustomers(keyword: string) {
  return request({
    url: "/customer",
    method: "get",
    params: { page: 1, limit: 10, search: keyword }
  })
}

export function getAdminPromptList() {
  return request({
    url: "/prompts",
    method: "get"
  })
}
