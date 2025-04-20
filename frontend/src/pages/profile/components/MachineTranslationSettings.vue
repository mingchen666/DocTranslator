<template>
  <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" label-position="top">
    <el-form-item label="翻译引擎" prop="provider">
      <el-select v-model="form.provider" placeholder="选择翻译引擎">
        <el-option label="百度翻译" value="baidu" />
        <el-option label="有道翻译" value="youdao" />
        <el-option label="Google翻译" value="google" />
      </el-select>
    </el-form-item>

    <el-form-item label="App ID" prop="app_id">
      <el-input v-model="form.app_id" placeholder="输入应用ID" clearable />
    </el-form-item>

    <el-form-item label="App Key" prop="app_key">
      <el-input v-model="form.app_key" placeholder="输入应用密钥" show-password clearable />
    </el-form-item>

    <el-form-item>
      <el-button type="primary" @click="submitForm">保存设置</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'
import { useTranslateStore } from '@/store/translate'
const translateStore = useTranslateStore()
const formRef = ref(null)
const form = ref({})
onMounted(() => {
  form.value = {
    provider: 'baidu',
    app_id: translateStore.baidu.app_id,
    app_key: translateStore.baidu.app_key
  }
})
const rules = {
  provider: [{ required: true, message: '请选择翻译引擎', trigger: 'change' }],
  app_id: [{ required: true, message: '请输入App ID', trigger: 'blur' }],
  app_key: [{ required: true, message: '请输入App Key', trigger: 'blur' }]
}

const submitForm = async () => {
  try {
    await formRef.value.validate()
    translateStore.updateBaiduSettings({
      app_id: form.value.app_id,
      app_key: form.value.app_key
    })
    ElMessage.success('保存成功!')
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}
</script>
