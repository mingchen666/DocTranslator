<script lang="ts" setup>
const openWebsite = () => {
  window.open("https://www.doctranslator.cn/", "_blank")
}
</script>

<template>
  <footer class="layout-footer">
    <span class="copyright-link" @click="openWebsite"> DocTranslator 1.6.0 © Powered by MingChen </span>
  </footer>
</template>

<style lang="scss" scoped>
.layout-footer {
  width: 100%;
  min-height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-placeholder);

  .copyright-link {
    cursor: pointer;
    text-decoration: none;
    transition: color 0.3s;

    &:hover {
      color: var(--el-color-primary);
    }
  }
}
</style>
