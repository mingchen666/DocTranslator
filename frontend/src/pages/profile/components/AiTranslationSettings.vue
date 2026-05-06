<template>
  <div class="ai-settings-container">
    <VipCard v-if="isVIP" />
    <el-form
      v-else
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
      class="settings-form"
    >
      <el-form-item label="服务商" prop="provider">
        <el-radio-group v-model="form.provider" class="provider-group">
          <el-radio-button label="openai" :disabled="isVIP">
            <div class="provider-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4z"/></svg>
              <span>OpenAI</span>
            </div>
          </el-radio-button>
          <el-radio-button label="member" :disabled="!isVIP">
            <div class="provider-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
              <span>会员服务</span>
            </div>
          </el-radio-button>
        </el-radio-group>
      </el-form-item>

      <template v-if="form.provider === 'openai'">
        <el-form-item prop="api_url">
          <template #label>
            <span class="label-with-ad">
              API 地址
              <el-tag
                size="small"
                type="warning"
                effect="light"
                style="margin-left: 8px; cursor: pointer;"
                @click="visitSite"
              >
                推荐中转站
              </el-tag>
            </span>
          </template>
          <el-input v-model="form.api_url" placeholder="须以 /v1 结尾，如 https://api.ezworkapi.top/v1" clearable />
        </el-form-item>
        <el-form-item label="API 密钥" prop="api_key">
          <el-input v-model="form.api_key" placeholder="输入您的 API Key" show-password clearable />
        </el-form-item>
      </template>

      <el-form-item>
        <div class="form-actions">
          <el-button type="primary" @click="submitForm" :loading="saving">保存设置</el-button>
          <el-button
            :type="testButtonType"
            @click="testConnection"
            :loading="testing"
            :disabled="!canTestConnection"
          >
            <template v-if="testResult === 'success'">
              <el-icon class="success-icon"><CircleCheck /></el-icon> 连接正常
            </template>
            <template v-else-if="testResult === 'fail'">
              <el-icon class="error-icon"><CircleClose /></el-icon> 连接失败
            </template>
            <template v-else>检查连接</template>
          </el-button>
        </div>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { checkOpenAI } from '@/api/trans'
import { ElMessage } from 'element-plus'
import VipCard from './VipCard.vue'
import { useTranslateStore } from '@/store/translate'
import { useUserStore } from '@/store/user'

const translateStore = useTranslateStore()
const userStore = useUserStore()

const formRef = ref(null)
const form = ref({
  provider: 'openai',
  api_url: '',
  api_key: ''
})

const isVIP = computed(() => userStore.isVip)
const saving = ref(false)
const testing = ref(false)
const testResult = ref('')

const testButtonType = computed(() => {
  if (testResult.value === 'success') return 'success'
  if (testResult.value === 'fail') return 'danger'
  return ''
})

const visitSite = () => {
  window.open('https://api.ezworkapi.top', '_blank')
}

const rules = {
  provider: [{ required: true, message: '请选择服务商', trigger: 'change' }],
  api_url: [{ required: true, message: '请输入API地址', trigger: 'blur' }],
  api_key: [{ required: true, message: '请输入API Key', trigger: 'blur' }]
}

const canTestConnection = computed(() => {
  return form.value.provider === 'openai' && form.value.api_url && form.value.api_key
})

const testConnection = async () => {
  if (!canTestConnection.value) return
  try {
    testing.value = true
    testResult.value = ''
    const res = await checkOpenAI({
      api_url: form.value.api_url,
      api_key: form.value.api_key
    })
    testResult.value = res.code === 200 ? 'success' : 'fail'
  } catch (error) {
    testResult.value = 'fail'
  } finally {
    testing.value = false
  }
}

const submitForm = async () => {
  try {
    await formRef.value.validate()
    saving.value = true
    translateStore.updateAIServerSettings({
      api_url: form.value.api_url,
      api_key: form.value.api_key
    })
    ElMessage.success('保存成功!')
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  form.value = {
    provider: 'openai',
    api_url: translateStore.aiServer.api_url,
    api_key: translateStore.aiServer.api_key
  }
})
</script>

<style scoped lang="scss">
.ai-settings-container {
  padding: 4px 0;
}

.settings-form {
  max-width: 600px;
}

.provider-group {
  .provider-btn {
    display: flex;
    align-items: center;
    gap: 6px;

    svg {
      flex-shrink: 0;
    }
  }
}

.label-with-ad {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.form-actions {
  display: flex;
  gap: 12px;

  .el-button {
    min-width: 120px;
  }

  .el-icon {
    margin-right: 4px;
    font-size: 14px;
  }

  .success-icon {
    color: var(--el-color-success);
  }

  .error-icon {
    color: var(--el-color-danger);
  }
}

@media (max-width: 576px) {
  .form-actions {
    flex-direction: column;

    .el-button {
      width: 100%;
    }
  }
}
</style>
