<template>
  <div class="security-settings">
    <el-form>
      <el-form-item label="登录邮箱:">
        <div class="email-display">
          {{ email }}
          <el-button type="text">更换邮箱</el-button>
        </div>
      </el-form-item>

      <el-form-item label="登录密码:">
        <el-button @click="$router.push('/reset')">修改密码</el-button>
      </el-form-item>

      <el-form-item label="账号安全:">
        <div class="security-tips">
          <el-icon><Warning /></el-icon>
          <span>请妥善保管您的账号信息，不要泄露给他人</span>
        </div>
      </el-form-item>
    </el-form>

    <!-- 绑定邮箱对话框 -->
    <el-dialog v-model="showBindDialog" title="绑定新邮箱" width="400px">
      <el-form :model="bindForm" label-width="80px">
        <el-form-item label="新邮箱" prop="email">
          <el-input v-model="bindForm.email" placeholder="请输入新邮箱地址"></el-input>
        </el-form-item>
        <el-form-item label="验证码" prop="code">
          <div class="code-input">
            <el-input v-model="bindForm.code" placeholder="请输入验证码"></el-input>
            <el-button type="primary" :disabled="countdown > 0" @click="sendCode">
              {{ countdown > 0 ? `${countdown}秒后重试` : '获取验证码' }}
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
import { Warning } from '@element-plus/icons-vue'

const props = defineProps({
  email: {
    type: String,
    required: true
  }
})

const showBindDialog = ref(false)
const bindForm = ref({
  email: '',
  code: ''
})
const countdown = ref(0)

// 发送验证码
const sendCode = () => {
  // 这里调用API发送验证码
  countdown.value = 60
  const timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(timer)
    }
  }, 1000)
}

// 确认绑定
const confirmBind = () => {
  emit('bind-email', bindForm.value.email)
  showBindDialog.value = false
}
</script>

<style scoped lang="scss">
.security-settings {
  padding: 12px 16px;
  .email-display {
    display: flex;
    align-items: center;

    .el-button {
      margin-left: 10px;
    }
  }

  .security-tips {
    display: flex;
    align-items: center;
    color: #e6a23c;

    .el-icon {
      margin-right: 5px;
    }
  }

  .code-input {
    display: flex;

    .el-input {
      flex: 1;
      margin-right: 10px;
    }
  }
}
</style>
