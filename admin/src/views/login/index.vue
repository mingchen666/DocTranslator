<script lang="ts" setup>
import { reactive, ref } from "vue"
import { useRouter } from "vue-router"
import { useUserStore } from "@/store/modules/user"
import { type FormInstance, type FormRules } from "element-plus"
//import { getLoginCodeApi } from "@/api/login"
import { type LoginRequestData } from "@/api/login/types/login"

const router = useRouter()
/** 登录表单元素的引用 */
const loginFormRef = ref<FormInstance | null>(null)

/** 登录按钮 Loading */
const loading = ref(false)
/** 验证码图片 URL */
//const codeUrl = ref("")
/** 登录表单数据 */
const loginFormData: LoginRequestData = reactive({
  email: "",
  password: ""
  // code: ""
})
/** 登录表单校验规则 */
const loginFormRules: FormRules = {
  email: [{ required: true, message: "请输入登录邮箱", trigger: "blur" }],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, max: 16, message: "长度在 6 到 16 个字符", trigger: "blur" }
  ]
  // code: [{ required: true, message: "请输入验证码", trigger: "blur" }]
}
/** 登录逻辑 */
const handleLogin = () => {
  loginFormRef.value?.validate((valid: boolean, fields) => {
    if (valid) {
      loading.value = true
      useUserStore()
        .login(loginFormData)
        .then(() => {
          router.push({ path: "/" })
        })
        .catch(() => {
          loginFormData.password = ""
        })
        .finally(() => {
          loading.value = false
        })
    } else {
      console.error("表单校验不通过", fields)
    }
  })
}
/** 创建验证码 */
/*const createCode = () => {
  // 先清空验证码的输入
  // loginFormData.code = ""
  // 获取验证码
  codeUrl.value = ""
  getLoginCodeApi().then((res) => {
    codeUrl.value = res.data
  })
}*/

/** 初始化验证码 */
// createCode()
</script>

<template>
  <div class="login-container">
    <img class="login_bg" src="@/assets/login/login_bg.png" alt="" />

    <div class="login-card">
      <div class="title">
        <img src="@/assets/login/login_title.png" />
      </div>
      <div class="content">
        <el-form
          ref="loginFormRef"
          label-position="top"
          :hide-required-asterisk="true"
          :model="loginFormData"
          :rules="loginFormRules"
          @keyup.enter="handleLogin"
        >
          <el-form-item label="用户名" prop="email">
            <el-input
              v-model.trim="loginFormData.email"
              placeholder="请输入登录邮箱"
              type="text"
              tabindex="1"
              size="large"
            />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              v-model.trim="loginFormData.password"
              placeholder="密码"
              type="password"
              tabindex="2"
              size="large"
              show-password
            />
          </el-form-item>
          <!-- <el-form-item prop="code">
            <el-input
              v-model.trim="loginFormData.code"
              placeholder="验证码"
              type="text"
              tabindex="3"
              :prefix-icon="Key"
              maxlength="7"
              size="large"
            >
              <template #append>
                <el-image :src="codeUrl" @click="createCode" draggable="false">
                  <template #placeholder>
                    <el-icon>
                      <Picture />
                    </el-icon>
                  </template>
                  <template #error>
                    <el-icon>
                      <Loading />
                    </el-icon>
                  </template>
                </el-image>
              </template>
            </el-input>
          </el-form-item> -->
          <el-button :loading="loading" type="primary" size="large" @click.prevent="handleLogin">登 录</el-button>
        </el-form>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.login-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  min-height: 100%;
  .login_bg {
    position: absolute;
    width: 100%;
    height: 100%;
  }
  .login-card {
    position: relative;
    z-index: 99;
    width: 432px;
    max-width: 85%;
    background: #ffffff;
    box-shadow: 0px 2px 15px 0px rgba(0, 0, 0, 0.15);
    border-radius: 16px;
    overflow: hidden;
    padding: 36px;
    .title {
      display: flex;
      justify-content: left;
      align-items: center;
      height: 48px;
      margin-top: 12px;
      img {
        height: 100%;
      }
    }
    .content {
      padding: 0;
      .el-button {
        width: 100%;
        margin-top: 30px;
        background: #045cf9;
        margin-bottom: 30px;
        font-size: 18px;
      }
      .el-form-item {
        margin-top: 25px;
        :deep(.el-form-item__label) {
          font-weight: bold;
          font-size: 16px;
          color: #00334d;
        }
      }
    }
  }
}
</style>
