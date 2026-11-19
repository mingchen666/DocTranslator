
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
  domain_mode: "legacy" | "auto" | "manual",
  domain: string,
}

export interface SiteSettingResponse extends SiteSetting {
  legacy: boolean,
  configured: boolean,
  project_url: string | null,
  api_prefix: string | null,
}

export type GetSiteSettingResponseData = ApiResponseData<SiteSettingResponse>

export type SettingNoResponseData=ApiResponseData<[]>