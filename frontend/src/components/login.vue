<template>
  <el-form :model="user" label-width="auto" ref="form" :show-message="false" :rules="rules">
    <el-form-item label="" required prop="email">
      <el-input v-model="user.email" placeholder="邮箱" />
    </el-form-item>
    <el-form-item label="" required prop="password">
      <el-input v-model="user.password" type="password" show-password placeholder="密码" />
    </el-form-item>
    <div class="flex_right">
      <el-text class="forget" @click="doForget">忘记密码?</el-text>
    </div>
    <el-form-item label="" class="center">
      <el-button type="primary" size="large" color="#055CF9" @click="doLogin(form)" style="width: 100%">登录</el-button>
    </el-form-item>
  </el-form>
</template>
<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { login } from '@/api/auth'
import { store } from '@/store/index'
const emit = defineEmits(['forget', 'success'])
const form = ref()
const user = reactive({
  email: '',
  password: '',
})
const rules = reactive({
  email: [{ required: true, message: '请填写邮箱地址', trigger: 'blur' }],
  password: [{ required: true, message: '请填写密码', trigger: 'blur' }],
})
function doLogin(form) {
  form.validate((valid, fields) => {
    if (valid) {
      login(user)
        .then((data) => {
          if (data.code == 200) {
            store.setToken(data.data.token)
            store.setUsername(data.data.email)
            store.setLevel(data.data.level)
            emit('success')
          } else {
            ElMessage({
              message: data.message,
              type: 'error',
            })
          }
        })
        .catch((data) => {
          console.log(data)
        })
    } else {
      ElMessage({
        message: fields[Object.keys(fields)[0]][0]['message'],
        type: 'error',
      })
    }
  })
}
function doForget() {
  emit('forget')
}
</script>
<style scoped lang="scss">
.forget {
  display: inline-block;
  font-family: 'PingFang SC';
  font-weight: 400;
  font-size: 12px;
  color: #111111;
  cursor: pointer;
  line-height: 14px;
  margin-bottom: 20px;
}
::v-deep {
  .right .el-form-item__content {
    justify-content: end;
  }
  .center .el-form-item__content {
    justify-content: center;
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
