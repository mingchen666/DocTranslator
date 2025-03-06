<template>
  <el-form :model="user" ref="form" label-width="auto" :show-message="false" :rules="rules">
    <el-form-item label="" required prop="email">
      <el-input v-model="user.email" placeholder="输入邮箱" />
    </el-form-item>
    <el-form-item label="" required prop="code">
      <el-input v-model="user.code" placeholder="邮箱验证码">
        <template #suffix>
          <el-button type="text" color="#055CF9" class="email-send-btn" @click="send">{{ send_text }}</el-button>
        </template>
      </el-input>
    </el-form-item>
    <el-form-item label="" required prop="password">
      <el-input v-model="user.password" type="password" show-password placeholder="输入密码" />
    </el-form-item>
    <el-form-item label="" required prop="password2">
      <el-input v-model="user.password2" type="password" show-password placeholder="确认输入密码" />
    </el-form-item>
    <el-form-item label="" class="center">
      <el-button type="primary" size="large" color="#055CF9" @click="doRegister(form)" style="width: 100%">
        提交
      </el-button>
    </el-form-item>
  </el-form>
</template>
<script setup>
import { ref, reactive, defineEmits } from 'vue'
import { registerSendEmail, register } from '@/api/auth'
import { ElMessage } from 'element-plus'
import { store } from '@/store/index'

const emit = defineEmits(['success'])
const user = reactive({
  email: '',
  code: '',
  password: '',
  password2: '',
})
const form = ref()
const rules = reactive({
  email: [{ required: true, message: '请填写邮箱地址', trigger: 'blur' }],
  code: [{ required: true, message: '请填写邮箱验证码', trigger: 'blur' }],
  password: [{ required: true, message: '请填写密码', trigger: 'blur' }],
  password2: [{ required: true, message: '请填写确认密码', trigger: 'blur' }],
})
const send_text = ref('发送')
const seconds = ref('60')
const disabled = ref(false)
function doRegister(form) {
  form.validate((valid, fields) => {
    if (valid) {
      if (user.password != user.password2) {
        ElMessage({
          message: '两次密码输入不一致',
          type: 'error',
        })
        return
      }
      register(user).then((data) => {
        if (data.code == 200) {
          store.setToken(data.data.token)
          store.setUsername(data.data.email)
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
  registerSendEmail(user.email)
    .then((data) => {
      if (data.code == 200) {
        send_text.value = seconds.value + 's'
        var timer = setInterval(function () {
          let s = parseInt(seconds.value)
          if (s > 0) {
            seconds.value = parseInt(seconds.value) - 1
            send_text.value = seconds.value + 's'
          } else {
            clearInterval(timer)
            disabled.value = false
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
:v-deep {
  .right .el-form-item__content {
    justify-content: end;
  }
  .center .el-form-item__content {
    justify-content: center;
  }
}
</style>
