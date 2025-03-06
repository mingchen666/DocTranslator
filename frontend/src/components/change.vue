<template>
  <el-form ref="form" :model="user" label-width="auto" :show-message="false" :rules="rules">
    <el-form-item label="" prop="oldpwd" required>
      <el-input v-model="user.oldpwd" type="password" show-password placeholder="原密码" />
    </el-form-item>
    <el-form-item label="" prop="newpwd" required>
      <el-input v-model="user.newpwd" type="password" show-password placeholder="设置新密码" />
    </el-form-item>
    <el-form-item label="" prop="newpwd_confirmation" required>
      <el-input v-model="user.newpwd_confirmation" type="password" show-password placeholder="确认新密码" />
    </el-form-item>
    <el-form-item label="" class="center">
      <el-button type="primary" size="large" color="#055CF9" @click="doForget(form)" style="width: 100%">
        提交
      </el-button>
    </el-form-item>
  </el-form>
</template>
<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { changePassword } from '@/api/account'
const emit = defineEmits(['success'])
const user = reactive({
  email: '',
  code: '',
  oldpwd: '',
  newpwd: '',
  newpwd_confirmation: '',
})
// const send_text=ref("发送")
// const seconds=ref("60")
const disabled = ref(false)
const form = ref()
const rules = reactive({
  oldpwd: [{ required: true, message: '请填写旧密码', trigger: 'blur' }],
  // code: [
  //     { required: true, message: '请填写邮箱验证码', trigger: 'blur' },
  // ],
  newpwd: [{ required: true, message: '请填写密码', trigger: 'blur' }],
  newpwd_confirmation: [{ required: true, message: '请填写确认密码', trigger: 'blur' }],
})
function doForget(form) {
  form.validate((valid, fields) => {
    if (valid) {
      if (user.newpwd != user.newpwd_confirmation) {
        ElMessage({
          message: '两次密码输入不一致',
          type: 'error',
        })
        return
      }
      changePassword(user).then((data) => {
        if (data.code == 200) {
          ElMessage({
            message: '修改成功',
            type: 'success',
          })
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
// function doReturn(){
//     emit('return')
// }
// function send(){
//     if(disabled.value){
//         return
//     }
//     if(user.email.trim().length==0){
//         ElMessage({
//             message:"请填写邮箱地址",
//             type:"error",
//         })
//         return
//     }
//     disabled.value=true
//     forgetSendEmail(user.email).then(data=>{
//         if(data.code==0){
//             send_text.value=seconds.value+"s"
//             var timer=setInterval(function(){
//                 let s=parseInt(seconds.value)
//                 if(s>0){
//                     seconds.value=parseInt(seconds.value)-1
//                     send_text.value=seconds.value+"s"
//                 }else{
//                     disabled.value=false
//                     clearInterval(timer)
//                     send_text.value="发送"
//                 }
//             },1000)
//         }else{
//             ElMessage({
//                 message:data.msg,
//                 type:"error",
//             })
//             disabled.value=false
//         }
//     }).catch(()=>{
//         disabled.value=false
//     })
// }
</script>
<style scoped lang="scss">
:v-deep {
  .right .el-form-item__content {
    justify-content: end;
  }
  .center .el-form-item__content {
    justify-content: center;
  }
  .btn {
    width: 100%;
  }
}
</style>
