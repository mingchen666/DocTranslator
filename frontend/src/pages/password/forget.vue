<template>
  <div class="forget-page">
    <div class="forget-container">
      <div class="forget-header">
        <h1 class="forget-title">忘记密码</h1>
        <p class="forget-subtitle">请输入您的邮箱以重置密码</p>
      </div>
      <el-form
        ref="form"
        :model="user"
        :show-message="false"
        :rules="rules"
        @keyup.enter="doForget(form)"
      >
        <el-form-item label="" prop="email">
          <el-input v-model="user.email" placeholder="输入邮箱" prefix-icon="el-icon-message" />
        </el-form-item>
        <el-form-item label="" prop="code">
          <el-input v-model="user.code" placeholder="邮箱验证码" prefix-icon="el-icon-key">
            <template #suffix>
              <el-button type="text" class="code-btn" @click="sendCode" :disabled="codeDisabled">
                {{ codeText }}
              </el-button>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="" prop="password">
          <el-input v-model="user.password" type="password" show-password placeholder="设置新密码" prefix-icon="el-icon-lock" />
        </el-form-item>
        <el-form-item label="" prop="password_confirmation">
          <el-input v-model="user.password_confirmation" type="password" show-password placeholder="确认新密码" prefix-icon="el-icon-lock" />
        </el-form-item>
        <el-form-item label="" class="center">
          <el-button type="primary" size="large" class="forget-btn" @click="doForget(form)">
            提交
          </el-button>
        </el-form-item>
        <div class="forget-actions">
          <el-link type="primary" class="return-link" @click="goToLogin">返回登录</el-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { forgetSendEmail, forget } from '@/api/auth'

const router = useRouter()
const form = ref()

// 表单数据
const user = reactive({
  email: '',
  code: '',
  password: '',
  password_confirmation: '',
})

// 表单验证规则
const rules = reactive({
  email: [{ required: true, message: '请填写邮箱地址', trigger: 'blur' }],
  code: [{ required: true, message: '请填写邮箱验证码', trigger: 'blur' }],
  password: [{ required: true, message: '请填写新密码', trigger: 'blur' }],
  password_confirmation: [{ required: true, message: '请填写确认密码', trigger: 'blur' }],
})

// 验证码相关
const codeText = ref('发送')
const codeDisabled = ref(false)
const sendCode = async () => {
  if (codeDisabled.value) return
  if (!user.email.trim()) {
    ElMessage.error('请填写邮箱地址')
    return
  }

  try {
    await forgetSendEmail(user.email)
    ElMessage.success('验证码已发送')
    codeDisabled.value = true
    let count = 60
    codeText.value = `${count}s`
    const timer = setInterval(() => {
      if (count <= 0) {
        clearInterval(timer)
        codeDisabled.value = false
        codeText.value = '发送'
        return
      }
      count--
      codeText.value = `${count}s`
    }, 1000)
  } catch (error) {
    ElMessage.error(error.message)
  }
}

// 提交忘记密码
const doForget = async (form) => {
  form.validate((valid, fields) => {
    if (valid) {
      if (user.password !== user.password_confirmation) {
        ElMessage.error('两次密码输入不一致')
        return
      }
      forget(user)
        .then((data) => {
          if (data.code === 200) {
            ElMessage.success('密码重置成功')
            router.push({ name: 'login' }) // 成功后跳转到登录页
          } else {
            ElMessage.error(data.message)
          }
        })
        .catch((error) => {
          ElMessage.error(error.message)
        })
    } else {
      ElMessage.error(fields[Object.keys(fields)[0]][0].message)
    }
  })
}

// 返回登录页
const goToLogin = () => {
  router.push({ name: 'login' })
}
</script>

<style scoped lang="scss">
.forget-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #6a11cb, #2575fc);
  padding: 20px;
}

.forget-container {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 30px;
}

.forget-header {
  text-align: center;
  margin-bottom: 24px;
}

.forget-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.forget-subtitle {
  font-size: 14px;
  color: #666;
}

.forget-actions {
  margin-top: 20px;
  text-align: center;
}

.return-link {
  font-size: 14px;
  color: #2575fc;
}

.forget-btn {
  width: 100%;
  background: linear-gradient(135deg, #6a11cb, #2575fc);
  border: none;
  transition: all 0.3s ease;
  &:hover {
    opacity: 0.9;
  }
}

.code-btn {
  font-size: 14px;
  font-weight: bolder;
  color: #2575fc;
  padding: 0;
}
</style>
