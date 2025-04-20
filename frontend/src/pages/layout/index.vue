<template>
  <div class="page-container">
    <layout-header></layout-header>
    <router-view></router-view>
    <!-- <layout-footer></layout-footer> -->
  </div>
</template>
<script setup>
import layoutHeader from './header.vue'
// import layoutFooter from './footer.vue'
</script>
<style scoped>
.page-container {
  width: 100%;
  height: 100vh;
  background: #f3f8ff;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
