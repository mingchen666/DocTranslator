<template>
  <div class="change-password-page">
    <div class="change-password-container">
      <div class="change-password-header">
        <h1 class="change-password-title">修改密码</h1>
        <p class="change-password-subtitle">请填写以下信息以修改您的密码</p>
      </div>
      <el-form
        ref="form"
        :model="user"
        :show-message="false"
        :rules="rules"
        @keyup.enter="doChangePassword(form)"
      >
        <el-form-item label="" prop="oldpwd">
          <el-input
            v-model="user.oldpwd"
            type="password"
            show-password
            placeholder="原密码"
            prefix-icon="el-icon-lock"
          />
        </el-form-item>
        <el-form-item label="" prop="newpwd">
          <el-input
            v-model="user.newpwd"
            type="password"
            show-password
            placeholder="设置新密码"
            prefix-icon="el-icon-lock"
          />
        </el-form-item>
        <el-form-item label="" prop="newpwd_confirmation">
          <el-input
            v-model="user.newpwd_confirmation"
            type="password"
            show-password
            placeholder="确认新密码"
            prefix-icon="el-icon-lock"
          />
        </el-form-item>
        <el-form-item label="" class="center">
          <el-button
            type="primary"
            size="large"
            class="change-password-btn"
            @click="doChangePassword(form)"
          >
            提交
          </el-button>
        </el-form-item>
        <!-- 添加忘记密码链接 -->
        <div class="forgot-password-link">
          <el-link type="primary" @click="$router.push('/forget')">忘记密码？</el-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { changePassword } from '@/api/account'

const router = useRouter()
const form = ref()

// 表单数据
const user = reactive({
  oldpwd: '',
  newpwd: '',
  newpwd_confirmation: ''
})

// 表单验证规则
const rules = reactive({
  oldpwd: [{ required: true, message: '请填写原密码', trigger: 'blur' }],
  newpwd: [{ required: true, message: '请填写新密码', trigger: 'blur' }],
  newpwd_confirmation: [{ required: true, message: '请填写确认密码', trigger: 'blur' }]
})

// 提交修改密码
const doChangePassword = async (form) => {
  form.validate((valid, fields) => {
    if (valid) {
      if (user.newpwd !== user.newpwd_confirmation) {
        ElMessage.error('两次密码输入不一致')
        return
      }
      changePassword(user)
        .then((data) => {
          if (data.code === 200) {
            ElMessage.success('密码修改成功')
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
</script>

<style scoped lang="scss">
.change-password-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #6a11cb, #2575fc);
  padding: 20px;
}

.change-password-container {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 30px;
}

.change-password-header {
  text-align: center;
  margin-bottom: 24px;
}

.change-password-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.change-password-subtitle {
  font-size: 14px;
  color: #666;
}

.change-password-btn {
  width: 100%;
  background: linear-gradient(135deg, #6a11cb, #2575fc);
  border: none;
  transition: all 0.3s ease;
  &:hover {
    opacity: 0.9;
  }
}

// 忘记密码链接样式
.forgot-password-link {
  text-align: center;
  margin-top: 16px;
  .el-link {
    font-size: 14px;
  }
}
</style>
