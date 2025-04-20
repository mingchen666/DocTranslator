
import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useUserStore = defineStore('user-info', () => {
  const token = ref('');
  const userInfo = ref({
    "email": "",
    "level": "",
    "created_at": "",
    "storage": 56584439
  })

  const updateToken = (newToken) => {
    token.value = newToken;
  };

  const updateUserInfo = (newValue) => {
    userInfo.value = newValue
  };
  const updateStorage = (newValue) => {
    userInfo.value.storage = newValue
  };
  // 退出登录
  const logout = () => {
    token.value = '';
    userInfo.value = {}
  };

  return {
    token,
    userInfo,
    updateToken,
    updateUserInfo,
    logout,
    updateStorage
  };
}, {
  persist: true, // 启用持久化
});
