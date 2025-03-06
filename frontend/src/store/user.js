
import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useUserStore = defineStore('user', () => {
  const token = ref('');
const userInfo= ref({})
  const updateToken = (newToken) => {
    token.value = newToken;
  };

  const updateUserInfo = (newValue) => {
    userInfo.value=newValue
  };


  return {
    token,
    userInfo,
    updateToken,
    updateUserInfo,
  };
}, {
  persist: true, // 启用持久化
});
