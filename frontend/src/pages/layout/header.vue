<template>
  <div class="page-header">
    <div class="head-box">
      <div class="logo">
        <img src="@/assets/logo.png" class="logo_img" alt="DocTranslator" />
        <span>{{ settingsStore.siteTitle }}</span>
        <a class="btn_return" href="https://www.ehemart.com/" v-if="false"><<返回官网</a>
        <img
          class="icon_vip phone_show"
          style="height: 16px; margin-left: 10px"
          v-if="false"
          src="@/assets/vip.png"
          alt=""
        />
      </div>
      <!-- 导航菜单 -->
      <div class="btn-box">
        <template v-if="userStore.token">
          <div class="flex-center">
            <div class="btn_set" @click="funOpenHome">
              <div class="icon_svg"><svg-icon icon-class="home" /></div>
              <span class="pc_show">首页</span>
            </div>
            <div class="btn_set" @click="funOpenCorpus">
              <div class="icon_svg"><svg-icon icon-class="corpus" /></div>
              <span class="pc_show">语料库</span>
            </div>
            <div class="btn_set" @click="funOpenSet">
              <div class="icon_svg"><svg-icon icon-class="setting" /></div>
              <span class="pc_show">翻译设置</span>
            </div>
            <div
              class="btn_set"
              @click="windowOpen('https://github.com/mingchen666/DocTranslator')"
            >
              <div class="icon_svg"><svg-icon icon-class="github" /></div>
              <span class="pc_show">Github</span>
            </div>
            <div class="btn_set" @click="$router.push('/profile')">
              <!-- <div class="icon_svg"><svg-icon icon-class="user" /></div> -->
              <el-icon class="icon_svg"><UserFilled /></el-icon>
              <span class="pc_show">个人中心</span>
            </div>
            <img
              class="icon_vip pc_show"
              v-if="store.level == 'vip'"
              src="@/assets/vip.png"
              alt=""
            />
            <el-dropdown placement="bottom-end" @command="user_action">
              <template #default>
                <div>
                  <el-button class="pc_show">
                    <div class="username">{{ userStore.userInfo.email }}</div>
                    <el-icon class="el-icon--right"><arrow-down /></el-icon>
                  </el-button>
                  <div class="phone_show icon_more">
                    <el-icon><MoreFilled /></el-icon>
                  </div>
                </div>
              </template>

              <template #dropdown>
                <el-dropdown-menu>
                  <!-- <el-dropdown-item command="profile">个人中心</el-dropdown-item> -->
                  <el-dropdown-item command="pwd">修改密码</el-dropdown-item>
                  <el-dropdown-item command="exit">退出</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
        <template v-else>
          <el-button class="pc_show" @click="$router.push('/login')">登录/注册</el-button>
          <el-icon class="phone_show icon_user" @click="$router.push('/login')"><User /></el-icon>
        </template>
      </div>
    </div>

    <!-- 退出弹窗 -->
    <el-dialog
      v-model="logoutVisible"
      modal-class="custom_dialog"
      center
      :show-close="false"
      width="90%"
      heigt="240px"
      style="border-radius: 20px"
    >
      <div class="dialog-container">
        <div class="dialog-title">退出登录</div>
        <div class="dialog-content">您确定要退出登录吗？</div>
        <div class="dialog-btns">
          <el-button class="dialog-btn cancel" @click="logoutVisible = false">取消</el-button>
          <el-button
            class="dialog-btn confirm"
            type="primary"
            color="#055CF9"
            @click="confirmLogout"
            >确认</el-button
          >
        </div>
      </div>
    </el-dialog>

    <!-- 翻译设置组件 -->
    <translation-settings ref="translationSettings" />
  </div>
</template>
<script setup>
import { useRouter } from 'vue-router'
import { store } from '@/store/index'
import { useUserStore } from '@/store/user'
import { useSettingsStore } from '@/store/settings'
import { useTranslateStore } from '@/store/translate'
import { authInfo } from '@/api/account'
import { ref, computed, onMounted } from 'vue'
import SvgIcon from '@/components/SvgIcon/index.vue'
import { UserFilled } from '@element-plus/icons-vue'
import TranslationSettings from '@/components/TranslationSettings.vue'
import { getSystemSetting, getTranslateSetting } from '@/api/settings'
const userStore = useUserStore()
const translationSettings = ref(null)
const settingsStore = useSettingsStore()
const translateStore = useTranslateStore()
const router = useRouter()

const logoutVisible = ref(false)
const langMultipleLimit = ref(5)

const types = [
  {
    value: 'trans_text',
    label: '仅文字部分',
    children: [
      {
        value: 'trans_text_only',
        label: '仅译文',
        children: [
          {
            value: 'trans_text_only_new',
            label: '重排版面'
          },
          {
            value: 'trans_text_only_inherit',
            label: '继承原版面'
          }
        ]
      },
      {
        value: 'trans_text_both',
        label: '原文+译文',
        children: [
          {
            value: 'trans_text_both_new',
            label: '重排版面'
          },
          {
            value: 'trans_text_both_inherit',
            label: '继承原版面'
          }
        ]
      }
    ]
  },
  {
    value: 'trans_all',
    label: '全部内容',
    children: [
      {
        value: 'trans_all_only',
        label: '仅译文',
        children: [
          {
            value: 'trans_all_only_new',
            label: '重排版面'
          },
          {
            value: 'trans_all_only_inherit',
            label: '继承原版面'
          }
        ]
      },
      {
        value: 'trans_all_both',
        label: '原文+译文',
        children: [
          {
            value: 'trans_all_both_new',
            label: '重排版面'
          },
          {
            value: 'trans_all_both_inherit',
            label: '继承原版面'
          }
        ]
      }
    ]
  }
]

// 获取用户信息
const getUserInfo = async () => {
  try {
    const res = await authInfo()
    if (res.code === 200) {
      userStore.updateUserInfo(res.data)
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

const form = ref({
  server: store.level == 'vip' ? 'member' : 'openai',
  api_url: 'https://api.openai.com',
  api_key: '',
  model: '',
  backup_model: '',
  langs: [],
  lang: '',
  type: [],
  uuid: '',
  prompt:
    '你是一个文档翻译助手，请将以下文本、单词或短语直接翻译成{target_lang}，不返回原文本。如果文本中包含{target_lang}文本、特殊名词（比如邮箱、品牌名、单位名词如mm、px、℃等）、无法翻译等特殊情况，请直接返回原文而无需解释原因。遇到无法翻译的文本直接返回原内容。保留多余空格。',
  threads: 10,
  scanned: false, // 添加 scanned 字段
  origin_lang: '', // 添加起始语言字段
  comparison_id: '', //术语id
  prompt_id: '', //提示语id
  prompt_title: '',
  doc2x_flag: 'N',
  doc2x_secret_key: ''
})

const rules = {
  files: [{ required: true, message: '请上传文件', trigger: ['blur', 'change'] }],
  api_url: [
    {
      required: true,
      message: '请输入接口地址',
      trigger: ['blur', 'change']
    }
  ],
  api_key: [
    {
      required: true,
      message: '请输入API Key',
      trigger: ['blur', 'change']
    }
  ],
  server: [{ required: true, message: '请选择供应商', trigger: ['blur', 'change'] }],
  type: [{ required: true, message: '请选择译文形式', trigger: ['blur', 'change'] }],
  model: [{ required: true, message: '请选择模型', trigger: ['blur', 'change'] }],
  langs: [{ required: true, message: '请选择翻译目标语言', trigger: ['blur', 'change'] }],
  prompt: [{ required: true, message: '请填写系统提示语', trigger: ['blur', 'change'] }],
  prompt_id: [{ required: true, message: '请选择提示语', trigger: ['blur', 'change'] }],
  threads: [{ required: true, message: '请填写线程数', trigger: ['blur', 'change'] }],
  doc2x_secret_key: [
    { required: true, message: '请输入Doc2x的API KEY', trigger: ['blur', 'change'] }
  ]
}

//用户操作
function user_action(command) {
  if (command == 'pwd') {
    router.push('/reset')
  }
  if (command == 'exit') {
    logoutVisible.value = !logoutVisible.value
  }
  if (command == 'profile') {
    router.push('/profile')
  }
}

//打开翻译设置弹窗
function funOpenSet() {
  translationSettings.value.open()
  // formSetShow.value = true
}

//打开语料库
function funOpenCorpus() {
  router.push('/corpus')
}

//回到首页
function funOpenHome() {
  router.push('/')
}

//演示版入口
function windowOpen(url) {
  window.open(url)
}

// 退出登录
function confirmLogout() {
  userStore.logout()
  logoutVisible.value = false
}
// 获取系统相关设置
const getSystemSettingsInfo = async () => {
  const res = await getSystemSetting()
  if (res.code === 200) {
    console.log('系统信息', res.data)
    // settingsStore.updateSystemSetting(res.data)
  }
}
// 获取默认翻译设置
const getTranslateSettingInfo = async () => {
  const res = await getTranslateSetting()
  if (res.code === 200) {
    // 更新系统设置store
    settingsStore.updateSystemSettings(res.data)
    // translateStore.updateAISettingsField('api_url',res.data.api_url)
  }
}
onMounted(() => {
  getUserInfo()
  getTranslateSettingInfo()
  // getSystemSettingsInfo()
})
</script>
<style scoped lang="scss">
.page-header {
  width: 100%;
  height: 60px;
  background: #ffffff;
  box-shadow: 0px 0px 12px 0px rgba(0, 22, 52, 0.05);
}
.head-box {
  max-width: 1240px;
  padding: 0 20px;
  margin: 0 auto;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.logo {
  display: flex;
  align-items: center;
  img {
    height: 44px;
  }
  span {
    font-size: 20px;
    font-weight: bold;
    margin-left: 20px;
  }
  .btn_return {
    color: #045cf9;
    margin-left: 10px;
    font-size: 14px;
    text-decoration: none;
    cursor: pointer;
  }
}
::v-deep {
  .btn_set {
    display: flex;
    align-items: center;
    margin-right: 20px;
    font-size: 14px;
    color: #000000;
    cursor: pointer;
    img {
      margin-right: 8px;
    }
    .icon_svg {
      margin-right: 8px;
      font-size: 16px;
      color: #666;
    }
    &:hover {
      color: #045cf9;
      .icon_svg {
        color: #045cf9;
      }
    }
  }
  .icon_vip {
    margin-right: 12px;
  }
  .username {
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 30px;
  }
  .el-dropdown {
    .el-tooltip__trigger {
      outline: none;
    }
    .el-button {
      outline: none;
    }
  }

  .custom_dialog {
    .el-dialog__header {
      padding-bottom: 0;
      font-size: 16px;
      color: #111;
    }
    .el-dialog {
      max-width: 410px;
      padding: 20px;
    }
  }
  .custom_2_dialog {
    .el-dialog {
      max-width: 410px;
    }
  }
  .change_dialog {
    .el-dialog {
      padding: 20px 40px;
    }
    .el-dialog__header {
      margin-top: 10px;
      margin-bottom: 20px;
    }
  }

  .dialog-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }
  .dialog-title {
    font-weight: bold;
    font-size: 20px;
    color: #111111;
    line-height: 24px;
    margin-top: 30px;
    margin-bottom: 20px;
  }
  .dialog-content {
    font-family: 'PingFang SC';
    font-weight: 400;
    font-size: 16px;
    color: #999999;
    line-height: 24px;
    margin-bottom: 40px;
  }
  .dialog-btns {
    margin-bottom: 30px;
  }
  .dialog-btn {
    width: 120px;
  }
  .dialog-btn.cancel {
    margin-right: 4px;
  }
  .dialog-btn.send-confirm {
    width: 327px;
  }
  .login_dialog1 {
    .el-dialog {
      padding: 20px 40px;
    }
    .el-menu {
      border: none;
      height: 65px;
    }
    .el-menu-item {
      padding: 0;
      height: 40px;
      font-size: 20px;
      font-family: PingFang SC;
      margin: 0 15px;
      background: #fff !important;
    }
  }
  .forget-title {
    display: flex;
    justify-content: space-between;
    margin-top: 10px;
    margin-bottom: 30px;
    .el-text {
      font-size: 22px;
      color: #111111;
    }
    .el-icon {
      font-size: 24px;
    }
  }

  .setting_dialog {
    .el-dialog {
      max-width: 800px;
      padding: 30px 70px;
    }
    .el-dialog__title {
      color: #111111;
    }
    .el-dialog__headerbtn {
      font-size: 20px;
      right: 10px;
      top: 10px;
      i {
        color: #111;
      }
    }
    .el-dialog__body {
      padding: 0 30px 0 30px;
    }
    .el-form-item {
      .el-form-item__label {
        justify-content: flex-start;
        color: #111111;
      }
      .el-input-number .el-input__inner {
        text-align: left;
      }
    }
    .btn_box {
      position: relative;
      text-align: center;
      .btn_check {
        position: absolute;
        left: 0;
        .el-tag {
          height: 28px;
          margin-left: 10px;
        }
      }
      .custom_btn {
        background: #fff;
        color: #055cf9;
        height: 28px;
        padding: 0 10px;
        &:hover {
          color: #055cf9;
          background: var(--el-color-primary-light-9);
        }
      }
    }
  }
  .no_label {
    label {
      opacity: 0;
    }
    .flex_box {
      width: 100%;
      .el-input {
        flex: 1;
        margin-right: 10px;
      }
    }
  }
}
</style>
<style type="text/css" lang="scss">
.flex_box {
  display: flex;
  align-items: center;
}
.flex-between {
  justify-content: space-between;
}
.flex-center {
  display: flex;
  align-items: center;
  justify-content: space-around;
}
.menu-center {
  justify-content: center;
}
.menu-title {
  font-family: 'PingFang SC';
  font-weight: bold;
  font-size: 22px;
  color: #8f8f91;
  line-height: 24px;
}
.menu-title.active {
  color: #111111;
}
.phone_show {
  display: none !important;
}

.language-selection {
  display: flex;
  align-items: center;
  gap: 10px; /* 调整元素之间的间距 */
  width: 100%;
}
.lang-select {
  width: 100%; /* 默认宽度为100% */
  transition: width 0.3s ease; /* 添加过渡效果 */
}
.language-selection:has(.conversion-symbol) .lang-select {
  width: 100%; /* 当有转换符号时，设置宽度为45% */
}
.conversion-symbol {
  font-size: 20px;
  color: #409eff; /* 使用 Element Plus 的主色调，可以根据需要调整 */
  flex-shrink: 0; /* 防止符号被压缩 */
}
@media screen and (max-width: 767px) {
  .pc_show {
    display: none !important;
  }
  .phone_show {
    display: inline-block !important;
  }
  .icon_user {
    font-size: 30px !important;
  }
  .logo span {
    font-size: 14px !important;
    margin-left: 10px !important;
  }
  .icon_more {
    font-size: 20px;
  }
  .btn_set {
    margin-right: 6px !important;
  }
  .logo_img {
    height: 30px !important;
  }

  .setting_dialog {
    .el-dialog {
      padding: 20px !important;
    }
    .el-dialog__body {
      padding: 0 !important;
      max-height: 300px;
      overflow-y: auto;
      .el-form-item {
        display: block !important;
        margin-bottom: 10px;
      }
    }
    .btn_box {
      text-align: right !important;
    }
  }

  .no_label {
    label {
      display: none;
    }
  }
}
</style>
