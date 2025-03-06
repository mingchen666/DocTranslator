<template>
  <el-form :model="user" ref="userform" label-width="auto" :rules="rules">
    <el-form-item prop="email" label="邮箱">
      <el-input v-model="user.email" placeholder="请输入邮箱" autocomplete="new-password" />
    </el-form-item>
    <el-form-item prop="level" label="用户等级">
      <el-select v-model="user.level" placeholder="">
        <el-option label="会员用户" value="vip" />
        <el-option label="普通用户" value="common" />
      </el-select>
    </el-form-item>
    <el-form-item prop="password" label="密码">
      <el-input type="password" v-model="user.password" placeholder="请输入" autocomplete="new-password" />
    </el-form-item>
    <el-form-item label="" class="center">
      <el-button type="primary" size="large" color="#055CF9" @click="doRegister()" style="width: 100%">提交</el-button>
    </el-form-item>
  </el-form>
</template>
<script setup lang="ts">
import { ref, reactive, defineEmits } from "vue"
import { registerCustomer } from "@/api/customer/index"
import { FormInstance, ElMessage } from "element-plus"
import { CreateOrUpdateCustomerRequestData } from "@/api/customer/types/customer"
import { cloneDeep } from "lodash-es"

const emit = defineEmits(["success"])

const DEFAULT_FORM_DATA: CreateOrUpdateCustomerRequestData = {
  email: "",
  password: "",
  level: "common"
}

const user = ref<CreateOrUpdateCustomerRequestData>(cloneDeep(DEFAULT_FORM_DATA))

const userform = ref<FormInstance | null>(null)
const rules = reactive({
  email: [{ required: true, message: "请填写邮箱地址", trigger: "blur" }],
  level: [{ required: true, message: "请填写用户等级" }],
  password: [{ required: true, message: "请填写密码", trigger: "blur" }]
})
const doRegister = () => {
  userform.value?.validate((valid: boolean, fields: any) => {
    if (!valid) return console.error("表单校验不通过", fields)
    registerCustomer(user.value)
      .then(() => {
        ElMessage.success("操作成功")
        emit("success")
        user.value = cloneDeep(DEFAULT_FORM_DATA)
      })
      .finally(() => {})
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
