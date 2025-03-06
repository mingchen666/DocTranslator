<template>
  <el-form ref="form" :model="user" label-width="auto" :show-message="false" :rules="rules">
    <el-form-item label="" prop="email" required>
      <el-input v-model="user.email" placeholder="输入邮箱"></el-input>
    </el-form-item>
    <el-form-item label="" prop="code" required>
      <el-input v-model="user.code" placeholder="邮箱验证码">
        <template #suffix>
          <el-button type="text" color="#055CF9" class="email-send-btn" @click="send">{{ send_text }}</el-button>
        </template>
      </el-input>
    </el-form-item>
    <el-form-item label="" prop="password" required>
      <el-input v-model="user.password" type="password" show-password placeholder="设置新密码" />
    </el-form-item>
    <el-form-item label="" prop="password_confirmation" required>
      <el-input v-model="user.password_confirmation" type="password" show-password placeholder="确认新密码" />
    </el-form-item>
    <el-form-item label="" class="center">
      <el-button type="primary" size="large" color="#055CF9" @click="doForget(form)" style="width: 100%">
        提交
      </el-button>
    </el-form-item>
    <div class="flex_right">
      <el-text class="login" @click="doReturn">返回登录</el-text>
    </div>
  </el-form>
</template>
<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { forgetSendEmail, forget } from '@/api/auth'
const emit = defineEmits(['return', 'success'])
const user = reactive({
  email: '',
  code: '',
  password: '',
  password_confirmation: '',
})
const send_text = ref('发送')
const seconds = ref('60')
const disabled = ref(false)
const form = ref()
const rules = reactive({
  email: [{ required: true, message: '请填写邮箱地址', trigger: 'blur' }],
  code: [{ required: true, message: '请填写邮箱验证码', trigger: 'blur' }],
  password: [{ required: true, message: '请填写密码', trigger: 'blur' }],
  password_confirmation: [{ required: true, message: '请填写确认密码', trigger: 'blur' }],
})
function doForget(form) {
  form.validate((valid, fields) => {
    if (valid) {
      if (user.password != user.password_confirmation) {
        ElMessage({
          message: '两次密码输入不一致',
          type: 'error',
        })
        return
      }
      forget(user).then((data) => {
        if (data.code == 200) {
          emit('success')
        } else {
          ElMessage({
            message: data.message,
            type: 'error',
          })
        }
      })
    } else {
      ElMessage({
        message: fields[Object.keys(fields)[0]][0]['message'],
        type: 'error',
      })
    }
  })
}
function doReturn() {
  emit('return')
}
function send() {
  if (disabled.value) {
    return
  }
  if (user.email.trim().length == 0) {
    ElMessage({
      message: '请填写邮箱地址',
      type: 'error',
    })
    return
  }
  disabled.value = true
  forgetSendEmail(user.email)
    .then((data) => {
      if (data.code == 200) {
        send_text.value = seconds.value + 's'
        var timer = setInterval(function () {
          let s = parseInt(seconds.value)
          if (s > 0) {
            seconds.value = parseInt(seconds.value) - 1
            send_text.value = seconds.value + 's'
          } else {
            disabled.value = false
            clearInterval(timer)
            send_text.value = '发送'
          }
        }, 1000)
      } else {
        ElMessage({
          message: data.message,
          type: 'error',
        })
        disabled.value = false
      }
    })
    .catch(() => {
      disabled.value = false
    })
}
</script>
<style scoped lang="scss">
::v-deep {
  .right .el-form-item__content {
    justify-content: end;
  }
  .center .el-form-item__content {
    justify-content: center;
  }
  .email-send-btn {
    font-weight: 400;
    font-size: 14px;
    color: #055cf9;
    line-height: 24px;
  }
  .login {
    font-family: 'PingFang SC';
    font-weight: 400;
    font-size: 14px !important;
    color: #055cf9 !important;
    line-height: 18px;
    cursor: pointer;
    margin-bottom: 10px;
  }
  .flex_right {
    display: flex;
    justify-content: flex-end;
  }
  .el-form-item {
    margin-bottom: 12px;
  }
}
</style>
