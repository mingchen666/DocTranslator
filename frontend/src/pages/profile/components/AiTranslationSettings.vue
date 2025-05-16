<template>
  <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" label-position="top">
    <!-- 服务商选择 -->
    <el-form-item label="服务商" prop="provider">
      <el-radio-group v-model="form.provider">
        <el-radio-button label="openai">OpenAI</el-radio-button>
        <el-radio-button label="member" :disabled="!isVIP">DocTranslator 会员</el-radio-button>
      </el-radio-group>
    </el-form-item>

    <!-- OpenAI配置 -->
    <template v-if="form.provider === 'openai'">
      <el-form-item prop="api_url">
        <template #label>
          <span class="label-with-ad">
            API地址
            <el-tag
              size="mini"
              type="warning"
              style="margin-left: 8px; cursor: pointer; font-size: medium"
              @click="visitSite"
            >
              🔥 推荐使用在线api中转站
            </el-tag>
          </span>
        </template>
        <el-input v-model="form.api_url" placeholder="https://api.ezworkapi.top" clearable />
      </el-form-item>

      <el-form-item label="API密钥" prop="api_key">
        <el-input v-model="form.api_key" placeholder="输入您的API Key" show-password clearable />
      </el-form-item>
    </template>

    <!-- 操作按钮 -->
    <el-form-item>
      <div class="form-actions">
        <el-button type="primary" @click="submitForm" :loading="saving"> 保存设置 </el-button>
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
          <template v-else> 检查连接 </template>
        </el-button>
      </div>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { checkOpenAI } from '@/api/trans'
import { ElMessage } from 'element-plus'
import { useTranslateStore } from '@/store/translate'
const translateStore = useTranslateStore()

const formRef = ref(null)
const form = ref({
  provider: 'openai',
  api_url: '',
  api_key: ''
})

const isVIP = computed(() => useTranslateStore().isVIP)
const saving = ref(false)
const testing = ref(false)
const testResult = ref('')

// 计算按钮类型
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

// 是否可以测试连接
const canTestConnection = computed(() => {
  return form.provider === 'openai' && form.api_url && form.api_key
})

// 测试连接
const testConnection = async () => {
  if (!canTestConnection.value) return

  try {
    testing.value = true
    testResult.value = ''

    const res = await checkOpenAI({
      api_url: form.api_url,
      api_key: form.api_key
    })

    testResult.value = res.code === 200 ? 'success' : 'fail'
  } catch (error) {
    testResult.value = 'fail'
  } finally {
    testing.value = false
  }
}

// 提交表单
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
// 初始化
onMounted(() => {
  form.value = {
    provider: 'openai',
    api_url: translateStore.aiServer.api_url,
    api_key: translateStore.aiServer.api_key
  }
})
</script>

<style scoped lang="scss">
.form-actions {
  display: flex;
  gap: 12px;

  .el-button {
    flex: 1;

    // 成功状态按钮
    &.el-button--success {
      background-color: var(--el-color-success-light-9);
      border-color: var(--el-color-success-light-7);
      color: var(--el-color-success);

      &:hover {
        background-color: var(--el-color-success-light-7);
      }
    }

    // 失败状态按钮
    &.el-button--danger {
      background-color: var(--el-color-danger-light-9);
      border-color: var(--el-color-danger-light-7);
      color: var(--el-color-danger);

      &:hover {
        background-color: var(--el-color-danger-light-7);
      }
    }
  }

  .el-icon {
    margin-right: 6px;
    font-size: 14px;
  }

  .success-icon {
    color: var(--el-color-success);
  }

  .error-icon {
    color: var(--el-color-danger);
  }
}
.ad-banner {
  background-color: #fff8e6;
  padding: 3px 10px;
  border-radius: 4px;
  margin-top: 5px;
  font-size: 12px;
  cursor: pointer;
}
.ad-banner:hover {
  background-color: #fffaf0;
}
@media (max-width: 768px) {
  .label-with-ad {
    display: flex;
    flex-direction: column;
  }
  .ad-banner {
    padding: 5px;
    text-align: center;
  }
}
</style>
