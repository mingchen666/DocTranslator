<template>
  <div class="personal-center-container">
    <!-- 主内容区 - 整个页面可滚动 -->
    <div class="scrollable-content-area">
      <div class="main-content-wrapper">
        <!-- PC端左侧导航 -->
        <el-menu class="side-nav" :default-active="activeTab" @select="handleTabChange">
          <el-menu-item index="basic">
            <template #title>
              <el-icon><User /></el-icon>
              <span>基本信息</span>
            </template>
          </el-menu-item>
          <el-menu-item index="security">
            <template #title>
              <el-icon><Lock /></el-icon>
              <span>账号安全</span>
            </template>
          </el-menu-item>
          <el-menu-item index="translation">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>翻译设置</span>
            </template>
          </el-menu-item>
        </el-menu>

        <!-- 右侧内容区 -->
        <div class="content-card-wrapper">
          <!-- 移动端顶部导航 -->
          <el-tabs v-model="activeTab" class="mobile-tabs">
            <el-tab-pane name="basic">
              <template #label>
                <span
                  ><el-icon><User /></el-icon> 基本信息</span
                >
              </template>
            </el-tab-pane>
            <el-tab-pane name="security">
              <template #label>
                <span
                  ><el-icon><Lock /></el-icon> 账号安全</span
                >
              </template>
            </el-tab-pane>
            <el-tab-pane name="translation">
              <template #label>
                <span
                  ><el-icon><Setting /></el-icon> 翻译设置</span
                >
              </template>
            </el-tab-pane>
          </el-tabs>

          <!-- 用户概览-->
          <el-card v-if="false" class="user-profile-card" shadow="hover">
            <div class="profile-header">
              <el-avatar :size="72" :src="userInfo.avatar || defaultAvatar" />
              <div class="profile-info">
                <div class="username">
                  {{ userInfo.username }}
                  <el-tag
                    v-if="userInfo.level === 'vip'"
                    class="vip-tag"
                    effect="dark"
                    type="warning"
                  >
                    <img src="@/assets/vip.png" class="vip-icon" /> VIP会员
                  </el-tag>
                </div>
                <div class="user-meta">
                  <span class="email">
                    <el-icon><Message /></el-icon>
                    {{ userInfo.email }}
                  </span>
                  <span class="register-date">
                    <el-icon><Calendar /></el-icon>
                    注册于: {{ formatTime(userInfo.created_at) || '-' }}
                  </span>
                </div>
              </div>
            </div>
          </el-card>
          <user-card :userInfo="userInfo"></user-card>
          <!-- 内容卡片 -->
          <el-card class="content-card" shadow="never">
            <basic-info
              v-show="activeTab === 'basic'"
              :userInfo="userInfo"
              @update-info="handleUpdateInfo"
            />
            <security-settings
              v-show="activeTab === 'security'"
              :email="userInfo.email"
              @change-password="handleChangePassword"
            />
            <translation-settings
              v-show="activeTab === 'translation'"
              :settings="translationSettings"
              @save-settings="handleSaveTranslationSettings"
            />
          </el-card>
        </div>
      </div>
    </div>
    <!-- 备案信息 -->
    <Filing />
  </div>
</template>

<script setup>
import Filing from '@/components/Filing.vue'
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { formatTime } from '@/utils/tools'
import { User, Lock, Setting, Message, Calendar } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'

import BasicInfo from './components/BasicInfo.vue'
import SecuritySettings from './components/SecuritySettings.vue'
import TranslationSettings from './components/TranslationSettings.vue'
import UserCard from './components/UserCard.vue'
const userStore = useUserStore()
const router = useRouter()
const activeTab = ref('basic')

// 用户数据
const userInfo = ref({
  email: '',
  level: '',
  storage: 0,
  created_at: ''
})

// 翻译设置（完整配置）
const translationSettings = ref({
  server: 'openai',
  api_url: 'https://api.openai.com',
  api_key: '',
  model: 'gpt-3.5-turbo',
  backup_model: '',
  langs: ['中文', '英语'],
  type: ['trans_text', 'trans_text_only', 'trans_text_only_new'],
  prompt:
    '你是一个文档翻译助手，请将以下文本、单词或短语直接翻译成{target_lang}，不返回原文本。如果文本中包含{target_lang}文本、特殊名词（比如邮箱、品牌名、单位名词如mm、px、℃等）、无法翻译等特殊情况，请直接返回原文而无需解释原因。遇到无法翻译的文本直接返回原内容。保留多余空格。',
  threads: 10,
  comparison_id: '',
  prompt_id: '',
  doc2x_flag: 'N',
  doc2x_secret_key: '',
  scanned: false,
  origin_lang: ''
})

// 默认头像
const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'
// 初始化从store获取用户信息
onMounted(() => {
  userInfo.value = userStore.userInfo
  // const registerTime=formatDate(userInfo.value.create_at)
})

// 切换标签页
const handleTabChange = (key) => {
  activeTab.value = key
}

// 处理更新基本信息
const handleUpdateInfo = (newInfo) => {
  console.log('模拟更新用户信息:', newInfo)
  userInfo.value = {
    ...userInfo.value,
    ...newInfo
  }
}

// 处理修改密码
const handleChangePassword = () => {
  router.push('/reset')
}

// 处理保存翻译设置
const handleSaveTranslationSettings = (settings) => {
  console.log('保存翻译设置:', settings)
  localStorage.setItem('api_url', settings.api_url)
  localStorage.setItem('api_key', settings.api_key)
  localStorage.setItem('model', settings.model)
  localStorage.setItem('backup_model', settings.backup_model)
  localStorage.setItem('langs', JSON.stringify(settings.langs))
  localStorage.setItem('type', JSON.stringify(settings.type))
  localStorage.setItem('prompt', settings.prompt)
  localStorage.setItem('threads', settings.threads)
  localStorage.setItem('comparison_id', settings.comparison_id)
  localStorage.setItem('prompt_id', settings.prompt_id)
  localStorage.setItem('doc2x_flag', settings.doc2x_flag)
  localStorage.setItem('doc2x_secret_key', settings.doc2x_secret_key)

  translationSettings.value = settings
}
</script>

<style scoped lang="scss">
.personal-center-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f3f8ff;
}

/* 可滚动内容区域 */
.scrollable-content-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px;

  /* 滚动条样式 */
  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background-color: var(--el-color-primary-light-5);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-track {
    background-color: var(--el-fill-color-light);
  }
}

/* 主内容容器 */
.main-content-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  gap: 20px;
  min-height: min-content;
}

/* 左侧导航 */
.side-nav {
  width: 220px;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  align-self: flex-start;
  border-radius: 12px;
  border: none;

  .el-menu-item {
    height: 48px;
    line-height: 48px;
    margin: 4px 0;
    border-radius: 8px;
    font-size: 15px;

    &.is-active {
      background-color: var(--el-color-primary-light-9);
      color: var(--el-color-primary);
      font-weight: 500;
    }

    .el-icon {
      font-size: 18px;
      margin-right: 8px;
    }
  }
}

/* 右侧内容区 */
.content-card-wrapper {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;

  .mobile-tabs {
    display: none;
  }

  .user-profile-card {
    border-radius: 12px;
    width: 100%;

    .profile-header {
      display: flex;
      align-items: center;
      padding: 16px;

      .el-avatar {
        margin-right: 20px;
        border: 2px solid var(--el-color-primary);
      }

      .profile-info {
        flex: 1;

        .username {
          font-size: 22px;
          font-weight: 600;
          margin-bottom: 8px;
          display: flex;
          align-items: center;
          gap: 10px;

          .vip-tag {
            display: inline-flex;
            align-items: center;

            .vip-icon {
              width: 16px;
              height: 16px;
              margin-right: 4px;
            }
          }
        }

        .user-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 16px;
          color: var(--el-text-color-secondary);
          font-size: 14px;

          .el-icon {
            margin-right: 4px;
            vertical-align: middle;
          }
        }
      }
    }
  }

  .content-card {
    border-radius: 12px;
    min-height: 400px;
    border: none;
  }
}

/* 响应式设计 */
@media screen and (max-width: 992px) {
  .main-content-wrapper {
    flex-direction: column;

    .side-nav {
      display: none;
    }
  }

  .content-card-wrapper {
    .mobile-tabs {
      display: block;
      margin-bottom: 16px;
    }
  }
}

@media screen and (max-width: 576px) {
  .scrollable-content-area {
    padding: 8px;
  }

  .user-profile-card {
    .profile-header {
      flex-direction: column;
      text-align: center;

      .el-avatar {
        margin-right: 0;
        margin-bottom: 16px;
      }

      .profile-info {
        text-align: center;

        .username {
          justify-content: center;
        }

        .user-meta {
          justify-content: center;
        }
      }
    }
  }
}
</style>
