<template>
  <div class="user-hero-card" :class="{ 'is-vip': userInfo.level === 'vip' }">
    <div class="card-bg-accent"></div>
    <div class="user-content">
      <div class="avatar-section">
        <el-avatar :size="56" :src="userInfo.avatar || defaultAvatar" />
        <div v-if="userInfo.level === 'vip'" class="vip-badge-float">
          <img src="@/assets/vip.png" alt="VIP" />
        </div>
      </div>
      <div class="info-section">
        <div class="name-row">
          <h2 class="username">{{ userInfo.name || userInfo.email || '未设置昵称' }}</h2>
          <span class="role-tag" :class="userInfo.level">
            <el-icon v-if="userInfo.level === 'vip'"><Trophy /></el-icon>
            {{ userInfo.level === 'vip' ? '尊享会员' : '普通用户' }}
          </span>
        </div>
        <div class="meta-grid">
          <div class="meta-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
            <span>{{ userInfo.email || '未绑定邮箱' }}</span>
          </div>
          <div class="meta-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            <span>注册于 {{ formatTime(userInfo.created_at) || '未知' }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { formatTime } from '@/utils/tools'
import { Trophy } from '@element-plus/icons-vue'
import defaultAvatar from '@/assets/avator.png'
defineProps({
  userInfo: {
    type: Object,
    required: true,
    default: () => ({})
  }
})
</script>

<style scoped lang="scss">
.user-hero-card {
  position: relative;
  background: white;
  border-radius: 16px;
  padding: 20px 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  overflow: hidden;

  .card-bg-accent {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6, #3b82f6);
    z-index: 1;
  }

  &.is-vip {
    .card-bg-accent {
      background: linear-gradient(90deg, #f6d365, #fda085, #f6d365);
    }

    border: 1px solid rgba(253, 160, 133, 0.15);
  }

  .user-content {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    gap: 20px;
  }
}

.avatar-section {
  position: relative;
  flex-shrink: 0;

  :deep(.el-avatar) {
    border: 2px solid #e2e8f0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  }

  .vip-badge-float {
    position: absolute;
    bottom: -2px;
    right: -4px;
    width: 22px;
    height: 22px;
    padding: 2px;
    background: white;
    border-radius: 50%;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);

    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
  }
}

.info-section {
  flex: 1;
  min-width: 0;

  .name-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 6px;

    .username {
      font-size: 20px;
      font-weight: 700;
      color: #1e293b;
      margin: 0;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .role-tag {
      font-size: 11px;
      padding: 3px 10px;
      border-radius: 20px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 4px;
      flex-shrink: 0;
      background: #f1f5f9;
      color: #64748b;

      &.vip {
        background: linear-gradient(135deg, #fce38a 0%, #f38181 100%);
        color: #fff;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
      }
    }
  }

  .meta-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    color: #94a3b8;
    font-size: 13px;

    .meta-item {
      display: flex;
      align-items: center;
      gap: 5px;

      svg {
        flex-shrink: 0;
      }

      span {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
  }
}

@media (max-width: 576px) {
  .user-hero-card {
    padding: 16px;
    border-radius: 12px;

    .user-content {
      flex-direction: column;
      text-align: center;
      gap: 12px;
    }
  }

  .info-section {
    .name-row {
      justify-content: center;
      flex-wrap: wrap;
    }

    .meta-grid {
      flex-direction: column;
      gap: 6px;
      align-items: center;
    }
  }
}
</style>
