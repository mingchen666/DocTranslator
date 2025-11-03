
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useUserStore = defineStore('user-info', () => {
  const token = ref('');
  const userInfo = ref({
    "email": "",
    "level": "",
    "created_at": "",
    "storage": null,
    "total_storage": 10000000
  })
  const isLogin = computed(() => {
    return token.value !== '';
  });
  const isVip = computed(() => {
    return userInfo.value.level === 'vip';
  });

  const updateToken = (newToken) => {
    token.value = newToken;
  };

  const updateUserInfo = (newValue) => {
    userInfo.value = newValue
  };
  const updateStorage = ({ storage, total_storage }) => {
    userInfo.value.storage = storage
    userInfo.value.total_storage = total_storage
  };
  // 退出登录
  const logout = () => {
    token.value = '';
    userInfo.value = {}
  };

  return {
    token,
    userInfo,
    isVip,
    updateToken,
    updateUserInfo,
    logout,
    isLogin,
    updateStorage
  };
}, {
  persist: true, // 启用持久化
});
