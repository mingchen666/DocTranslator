<template>
  <div class="security-settings">
    <!-- 卡片容器 -->
    <el-card class="settings-card">
      <!-- 标题区 -->
      <div class="card-header">
        <h2 class="title">账户安全设置</h2>
        <p class="subtitle">请谨慎修改您的账户信息</p>
      </div>

      <!-- 表单区 -->
      <el-form ref="formRef" :model="formData" :rules="rules" label-position="top" class="settings-form">
        <!-- 用户名修改 -->
        <el-form-item label="用户名" prop="user">
          <el-input v-model="formData.user" placeholder="请输入新的用户名(邮箱)" clearable :prefix-icon="User" />
        </el-form-item>

        <!-- 密码修改 -->
        <el-form-item label="原密码" prop="old_password">
          <el-input
            v-model="formData.old_password"
            type="password"
            show-password
            placeholder="请输入当前密码"
            :prefix-icon="Lock"
          />
        </el-form-item>

        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="formData.new_password"
            type="password"
            show-password
            placeholder="6-16位长度"
            :prefix-icon="Key"
          />
        </el-form-item>

        <el-form-item label="确认新密码" prop="confirm_password">
          <el-input
            v-model="formData.confirm_password"
            type="password"
            show-password
            placeholder="请再次输入新密码"
            :prefix-icon="Key"
          />
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item class="form-actions">
          <el-button type="primary" :loading="submitting" @click="handleSubmit"> 保存修改 </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import { User, Lock, Key } from "@element-plus/icons-vue"
import { updatePasswordApi } from "@/api/login"
const formRef = ref()
const submitting = ref(false)
const router = useRouter()
// 表单数据
const formData = reactive({
  user: "",
  old_password: "",
  new_password: "",
  confirm_password: ""
})

// 用户名验证
// const validateUsername = (rule, value, callback) => {
//   if (!value) {
//    callback(new Error("用户名不能为空"))
//    }
//   if (value.length < 6 || value.length > 16) {
//     callback(new Error("用户名长度需在6到16个字符之间"))
//   } else {
//     callback()
//   }
// }

// 密码复杂度验证
const validatePassword = (rule, value, callback) => {
  if (value.length < 6) {
    callback(new Error("密码至少需要6位"))
  } else {
    callback()
  }
}

// 确认密码验证
const validateConfirm = (rule, value, callback) => {
  if (value !== formData.new_password) {
    callback(new Error("两次输入的密码不一致"))
  } else {
    callback()
  }
}

// 表单验证规则
const rules = {
  // user: [{ required: false, validator: validateUsername, trigger: "blur" }],
  old_password: [{ required: true, message: "请输入原密码", trigger: "blur" }],
  new_password: [
    { required: true, message: "请输入新密码", trigger: "blur" },
    { validator: validatePassword, trigger: "blur" }
  ],
  confirm_password: [
    { required: true, message: "请确认新密码", trigger: "blur" },
    { validator: validateConfirm, trigger: "blur" }
  ]
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    // 修改密码请求
    const res = await updatePasswordApi(formData)
    if (res.code === 200) {
      submitting.value = false
      ElMessage.success("修改成功")
      router.push("/login")
    } else {
      submitting.value = false
      ElMessage.error("修改失败，请重试")
    }
  } catch (error) {
    ElMessage.error(error.message || "修改失败")
    submitting.value = false
  }
}

// 重置表单
const handleReset = () => {
  formRef.value.resetFields()
}
</script>

<style lang="scss" scoped>
.security-settings {
  padding: 10px;
  display: flex;
  max-width: 1400px;
  justify-content: center;
  align-items: center;
  height: 100%;
  // min-height: calc(100vh - 64px);
  background-color: #f5f7fa; // 浅灰色背景
}

.settings-card {
  width: 100%;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  width: 50%;
  margin-bottom: 24px;

  .title {
    font-size: 20px;
    font-weight: 600;
    color: #303133;
    margin-bottom: 8px;
  }

  .subtitle {
    font-size: 14px;
    color: #909399;
  }
}

.settings-form {
  width: 40%;

  :deep(.el-form-item__label) {
    font-weight: 500;
    color: #606266;
    padding-bottom: 8px;
  }

  :deep(.el-input__inner) {
    border-radius: 8px;
    transition: border-color 0.3s ease;

    &:hover {
      border-color: #c0c4cc;
    }
  }

  .form-actions {
    margin-top: 32px;
    text-align: center;

    .el-button {
      width: 120px;
      font-size: 14px;
      border-radius: 8px;
    }

    .el-button--primary {
      background-color: #409eff;
      border-color: #409eff;

      &:hover {
        opacity: 0.9;
      }
    }
  }
}
</style>
