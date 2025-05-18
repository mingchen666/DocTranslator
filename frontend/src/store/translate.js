
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useSettingsStore } from './settings';
export const useTranslateStore = defineStore('translate-settings', () => {
  // 当前翻译服务
  const currentService = ref('ai') // ai/baidu/google
  const settingsStore = useSettingsStore();
  // console.log('settingsStore', settingsStore.system_settings);

  // AI翻译设置
  const aiServer = ref({
    api_url: settingsStore.system_settings.api_url || '',
    api_key: '',
    model: settingsStore.system_settings.default_model,
    backup_model: settingsStore.system_settings.default_backup,
    prompt: settingsStore.system_settings.prompt_template,
    prompt_id: null,
    threads: settingsStore.system_settings.max_threads,
    comparison_id: null,
    lang: '',
    doc2x_flag: '',
    doc2x_secret_key: ''
  })

  // 百度翻译设置
  const baidu = ref({
    app_id: '',
    app_key: '',
    from_lang: 'auto',
    to_lang: 'zh',
    needIntervene: false // 是否使用术语库
  })

  // 谷歌翻译设置
  const google = ref({
    app_key: '',
    project_id: '',
    from_lang: 'auto',
    to_lang: 'zh'
  })
  // 其他设置
  const otherSettings = ref({
    langs: ['中文', '英语'],
    comparison_id: '',
    threads: 5,
    doc2x_flag: 'N', // 是否使用doc2x
    doc2x_secret_key: ''
  })
  // 通用设置
  const common = ref({
    langs: ['中文', '英语'],
    type: ['trans_text', 'trans_text_only', 'trans_text_only_new'],
    // comparison_id: null,
    doc2x_flag: 'N',
    doc2x_secret_key: ''
  })

  // 模型和语言选项
  const models = ref(['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo'])
  const langOptions = ref([
    { value: 'auto', label: '自动检测' },
    { value: 'zh', label: '中文' },
    { value: 'en', label: '英语' },
    // 其他语言...
  ])

  const terms = ref([])

  // 更新当前服务
  const updateCurrentService = (service) => {
    currentService.value = service
  }

  // 更新AI设置
  const updateAIServerSettings = (settings) => {
    aiServer.value = { ...aiServer.value, ...settings }
  }

  // 更新百度翻译设置
  const updateBaiduSettings = (settings) => {
    baidu.value = { ...baidu.value, ...settings }
  }

  // 更新谷歌翻译设置
  const updateGoogleSettings = (settings) => {
    google.value = { ...google.value, ...settings }
  }

  // 更新通用设置
  const updateCommonSettings = (settings) => {
    common.value = { ...common.value, ...settings }
  }
  // 更新其他设置
  const updateOtherSettings = (settings) => {
    otherSettings.value = { ...otherSettings.value, ...settings }
  }
  // 更新AI翻译表单其中某一个字段
  const updateAISettingsField = (field, value) => {
    aiServer.value[field] = value
    // if (currentService.value === 'ai') {
    //   aiServer.value[field] = value
    // } else if (currentService.value === 'baidu') {
    //   baidu.value[field] = value
    // } else if (currentService.value === 'google') {
    //   google.value[field] = value
    // }
  }
  // 获取当前服务的全部表单数据
  const getCurrentServiceForm = computed(() => {
    switch (currentService.value) {
      case 'ai':
        return { ...aiServer.value, ...common.value, server: 'openai' };
      case 'baidu':
        return { ...baidu.value, ...common.value, server: 'baidu' };
      case 'google':
        return { ...google.value, ...common.value, server: 'google' };
      default:
        return {}; // 默认返回空对象
    }
  });
  // 保存所有设置
  const saveAllSettings = (settings) => {
    if (settings.currentService) {
      currentService.value = settings.currentService
    }
    if (settings.aiServer) updateAIServerSettings(settings.aiServer)
    if (settings.baidu) updateBaiduSettings(settings.baidu)
    if (settings.google) updateGoogleSettings(settings.google)
    if (settings.common) updateCommonSettings(settings.common)
    if (settings.otherSettings) updateOtherSettings(settings.otherSettings)
  }

  // 重置当前服务设置
  const resetCurrentService = () => {
    if (currentService.value === 'ai') {
      aiServer.value = {
        api_url: 'https://api.openai.com',
        api_key: '',
        model: 'gpt-3.5-turbo',
        backup_model: '',
        prompt: '你是一个文档翻译助手...',
        prompt_id: 0
      }
    } else if (currentService.value === 'baidu') {
      baidu.value = {
        app_id: '',
        app_key: '',
        from_lang: 'auto',
        to_lang: 'zh'
      }
    } else if (currentService.value === 'google') {
      google.value = {
        api_key: '',
        project_id: '',
        from_lang: 'auto',
        to_lang: 'zh'
      }
    }
  }

  return {
    currentService,
    aiServer,
    baidu,
    google,
    common,
    models,
    langOptions,
    terms,
    otherSettings,
    updateCurrentService,
    updateAIServerSettings,
    updateBaiduSettings,
    updateGoogleSettings,
    updateCommonSettings,
    updateOtherSettings,
    saveAllSettings,
    resetCurrentService,
    updateAISettingsField,
    getCurrentServiceForm
  }
}, {
  persist: true, // 启用持久化
});
