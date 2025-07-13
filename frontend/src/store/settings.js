import { de } from 'element-plus/es/locales.mjs'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSettingsStore = defineStore('system-settings', () => {
  const system_settings = ref({
    prompt_template: '',
    default_model: '',
    default_backup: '',
    api_url: '',
    api_key: '',
    models: [],
    max_threads: 10,
    threads: 10,
  })
  const version = ref('community')
  const default_prompt = ref(`你是一个文档翻译助手，请将以下内容直接翻译成{target_lang}，不返回原文本。如果文本中包含{target_lang}文本、特殊名词（比如邮箱、品牌名、单位名词如mm、px、℃等）、无法翻译等特殊情况，请直接返回原词语而无需解释原因。遇到无法翻译的文本直接返回原内容。保留多余空格。`)
  const siteTitle = 'DocTranslator'
  const updateSystemSettings = (newValue) => {
    system_settings.value = newValue
  }
  return {
    default_prompt,
    version,
    system_settings,
    siteTitle,
    updateSystemSettings
  }
},
  { persist: true })
