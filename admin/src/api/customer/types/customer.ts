export interface CreateOrUpdateCustomerRequestData {
  id?: number
  email: string
  password?: string
  level: string
}

export interface GetCustomerRequestData {
  /** 当前页码 */
  page: number
  /** 查询条数 */
  limit: number
  /** 关键字 */
  keyword?: string
}

export interface GetCustomerData {
  id: number
  created_at: string
  email: string
  level: string
  status: boolean
}

export type GetCustomerResponseData = ApiResponseData<{
  data: GetCustomerData[]
  total: number
}>

export interface RegisterData {
  email: string
  password?: string
  level: string
}
