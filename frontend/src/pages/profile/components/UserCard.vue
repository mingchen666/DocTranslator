<template>
  <el-card class="user-profile-card" :class="{'vip-user': userInfo.level === 'vip'}">
    <div class="profile-content">
      <div class="avatar-container">
        <el-avatar :size="72" :src="userInfo.avatar || defaultAvatar" />
        <!-- 仅VIP显示徽章 -->
        <div v-if="userInfo.level === 'vip'" class="vip-badge">
          <el-icon><CrownFilled /></el-icon>
        </div>
      </div>
      
      <div class="user-details">
        <div class="name-row">
          <h3 class="username">{{ userInfo.username }}</h3>
          <!-- 仅VIP显示标签 -->
          <span v-if="userInfo.level === 'vip'" class="vip-tag">
            <el-icon><StarFilled /></el-icon>
            尊享会员
          </span>
        </div>
        
        <div class="meta-row">
          <div class="meta-item">
            <el-icon class="meta-icon"><Message /></el-icon>
            <span>{{ userInfo.email }}</span>
          </div>
          <div class="meta-item">
            <el-icon class="meta-icon"><Calendar /></el-icon>
            <span>注册于 {{ formatTime(userInfo.created_at) || '未知时间' }}</span>
          </div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<style scoped lang="scss">
.user-profile-card {
  border: none;
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  
  /* 普通用户样式（保持简洁） */
  .profile-content {
    display: flex;
    align-items: flex-start;
    padding: 20px;
    
    .avatar-container {
      position: relative;
      margin-right: 20px;
      
      .el-avatar {
        background: #f5f7fa;
        border: 3px solid white;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
      }
    }
    
    .user-details {
      flex: 1;
      
      .name-row {
        display: flex;
        align-items: center;
        margin-bottom: 12px;
        
        .username {
          font-size: 18px;
          font-weight: 600;
          color: #333;
        }
      }
      
      .meta-row {
        display: flex;
        flex-direction: column;
        gap: 8px;
        
        .meta-item {
          display: flex;
          align-items: center;
          font-size: 14px;
          color: #666;
          
          .meta-icon {
            margin-right: 8px;
            font-size: 16px;
            color: #999;
          }
        }
      }
    }
  }
  
  /* VIP用户专属样式 */
  &.vip-user {
    border-left: 3px solid #409eff;
    background: linear-gradient(to right, #f5faff 0%, white 15%);
    
    .avatar-container .vip-badge {
      position: absolute;
      top: -6px;
      right: -6px;
      width: 24px;
      height: 24px;
      background: #409eff;
      border-radius: 50%;
      border: 2px solid white;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .el-icon {
        color: white;
        font-size: 12px;
      }
    }
    
    .username {
      color: #175ce6;
    }
    
    .vip-tag {
      margin-left: 10px;
      padding: 2px 8px;
      background: #409eff;
      color: white;
      font-size: 12px;
      border-radius: 10px;
      display: inline-flex;
      align-items: center;
      
      .el-icon {
        margin-right: 4px;
        font-size: 12px;
      }
    }
    
    .meta-icon {
      color: #409eff !important;
    }
  }
}
</style>



<script setup>
import { formatTime } from '@/utils/tools'
defineProps({
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
</script>