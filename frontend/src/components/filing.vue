<template>
  <!-- 版权信息 -->
  <div class="filing">
    <a
      href="https://github.com/mingchen666/DocTranslator"
      target="_blank"
      rel="noopener noreferrer"
      class="copyright-link"
    >
      <p>© 2026 DocTranslator 1.6.0 保留所有权利</p>
    </a>
  </div>
</template>

<style scoped lang="scss">
.filing {
  width: 100%;
  font-size: 14px;
  text-align: center;
  padding: 20px 0;
  box-sizing: border-box;
  line-height: 20px;

  .copyright-link {
    display: inline-block;
    text-decoration: none;
    transition: all 0.3s ease;
    padding: 8px 10px;
    border-radius: 8px;

    p {
      color: #949db0;
      margin: 0;
      transition: color 0.3s ease;
    }

    &:hover {
      p {
        color: #3b82f6;
      }
    }
  }
}

/* 移动端适配 */
@media (max-width: 576px) {
  .filing {
    font-size: 12px;
    padding: 16px 0;

    .copyright-link {
      padding: 6px 12px;
    }
  }
}
</style>
