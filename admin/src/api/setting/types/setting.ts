
export interface ApiSetting {
  api_url: string,
  api_key: string,
  models: string,
  default_model: string,
  default_backup: string
}

export type GetApiSettingResponseData = ApiResponseData<ApiSetting>


export interface OtherSetting {
  prompt: string,
  threads: string,
  email_limit: string,
}

export type GetOtherSettingResponseData = ApiResponseData<OtherSetting>


export interface SiteSetting {
  version: string,
}

export type GetSiteSettingResponseData = ApiResponseData<SiteSetting>

export type SettingNoResponseData=ApiResponseData<[]>