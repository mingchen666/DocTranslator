<template>
  <div class="auth-page">
    <!-- 装饰背景球（极淡，增加层次感） -->
    <div class="bg-shape shape-1"></div>
    <div class="bg-shape shape-2"></div>

    <div class="auth-box">
      <!-- 左侧：品牌与开源信息 -->
      <div class="auth-sidebar">
        <div class="sidebar-top">
          <!-- Logo和名称放一行 -->
          <div class="brand-header">
            <img src="@/assets/logo.png" alt="Logo" class="brand-logo" />
            <span class="brand-name">DocTranslator</span>
          </div>

          <div class="brand-slogan">
            <p class="main-slogan">AI文档智能翻译平台</p>
            <p class="sub-slogan">一站式文档翻译平台</p>
          </div>

          <div class="feature-list">
            <div class="feature-item">
              <el-icon><Connection /></el-icon>
              <span>开源项目，社区支持</span>
            </div>
            <div class="feature-item">
              <el-icon><Lock /></el-icon>
              <span>支持本地/云端部署</span>
            </div>
            <div class="feature-item">
              <el-icon><Document /></el-icon>
              <span>支持定制化功能开发</span>
            </div>
          </div>
        </div>

        <div class="sidebar-footer">
          <div class="copyright-info">
            <a href="https://www.doctranslator.cn" target="_blank" class="github-link">
              <p class="copyright">© 2025 DocTranslator 1.4.3 保留所有权利</p>
              <!-- 未经同意，不得删除。 -->
            </a>
          </div>
        </div>
      </div>

      <!-- 右侧：登录/注册表单 -->
      <div class="auth-form-container">
        <!-- 移动端专用头部 -->
        <div class="mobile-header">
          <div class="mobile-brand">
            <img src="@/assets/logo.png" alt="Logo" class="mobile-logo" />
            <div class="mobile-text">
              <h1 class="mobile-title">DocTranslator Pro</h1>
              <p class="mobile-subtitle">AI文档智能翻译平台</p>
            </div>
          </div>
        </div>

        <div class="form-wrapper">
          <div class="auth-header">
            <h2 class="auth-title">{{ activeTab === 'login' ? '欢迎回来' : '创建账号' }}</h2>
            <p class="auth-subtitle">
              {{ activeTab === 'login' ? '登录您的账户' : '注册新账户开始使用' }}
            </p>
          </div>

          <el-tabs v-model="activeTab" stretch class="custom-tabs">
            <!-- 登录 Tab -->
            <el-tab-pane label="登录" name="login">
              <el-form
                ref="loginFormRef"
                :model="loginForm"
                :rules="loginRules"
                size="large"
                class="auth-form"
                @keyup.enter="doLogin"
              >
                <!-- prop="email" -->
                <el-form-item>
                  <el-input
                    v-model="loginForm.email"
                    placeholder="请输入邮箱地址"
                    prefix-icon="Message"
                  />
                </el-form-item>
                <!-- prop="password" -->
                <el-form-item>
                  <el-input
                    v-model="loginForm.password"
                    type="password"
                    show-password
                    placeholder="请输入密码"
                    prefix-icon="Lock"
                  />
                </el-form-item>

                <div class="form-actions">
                  <el-link :underline="false" class="forget-link" @click="goToForgot"
                    >忘记密码?</el-link
                  >
                </div>

                <el-button
                  type="primary"
                  class="submit-btn"
                  :loading="loginLoading"
                  @click="doLogin"
                  >登录</el-button
                >
              </el-form>
            </el-tab-pane>

            <!-- 注册 Tab -->
            <el-tab-pane label="注册" name="register">
              <el-form
                ref="registerFormRef"
                :model="registerForm"
                :rules="registerRules"
                size="large"
                class="auth-form"
                @keyup.enter="doRegister"
              >
                <el-form-item prop="email">
                  <el-input
                    v-model="registerForm.email"
                    placeholder="请输入邮箱地址"
                    prefix-icon="Message"
                  />
                </el-form-item>
                <el-form-item prop="code">
                  <el-input
                    v-model="registerForm.code"
                    placeholder="请输入验证码"
                    prefix-icon="Key"
                  >
                    <template #suffix>
                      <el-button
                        type="primary"
                        link
                        class="code-btn"
                        :disabled="codeDisabled"
                        :loading="codeSending"
                        @click="sendCode"
                      >
                        {{ codeText }}
                      </el-button>
                    </template>
                  </el-input>
                </el-form-item>
                <el-form-item prop="password">
                  <el-input
                    v-model="registerForm.password"
                    type="password"
                    show-password
                    placeholder="请设置密码"
                    prefix-icon="Lock"
                  />
                </el-form-item>
                <el-form-item prop="password2">
                  <el-input
                    v-model="registerForm.password2"
                    type="password"
                    show-password
                    placeholder="请确认密码"
                    prefix-icon="Lock"
                  />
                </el-form-item>

                <el-button
                  type="primary"
                  class="submit-btn"
                  :loading="registerLoading"
                  @click="doRegister"
                >
                  注册
                </el-button>
              </el-form>
            </el-tab-pane>
          </el-tabs>

          <!-- 底部说明 -->
          <div class="form-footer">
            <p class="footer-text">
              继续使用即表示同意
              <el-link type="primary" class="footer-link">服务条款</el-link>
              和
              <el-link type="primary" class="footer-link">隐私政策</el-link>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
// 引入需要的图标
import { Message, Lock, Key, Connection, Document, Link } from '@element-plus/icons-vue'
import { login, register, registerSendEmail } from '@/api/auth'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const router = useRouter()
const activeTab = ref('login')
const loginFormRef = ref(null)
const registerFormRef = ref(null)
const loginLoading = ref(false)
const registerLoading = ref(false)
const codeSending = ref(false)

// 登录数据
const loginForm = reactive({
  email: '',
  password: ''
})
const loginRules = reactive({
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
})

// 注册数据
const registerForm = reactive({
  email: '',
  code: '',
  password: '',
  password2: ''
})
const registerRules = reactive({
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  code: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
  password: [
    { required: true, message: '请设置密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  password2: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) callback(new Error('两次密码输入不一致'))
        else callback()
      },
      trigger: 'blur'
    }
  ]
})

// 验证码逻辑
const codeText = ref('获取验证码')
const codeDisabled = ref(false)

const sendCode = async () => {
  if (codeDisabled.value || codeSending.value) return
  if (!registerForm.email) {
    ElMessage.warning('请先输入邮箱地址')
    return
  }
  try {
    codeSending.value = true
    await registerSendEmail(registerForm.email)
    ElMessage.success('验证码已发送到您的邮箱')
    codeDisabled.value = true

    let count = 60
    codeText.value = `${count}s后重新发送`
    const timer = setInterval(() => {
      count--
      if (count <= 0) {
        clearInterval(timer)
        codeDisabled.value = false
        codeText.value = '获取验证码'
      } else {
        codeText.value = `${count}s后重新发送`
      }
    }, 1000)
  } catch (error) {
    ElMessage.error(error.message || '发送失败，请稍后重试')
  } finally {
    codeSending.value = false
  }
}

// 登录提交
const doLogin = () => {
  if (!loginFormRef.value) return
  loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loginLoading.value = true
      try {
        const res = await login(loginForm)
        if (res.code === 200) {
          userStore.updateToken(res.data.token)
          ElMessage.success('登录成功')
          router.push({ name: 'home' })
        } else {
          ElMessage.error(res.message || '登录失败')
        }
      } catch (err) {
        ElMessage.error(err.message || '登录失败，请稍后重试')
      } finally {
        loginLoading.value = false
      }
    } else {
      ElMessage.error('请正确填写表单')
    }
  })
}

// 注册提交
const doRegister = () => {
  if (!registerFormRef.value) return
  registerFormRef.value.validate(async (valid) => {
    if (valid) {
      registerLoading.value = true
      try {
        const res = await register(registerForm)
        if (res.code === 200) {
          ElMessage.success('注册成功，请登录')
          activeTab.value = 'login'
          // 将注册邮箱填入登录表单
          loginForm.email = registerForm.email
          // 清空注册表单
          Object.assign(registerForm, {
            email: '',
            code: '',
            password: '',
            password2: ''
          })
        } else {
          ElMessage.error(res.message || '注册失败')
        }
      } catch (err) {
        ElMessage.error(err.message || '注册失败，请稍后重试')
      } finally {
        registerLoading.value = false
      }
    } else {
      ElMessage.error('请正确填写表单')
    }
  })
}

const goToForgot = () => {
  router.push({ name: 'forget' })
}
</script>

<style scoped lang="scss">
/* 
  配色变量：
  主色调：#3b82f6 (品牌蓝)
  背景色：#f0f7ff (极淡蓝)
  侧边栏背景：#eff6ff (淡蓝)
  文字色：#1e293b (深灰蓝)
*/

.auth-page {
  width: 100vw;
  height: 100vh;
  overflow: hidden; /* 核心：禁止出现滚动条 */
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #f0f7ff 0%, #ffffff 100%); /* 极淡的蓝色背景 */
  position: relative;
}

/* 背景装饰，增加一点点现代感，但不抢眼 */
.bg-shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  z-index: 0;
  opacity: 0.6;
}
.shape-1 {
  width: 500px;
  height: 500px;
  background: #dbeafe; /* 淡蓝色 */
  top: -100px;
  left: -100px;
}
.shape-2 {
  width: 400px;
  height: 400px;
  background: #e0f2fe; /* 另一种淡蓝 */
  bottom: -100px;
  right: -100px;
}

/* 主容器 */
.auth-box {
  position: relative;
  z-index: 1;
  width: 1000px;
  height: 600px;
  border-radius: 20px;
  display: flex;
  overflow: hidden;
}

/* 左侧：品牌侧边栏 */
.auth-sidebar {
  width: 400px;
  padding: 60px 40px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: #334155;

  .brand-header {
    display: flex;
    align-items: center; /* 垂直居中 */
    gap: 15px; /* 图片和文字间距 */
    margin-bottom: 20px;

    .brand-logo {
      width: 48px;
      height: 48px;
      display: block;
    }

    .brand-name {
      font-size: 28px;
      font-weight: 700;
      color: #0f172a;
      letter-spacing: 0.5px;
      line-height: 1;
    }
  }

  .main-slogan {
    font-size: 24px;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 8px;
  }

  .sub-slogan {
    font-size: 14px;
    color: #64748b;
    margin-bottom: 40px;
  }

  .feature-list {
    display: flex;
    flex-direction: column;
    gap: 20px;

    .feature-item {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 14px;
      color: #475569;

      .el-icon {
        font-size: 18px;
        color: #3b82f6; /* 图标保持品牌蓝 */
        background: #dbeafe;
        padding: 6px;
        border-radius: 6px;
        box-sizing: content-box;
      }
    }
  }

  .sidebar-footer {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;

    .copyright-info {
      display: flex;
      flex-direction: column;
      gap: 2px;
      :hover {
        color: #1b6df2 !important;
      }
      .copyright {
        font-size: 14px;
        color: #94a3b8;
        margin: 0;
      }
    }

    .github-link {
      display: flex;
      align-items: center;
      gap: 4px;
      color: #64748b;
      text-decoration: none;
      transition: color 0.2s;
      font-size: 13px;

      &:hover {
        color: #3b82f6;
      }

      .el-icon {
        font-size: 14px;
      }
    }
  }
}

/* 移动端专用头部 */
.mobile-header {
  display: none; /* PC端隐藏 */
}

/* 右侧：表单区 */
.auth-form-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px;
}

.form-wrapper {
  width: 360px;

  .auth-header {
    margin-bottom: 30px;
    text-align: left;

    .auth-title {
      font-size: 26px;
      font-weight: 700;
      color: #0f172a;
      margin-bottom: 8px;
    }
    .auth-subtitle {
      font-size: 14px;
      color: #64748b;
    }
  }
}

/* 改造 Tabs 样式 */
.custom-tabs {
  :deep(.el-tabs__item) {
    font-size: 16px;
    color: #64748b;
    padding: 0 20px 10px 0; /* 左对齐Tab */
    height: auto;
  }

  :deep(.el-tabs__item.is-active) {
    color: #3b82f6;
    font-weight: 600;
  }

  :deep(.el-tabs__active-bar) {
    background-color: #3b82f6;
    height: 3px;
    border-radius: 2px;
  }

  :deep(.el-tabs__nav-wrap::after) {
    height: 1px;
    background-color: #f1f5f9;
  }
}

/* 输入框样式微调 */
.auth-form {
  margin-top: 20px;

  :deep(.el-input__wrapper) {
    box-shadow: none;
    background: #f8fafc; /* 极淡灰蓝背景 */
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    transition: all 0.2s;
    padding: 1px 11px;

    &:hover {
      border-color: #cbd5e1;
    }

    &.is-focus {
      background: #fff;
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); /* 柔和的蓝色光晕 */
    }
  }

  :deep(.el-input__inner) {
    height: 44px;
    color: #334155;
  }
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 24px;
  margin-top: -10px;

  .forget-link {
    color: #64748b;
    font-size: 13px;
    &:hover {
      color: #3b82f6;
    }
  }
}

.submit-btn {
  width: 100%;
  height: 46px;
  font-size: 16px;
  border-radius: 8px;
  background: #3b82f6;
  border: none;
  font-weight: 500;

  &:hover {
    background: #2563eb;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
  }
}

.code-btn {
  font-size: 14px;
  font-weight: 500;
  color: #3b82f6;
  padding: 0;
  margin-right: 8px;

  &:hover {
    color: #2563eb;
  }

  &.is-disabled {
    color: #9ca3af;
  }
}

.form-footer {
  text-align: center;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #f1f5f9;

  .footer-text {
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    color: #94a3b8;
    line-height: 1.5;
  }

  .footer-link {
    font-size: 12px;
    font-weight: 500;
    color: #3b82f6;
  }
}

/* 移动端适配 */
@media screen and (max-width: 768px) {
  .auth-box {
    width: 100%;
    height: 100%;
    border-radius: 0;
    flex-direction: column;
    box-shadow: none;
  }

  .auth-sidebar {
    display: none;
  }

  .mobile-header {
    display: block; /* 移动端显示 */
    width: 100%;
    text-align: center;
    margin-bottom: 20px;
    padding-bottom: 20px;
    border-bottom: 1px solid #f1f5f9;
  }

  .mobile-brand {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;

    .mobile-logo {
      width: 40px;
      height: 40px;
    }

    .mobile-text {
      text-align: left;

      .mobile-title {
        font-size: 22px;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
        line-height: 1.2;
      }

      .mobile-subtitle {
        font-size: 13px;
        color: #64748b;
        margin: 2px 0 0 0;
      }
    }
  }

  .auth-form-container {
    flex: none;
    padding: 20px 24px;
  }

  .form-wrapper {
    width: 100%;
    max-width: 400px;
  }

  .auth-header {
    text-align: center;
    margin-bottom: 24px;

    .auth-title {
      font-size: 22px;
    }

    .auth-subtitle {
      font-size: 13px;
    }
  }

  .custom-tabs {
    :deep(.el-tabs__item) {
      font-size: 15px;
      padding: 0 12px 8px;
    }
  }
}

/* 表单验证错误样式 */
:deep(.el-form-item.is-error .el-input__wrapper) {
  border-color: #ef4444;
}

:deep(.el-form-item__error) {
  font-size: 12px;
  line-height: 1.4;
  padding-top: 4px;
}

/* 加载状态样式 */
.submit-btn.is-loading {
  opacity: 0.8;
  cursor: not-allowed;
}
</style>
