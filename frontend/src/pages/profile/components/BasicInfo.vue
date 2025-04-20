<template>
  <div class="basic-info">
    <!-- 邮箱展示 -->
    <div class="info-row">
      <span class="info-label">邮箱账号：</span>
      <span class="info-content">{{ userInfo.email || '-' }}</span>
    </div>

    <!-- 会员状态 -->
    <div class="info-row">
      <span class="info-label">账户类型：</span>
      <span class="info-content">
        <span class="user-level" :class="{ vip: userInfo.level === 'vip' }">
          {{ userInfo.level === 'vip' ? 'VIP会员' : '普通用户' }}
          <img v-if="userInfo.level === 'vip'" src="@/assets/vip.png" class="vip-icon" />
        </span>
      </span>
    </div>

    <!-- 注册时间 -->
    <div class="info-row">
      <span class="info-label">注册时间：</span>
      <span class="info-content">{{ formatTime(userInfo.created_at) || '-' }}</span>
    </div>

    <!-- 存储空间 -->
    <div class="info-row">
      <span class="info-label">存储空间：</span>
      <div class="storage-display">
        <div class="storage-bar">
          <div
            class="storage-used"
            :style="{ width: storagePercentage + '%' }"
            :class="{ warning: storagePercentage > 80 }"
          ></div>
        </div>
        <div class="storage-details">
          <span class="storage-text"> {{ formattedStorage }} / 100 MB </span>
          <span class="storage-percent">{{ storagePercentage }}%</span>
          <el-button
            v-if="userInfo.level !== 'vip'"
            type="text"
            size="small"
            class="upgrade-btn"
            @click="upgradeStorage"
          >
            扩容空间
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, toRefs } from 'vue'
import { useRouter } from 'vue-router'
import { formatTime } from '@/utils/tools'
const router = useRouter()
const props = defineProps({
  userInfo: {
    type: Object,
    required: true,
    default: () => ({
      email: '',
      level: '',
      storage: 0,
      create_at: ''
    })
  }
})

// 使用toRefs确保响应式
const { userInfo } = toRefs(props)

// 总空间100MB = 104857600字节
const totalBytes = 104857600

// 计算存储空间百分比
const storagePercentage = computed(() => {
  const percentage = (userInfo.value.storage / totalBytes) * 100;
  return Math.min(100, parseFloat(percentage.toFixed(2)));
});


// 格式化存储显示
const formattedStorage = computed(() => {
  // const MB = userInfo.value.storage / (1024 * 1024)
  const MB = 45895785 / (1024 * 1024)
  return MB.toFixed(2) + ' MB'
})

// 升级存储空间
const upgradeStorage = () => {
  router.push('/upgrade')
}
</script>

<style scoped lang="scss">
.basic-info {
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.5;

  .info-row {
    display: flex;
    min-height: 40px;
    align-items: center;

    .info-label {
      display: inline-block;
      width: 84px;
      text-align: right;
      color: #888;
      margin-right: 16px;
      font-weight: normal;
      flex-shrink: 0;
    }

    .info-content {
      flex: 1;
      color: #333;
      display: flex;
      align-items: center;
      min-height: 40px;
      padding: 4px 0;
    }
  }

  .user-level {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 13px;

    background: #f5f5f5;
    color: #666;

    &.vip {
      background: #fff8e6;
      color: #e6a23c;
      font-weight: 500;
    }

    .vip-icon {
      width: 14px;
      height: 14px;
      margin-left: 6px;
    }
  }

  .storage-display {
    width: 100%;
    margin-top: 2px;

    .storage-bar {
      height: 10px;
      background: #f0f0f0;
      border-radius: 5px;
      margin: 8px 0;
      overflow: hidden;

      .storage-used {
        height: 100%;
        background: #67c23a;
        border-radius: 5px;
        transition: width 0.3s ease;

        &.warning {
          background: #e6a23c;
        }
      }
    }

    .storage-details {
      display: flex;
      align-items: center;
      font-size: 13px;
      margin-top: -2px;

      .storage-text {
        color: #666;
        margin-right: 12px;
      }

      .storage-percent {
        color: #333;
        font-weight: 500;
        margin-right: auto;
      }

      .upgrade-btn {
        padding: 0 6px;
        margin-left: 8px;
        height: 24px;
      }
    }
  }
}
</style>
