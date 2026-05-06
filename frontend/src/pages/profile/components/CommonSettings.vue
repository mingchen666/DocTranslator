<template>
  <div class="common-settings-container">
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="settings-form">
      <div class="form-section-title">
        <span class="section-dot"></span>
        术语与线程
      </div>

      <el-form-item label="默认术语库（AI 翻译）" prop="comparison_id">
        <el-select
          v-model="form.comparison_id"
          placeholder="选择术语库"
          clearable
          filterable
          style="width: 100%"
          @focus="fetchTermList"
        >
          <el-option v-for="term in termList" :key="term.id" :label="term.title" :value="term.id" />
        </el-select>
      </el-form-item>

      <el-form-item label="线程数" prop="threads">
        <el-input-number v-model="form.threads" :min="1" :max="10" :step="1" />
      </el-form-item>

      <div class="form-section-title">
        <span class="section-dot"></span>
        Doc2X 配置
      </div>

      <el-alert
        type="warning"
        description="启用后，所有 PDF 将使用 Doc2X 进行解析处理"
        show-icon
        :closable="false"
        style="margin-bottom: 18px;"
      />

      <el-form-item label="是否使用 Doc2X 翻译 PDF 文件">
        <el-radio-group v-model="form.doc2x_flag" @change="handleDoc2xToggle">
          <el-radio-button label="N">禁用</el-radio-button>
          <el-radio-button label="Y">启用</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="form.doc2x_flag === 'Y'" label="Doc2X 密钥" prop="doc2x_secret_key">
        <el-input
          v-model="form.doc2x_secret_key"
          placeholder="输入 Doc2X API Key"
          clearable
          show-password
        />
      </el-form-item>

      <el-form-item>
        <div class="form-actions">
          <el-button type="primary" @click="submitForm">保存设置</el-button>
          <el-button @click="resetForm">重置</el-button>
        </div>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { comparison_my } from '@/api/corpus'
import { useTranslateStore } from '@/store/translate'

const translateStore = useTranslateStore()

const formRef = ref(null)
const termList = ref([])

const form = ref({})

onMounted(() => {
  form.value = {
    comparison_id: translateStore.aiServer.comparison_id,
    type: translateStore.common.type,
    threads: translateStore.common.threads,
    doc2x_flag: translateStore.common.doc2x_flag,
    doc2x_secret_key: translateStore.common.doc2x_secret_key
  }
})

const rules = reactive({
  comparison_id: [{ required: false }],
  type: [{ required: true, message: '请选择译文形式', trigger: 'change' }],
  threads: [
    { required: true, message: '请设置线程数', trigger: 'blur' },
    { type: 'number', min: 1, max: 20, message: '线程数必须在1-20之间', trigger: 'blur' }
  ],
  doc2x_secret_key: [
    { required: form.doc2x_flag === 'Y', message: '请输入Doc2X API Key', trigger: 'blur' }
  ]
})

const fetchTermList = async () => {
  try {
    const res = await comparison_my()
    if (res.code === 200) {
      termList.value = res.data.data
    }
  } catch (error) {
    console.error('获取术语列表失败:', error)
    ElMessage.error('获取术语列表失败')
  }
}

const handleDoc2xToggle = (value) => {
  if (value === 'N') {
    form.value.doc2x_secret_key = ''
  }
  rules.doc2x_secret_key[0].required = value === 'Y'
}

const submitForm = async () => {
  try {
    await formRef.value.validate()
    const submitData = {
      threads: form.value.threads,
      doc2x_flag: form.value.doc2x_flag,
      doc2x_secret_key: form.value.doc2x_secret_key
    }
    translateStore.updateCommonSettings(submitData)
    translateStore.updateAIServerSettings({ comparison_id: form.value.comparison_id })
    ElMessage.success('保存成功!')
  } catch (error) {
    console.error('表单验证失败:', error)
    ElMessage.error('请检查表单填写是否正确')
  }
}

const resetForm = () => {
  formRef.value?.resetFields()
}

onMounted(() => {
  fetchTermList()
})
</script>

<style scoped lang="scss">
.common-settings-container {
  padding: 4px 0;
}

.settings-form {
  max-width: 600px;
}

.form-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  margin: 20px 0 14px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f1f5f9;

  .section-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #3b82f6;
  }
}

.form-actions {
  display: flex;
  gap: 12px;
}
</style>
