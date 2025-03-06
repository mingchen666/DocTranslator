export interface GetTranslateRequestData {
  /** 当前页码 */
  page: number
  /** 查询条数 */
  limit: number
  /** 关键字 */
  keyword?: string
}

export interface GetTranslateData {
  id: number
  translate_no: string
  created_at: string
  origin_filename: string
  origin_filepath: string
  target_filepath: string
  start_at: string
  end_at: string
  status: boolean
}

export type GetTranslateResponseData = ApiResponseData<{
  data: GetTranslateData[]
  total: number
}>

export type TranslateNoResponseData=ApiResponseData<[]>