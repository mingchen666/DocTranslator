// src/store/useTranslateStore.js
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTranslateStore = defineStore(
  'translate',
  () => {
    // State
    const pTitle = ref('')
    const version = ref('')
    const prompt = ref('')
    const comparisonList = ref([])
    const promptList = ref([])
    const models = ref([])
    const form = ref({
      api_url: 'https://api.openai.com',
      api_key: '',
      model: '',
      backup_model: '',
      langs: [],
      lang: '',
      type: [],
      threads: '',
      langs: [],
      type: [],
      doc2x_flag: '',
      doc2x_secret_key: ''
    })
    const translatesSettingData = ref({})

    // Actions
    const updateTitle = (title) => {
      pTitle.value = title
    }

    const updateVersion = (newVersion) => {
      version.value = newVersion
    }

    const updatePrompt = (newPrompt) => {
      prompt.value = newPrompt
    }

    const updateComparisonList = (newList) => {
      comparisonList.value = newList
    }

    const updatePromptList = (newList) => {
      promptList.value = newList
    }

    const updateModels = (newModels) => {
      models.value = newModels
    }

    const updateForm = (newForm) => {
      form.value = { ...form.value, ...newForm }
    }

    const updateTranslatesSettingData = (newData) => {
      translatesSettingData.value = newData
    }

    return {
      pTitle,
      version,
      prompt,
      comparisonList,
      promptList,
      models,
      form,
      translatesSettingData,
      updateTitle,
      updateVersion,
      updatePrompt,
      updateComparisonList,
      updatePromptList,
      updateModels,
      updateForm,
      updateTranslatesSettingData
    }
  },
  {
    persist: true // 启用持久化
  }
)
