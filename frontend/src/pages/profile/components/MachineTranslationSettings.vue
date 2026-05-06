<template>
  <div class="machine-settings-container">
    <VipCard v-if="isVIP" />
    <el-form v-else ref="formRef" :model="form" :rules="rules" label-position="top" class="settings-form">
      <el-form-item label="翻译引擎" prop="provider">
        <el-select v-model="form.provider" placeholder="选择翻译引擎" style="width: 100%">
          <el-option label="百度翻译" value="baidu">
            <div class="engine-option">
              <span class="engine-name">百度翻译</span>
              <span class="engine-desc">国内稳定</span>
            </div>
          </el-option>
          <el-option label="有道翻译" value="youdao">
            <div class="engine-option">
              <span class="engine-name">有道翻译</span>
              <span class="engine-desc">词典丰富</span>
            </div>
          </el-option>
          <el-option label="Google翻译" value="google">
            <div class="engine-option">
              <span class="engine-name">Google翻译</span>
              <span class="engine-desc">多语言支持</span>
            </div>
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="App ID" prop="app_id">
        <el-input v-model="form.app_id" placeholder="输入应用 ID" clearable />
      </el-form-item>

      <el-form-item label="App Key" prop="app_key">
        <el-input v-model="form.app_key" placeholder="输入应用密钥" show-password clearable />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="submitForm">保存设置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { onMounted, ref, computed } from 'vue'
import VipCard from './VipCard.vue'
import { useTranslateStore } from '@/store/translate'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const isVIP = computed(() => userStore.isVip)
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

<style scoped lang="scss">
.machine-settings-container {
  padding: 4px 0;
}

.settings-form {
  max-width: 600px;
}

.engine-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;

  .engine-name {
    font-size: 14px;
    color: #334155;
  }

  .engine-desc {
    font-size: 12px;
    color: #94a3b8;
  }
}
</style>
