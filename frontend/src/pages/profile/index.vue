<template>
  <div class="personal-center-container">
    <div class="scrollable-content-area">
      <div class="main-content-wrapper">
        <el-menu class="side-nav" :default-active="activeTab" @select="handleTabChange">
          <div class="nav-header">
            <el-avatar :size="36" :src="userInfo.avatar || defaultAvatar" />
            <div class="nav-user-info">
              <span class="nav-username">{{ userInfo.name || userInfo.email || '用户' }}</span>
              <span class="nav-role" :class="userInfo.level">{{ userInfo.level === 'vip' ? '尊享会员' : '普通用户' }}</span>
            </div>
          </div>
          <el-divider style="margin: 8px 0 12px;" />
          <el-menu-item index="basic">
            <el-icon><User /></el-icon>
            <span>基本信息</span>
          </el-menu-item>
          <el-menu-item index="security">
            <el-icon><Lock /></el-icon>
            <span>账号安全</span>
          </el-menu-item>
          <el-menu-item index="translation">
            <el-icon><Setting /></el-icon>
            <span>翻译设置</span>
          </el-menu-item>
          <el-menu-item index="mcp">
            <el-icon><Connection /></el-icon>
            <span>MCP 配置</span>
          </el-menu-item>
        </el-menu>

        <div class="content-card-wrapper">
          <div class="mobile-tabs-container">
            <el-tabs v-model="activeTab" class="mobile-tabs">
              <el-tab-pane name="basic">
                <template #label>
                  <div class="tab-label">
                    <el-icon><User /></el-icon>
                    <span>基本信息</span>
                  </div>
                </template>
              </el-tab-pane>
              <el-tab-pane name="security">
                <template #label>
                  <div class="tab-label">
                    <el-icon><Lock /></el-icon>
                    <span>账号安全</span>
                  </div>
                </template>
              </el-tab-pane>
              <el-tab-pane name="translation">
                <template #label>
                  <div class="tab-label">
                    <el-icon><Setting /></el-icon>
                    <span>翻译设置</span>
                  </div>
                </template>
              </el-tab-pane>
              <el-tab-pane name="mcp">
                <template #label>
                  <div class="tab-label">
                    <el-icon><Connection /></el-icon>
                    <span>MCP 配置</span>
                  </div>
                </template>
              </el-tab-pane>
            </el-tabs>
          </div>

          <user-card :userInfo="userInfo" />

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
            <mcp-config
              v-show="activeTab === 'mcp'"
            />
          </el-card>
        </div>
      </div>
    </div>
    <Filing />
  </div>
</template>

<script setup>
import Filing from '@/components/Filing.vue'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, Setting, Connection } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import defaultAvatar from '@/assets/avator.png'

import BasicInfo from './components/BasicInfo.vue'
import SecuritySettings from './components/SecuritySettings.vue'
import TranslationSettings from './components/TranslationSettings.vue'
import McpConfig from './mcp.vue'
import UserCard from './components/UserCard.vue'

const userStore = useUserStore()
const router = useRouter()
const activeTab = ref('basic')

const userInfo = ref({
  email: '',
  level: '',
  storage: 0,
  created_at: ''
})

const translationSettings = ref({
  server: 'openai',
  api_url: 'https://api.openai.com',
  api_key: '',
  model: 'gpt-3.5-turbo',
  backup_model: '',
  langs: ['中文', '英语'],
  type: ['trans_text', 'trans_text_only', 'trans_text_only_new'],
  prompt: '',
  threads: 10,
  comparison_id: '',
  prompt_id: '',
  doc2x_flag: 'N',
  doc2x_secret_key: '',
  scanned: false,
  origin_lang: ''
})

onMounted(() => {
  userInfo.value = userStore.userInfo
})

const handleTabChange = (key) => {
  activeTab.value = key
}

const handleUpdateInfo = (newInfo) => {
  userInfo.value = { ...userInfo.value, ...newInfo }
}

const handleChangePassword = () => {
  router.push('/password')
}

const handleSaveTranslationSettings = (settings) => {
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
  background: #f0f4f8;
}

.scrollable-content-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background-color: rgba(100, 116, 139, 0.25);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-track {
    background-color: transparent;
  }
}

.main-content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  gap: 20px;
  min-height: min-content;
}

.side-nav {
  width: 220px;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  align-self: flex-start;
  border-radius: 16px;
  border: none;
  padding: 16px 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);

  .nav-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 4px 8px;

    .el-avatar {
      border: 2px solid #e2e8f0;
      flex-shrink: 0;
    }

    .nav-user-info {
      min-width: 0;

      .nav-username {
        display: block;
        font-size: 14px;
        font-weight: 600;
        color: #1e293b;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .nav-role {
        display: inline-block;
        font-size: 11px;
        padding: 1px 6px;
        border-radius: 4px;
        margin-top: 2px;

        &.vip {
          background: linear-gradient(135deg, #fce38a 0%, #f38181 100%);
          color: white;
          font-weight: 600;
        }

        &.free, &.normal {
          background: #f1f5f9;
          color: #64748b;
        }
      }
    }
  }

  .el-menu-item {
    height: 44px;
    line-height: 44px;
    margin: 2px 0;
    border-radius: 10px;
    font-size: 14px;
    color: #64748b;
    transition: all 0.2s ease;

    .el-icon {
      font-size: 18px;
      margin-right: 10px;
    }

    &:hover {
      background-color: #f8fafc;
      color: #334155;
    }

    &.is-active {
      background-color: #eff6ff;
      color: #3b82f6;
      font-weight: 500;

      .el-icon {
        color: #3b82f6;
      }
    }
  }
}

.content-card-wrapper {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;

  .mobile-tabs-container {
    display: none;
  }

  .mobile-tabs {
    width: 100%;
    background: white;
    border-radius: 12px;
    padding: 0 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);

    :deep(.el-tabs__nav) {
      width: 100%;
      display: flex;
      justify-content: space-around;
    }

    :deep(.el-tabs__item) {
      flex: 1;
      text-align: center;
      padding: 0 8px;
      height: 46px;
      line-height: 46px;
      font-size: 13px;
      color: #64748b;
      transition: all 0.2s ease;

      &.is-active {
        color: #3b82f6;
        font-weight: 600;
      }

      &:hover {
        color: #3b82f6;
      }
    }

    :deep(.el-tabs__active-bar) {
      background-color: #3b82f6;
      height: 3px;
      border-radius: 3px 3px 0 0;
    }

    :deep(.el-tabs__nav-wrap::after) {
      display: none;
    }
  }

  .tab-label {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;

    .el-icon {
      font-size: 15px;
    }

    span {
      font-size: 13px;
    }
  }

  .content-card {
    border-radius: 16px;
    min-height: 400px;
    border: none;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  }
}

@media screen and (max-width: 992px) {
  .main-content-wrapper {
    flex-direction: column;

    .side-nav {
      display: none;
    }
  }

  .content-card-wrapper {
    .mobile-tabs-container {
      display: block;
    }
  }
}

@media screen and (max-width: 576px) {
  .scrollable-content-area {
    padding: 12px;
  }

  .content-card-wrapper {
    gap: 12px;

    .mobile-tabs {
      border-radius: 10px;
      padding: 0 4px;

      :deep(.el-tabs__item) {
        padding: 0 4px;
        font-size: 12px;
        height: 40px;
        line-height: 40px;

        .tab-label {
          gap: 3px;

          .el-icon {
            font-size: 14px;
          }

          span {
            font-size: 12px;
          }
        }
      }
    }

    .content-card {
      border-radius: 12px;
      min-height: 300px;
    }
  }
}
</style>
