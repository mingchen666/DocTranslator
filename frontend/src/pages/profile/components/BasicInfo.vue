<template>
  <div class="basic-info-container">
    <div class="section-header">

      <div>
        <h3>账户概览</h3>
        <p class="subtitle">查看您的账户状态和资源使用情况</p>
      </div>
    </div>

    <div class="info-grid">
      <div class="info-card storage-card">
        <div class="info-card-header">
          <div class="info-card-icon storage-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
          </div>
          <span class="info-card-label">云端存储空间</span>
        </div>
        <div class="storage-body">
          <div class="storage-stats">
            <span class="storage-used">{{ formattedStorage }}</span>
            <span class="storage-sep">/</span>
            <span class="storage-total">{{ formattedAllStorage }}</span>
          </div>
          <div class="progress-wrapper">
            <el-progress
              :percentage="storagePercentage"
              :stroke-width="8"
              :color="progressColor"
              :show-text="false"
              class="custom-progress"
            />
          </div>
          <div class="storage-footer">
            <span class="usage-text">已使用 {{ storagePercentage }}%</span>
            <el-button v-if="userInfo.level !== 'vip'" type="primary" link size="small" @click="upgradeStorage">
              升级空间 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <div class="info-card account-card">
        <div class="info-card-header">
          <div class="info-card-icon account-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          </div>
          <span class="info-card-label">账户状态</span>
        </div>
        <div class="account-body">
          <div class="account-row">
            <span class="account-label">会员等级</span>
            <span class="account-value">
              <el-tag :type="userInfo.level === 'vip' ? 'warning' : 'info'" size="small" round effect="light">
                {{ userInfo.level === 'vip' ? '尊享会员' : '普通用户' }}
              </el-tag>
            </span>
          </div>
          <div class="account-row">
            <span class="account-label">注册时间</span>
            <span class="account-value">{{ formatTime(userInfo.created_at) || '-' }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, toRefs } from 'vue'
import { useRouter } from 'vue-router'
import { formatTime } from '@/utils/tools'
import { ArrowRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const props = defineProps({
  userInfo: { type: Object, required: true }
})
const { userInfo } = toRefs(props)

const storagePercentage = computed(() => {
  if (!userInfo.value.total_storage) return 0
  const p = (userInfo.value.storage / userInfo.value.total_storage) * 100
  return Math.min(100, parseFloat(p.toFixed(2)))
})

const formattedStorage = computed(() => (userInfo.value.storage / (1024 * 1024)).toFixed(2) + ' MB')
const formattedAllStorage = computed(
  () => (userInfo.value.total_storage / (1024 * 1024)).toFixed(2) + ' MB'
)

const progressColor = computed(() => {
  if (storagePercentage.value < 60) return '#3b82f6'
  if (storagePercentage.value < 80) return '#e6a23c'
  return '#f56c6c'
})

const upgradeStorage = () => ElMessage.info('请联系管理员扩容')
</script>

<style scoped lang="scss">
.basic-info-container {
  padding: 4px 0;
}

.section-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 24px;

  h3 {
    font-size: 18px;
    font-weight: 600;
    color: #1e293b;
    margin: 0 0 2px;
  }

  .subtitle {
    font-size: 13px;
    color: #94a3b8;
    margin: 0;
  }
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.info-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 18px;
  transition: all 0.2s ease;

  &:hover {
    border-color: #cbd5e1;
  }

  .info-card-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
  }

  .info-card-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;

    &.storage-icon {
      background: #eff6ff;
      color: #3b82f6;
    }

    &.account-icon {
      background: #f0fdf4;
      color: #22c55e;
    }
  }

  .info-card-label {
    font-size: 14px;
    font-weight: 600;
    color: #334155;
  }
}

.storage-body {
  .storage-stats {
    display: flex;
    align-items: baseline;
    gap: 4px;
    margin-bottom: 10px;

    .storage-used {
      font-size: 22px;
      font-weight: 700;
      color: #1e293b;
    }

    .storage-sep {
      color: #94a3b8;
      font-size: 14px;
    }

    .storage-total {
      font-size: 14px;
      color: #94a3b8;
    }
  }

  .progress-wrapper {
    margin-bottom: 10px;

    :deep(.el-progress-bar__outer) {
      background-color: #e2e8f0;
      border-radius: 4px;
    }

    :deep(.el-progress-bar__inner) {
      border-radius: 4px;
    }
  }

  .storage-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;

    .usage-text {
      color: #64748b;
    }
  }
}

.account-body {
  .account-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid #f1f5f9;

    &:last-child {
      border-bottom: none;
      padding-bottom: 0;
    }

    &:first-child {
      padding-top: 0;
    }

    .account-label {
      font-size: 13px;
      color: #64748b;
    }

    .account-value {
      font-size: 13px;
      color: #334155;
      font-weight: 500;
    }
  }
}

@media (max-width: 576px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
