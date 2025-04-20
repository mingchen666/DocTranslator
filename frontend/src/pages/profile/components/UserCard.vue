<template>
  <el-card class="user-profile-card">
    <div class="profile-content">
      <el-avatar :size="64" :src="userInfo.avatar || defaultAvatar" />
      <div class="user-details">
        <div class="name-row">
          <span class="username">{{ userInfo.username }}</span>
          <span v-if="userInfo.level === 'vip'" class="vip-badge">
            <el-icon><StarFilled /></el-icon>
          </span>
        </div>
        <div class="meta-row">
          <div class="meta-item">
            <el-icon><Message /></el-icon>
            <span>{{ userInfo.email }}</span>
          </div>
          <div class="meta-item">
            <el-icon><Calendar /></el-icon>
            <span>{{ formatTime(userInfo.created_at) || '未设置' }}</span>
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
  background: #f8fafc;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  
  .profile-content {
    display: flex;
    align-items: center;
    padding: 16px;
    
    .el-avatar {
      background: #e2e8f0;
      margin-right: 20px;
    }
    
    .user-details {
      flex: 1;
      
      .name-row {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
        
        .username {
          font-size: 16px;
          font-weight: 500;
          color: #1e293b;
        }
        
        .vip-badge {
          margin-left: 8px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 20px;
          height: 20px;
          background: linear-gradient(135deg, #f59e0b, #f97316);
          border-radius: 50%;
          
          .el-icon {
            color: white;
            font-size: 12px;
          }
        }
      }
      
      .meta-row {
        display: flex;
        flex-direction: column;
        gap: 6px;
        
        .meta-item {
          display: flex;
          align-items: center;
          font-size: 13px;
          color: #64748b;
          
          .el-icon {
            margin-right: 8px;
            font-size: 14px;
            color: #94a3b8;
          }
        }
      }
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