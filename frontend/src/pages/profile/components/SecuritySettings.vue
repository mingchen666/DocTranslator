<template>
  <div class="security-settings">
    <div class="section-header">
      <div>
        <h3>账号安全</h3>
        <p class="subtitle">管理您的账号安全设置</p>
      </div>
    </div>

    <div class="security-list">
      <div class="security-item">
        <div class="security-item-left">
          <div class="security-item-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
          </div>
          <div class="security-item-info">
            <span class="item-title">登录邮箱</span>
            <span class="item-desc">{{ email || '未绑定邮箱' }}</span>
          </div>
        </div>
        <div class="security-item-right">
          <el-button text type="primary" size="small" @click="showBindDialog = true">更换邮箱</el-button>
        </div>
      </div>

      <div class="security-item">
        <div class="security-item-left">
          <div class="security-item-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
          </div>
          <div class="security-item-info">
            <span class="item-title">登录密码</span>
            <span class="item-desc">定期更换密码可以保护账号安全</span>
          </div>
        </div>
        <div class="security-item-right">
          <el-button text type="primary" size="small" @click="$router.push('/password')">修改密码</el-button>
        </div>
      </div>

      <div class="security-item">
        <div class="security-item-left">
          <div class="security-item-icon warning">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          </div>
          <div class="security-item-info">
            <span class="item-title">安全提示</span>
            <span class="item-desc warning-text">请妥善保管您的账号信息，不要泄露给他人</span>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="showBindDialog" title="绑定新邮箱" width="420px" :close-on-click-modal="false" class="security-dialog">
      <el-form :model="bindForm" label-position="top">
        <el-form-item label="新邮箱">
          <el-input v-model="bindForm.email" placeholder="请输入新邮箱地址" />
        </el-form-item>
        <el-form-item label="验证码">
          <div class="code-input-row">
            <el-input v-model="bindForm.code" placeholder="请输入验证码" />
            <el-button type="primary" :disabled="countdown > 0" @click="sendCode">
              {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBindDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmBind">确认绑定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  email: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['bind-email'])

const showBindDialog = ref(false)
const bindForm = ref({
  email: '',
  code: ''
})
const countdown = ref(0)

const sendCode = () => {
  countdown.value = 60
  const timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(timer)
    }
  }, 1000)
}

const confirmBind = () => {
  emit('bind-email', bindForm.value.email)
  showBindDialog.value = false
}
</script>

<style scoped lang="scss">
.security-settings {
  padding: 4px 0;
}

.section-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 24px;

  h3 {
    font-size: 18px;
    font-weight: 600;
    color: #1e293b;
    margin: 0 0 2px;
  }

  .subtitle {
    font-size: 13px;
    color: #94a3b8;
    margin: 0;
  }
}

.security-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.security-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  transition: all 0.2s ease;

  &:hover {
    border-color: #cbd5e1;
  }

  & + & {
    margin-top: -1px;
    border-radius: 12px;
  }

  .security-item-left {
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .security-item-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    background: #eff6ff;
    color: #3b82f6;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    &.warning {
      background: #fdf6ec;
      color: #e6a23c;
    }
  }

  .security-item-info {
    .item-title {
      display: block;
      font-size: 14px;
      font-weight: 500;
      color: #1e293b;
      margin-bottom: 2px;
    }

    .item-desc {
      display: block;
      font-size: 12px;
      color: #94a3b8;

      &.warning-text {
        color: #e6a23c;
      }
    }
  }
}

.code-input-row {
  display: flex;
  gap: 10px;
  width: 100%;

  .el-input {
    flex: 1;
  }
}

@media (max-width: 576px) {
  .security-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;

    .security-item-right {
      align-self: flex-end;
    }
  }
}
</style>
