<template>
  <div class="translation-settings-wrapper">
    <div class="section-header">
      <div>
        <h3>翻译设置</h3>
        <p class="subtitle">配置翻译服务提供商和通用偏好</p>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="settings-tabs">
      <el-tab-pane name="ai">
        <template #label>
          <div class="tab-label">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4z"/></svg>
            <span>AI 翻译</span>
          </div>
        </template>
        <ai-translation-settings />
      </el-tab-pane>
      <el-tab-pane name="machine">
        <template #label>
          <div class="tab-label">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>
            <span>机器翻译</span>
          </div>
        </template>
        <machine-translation-settings />
      </el-tab-pane>
      <el-tab-pane name="common">
        <template #label>
          <div class="tab-label">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
            <span>通用设置</span>
          </div>
        </template>
        <common-settings />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AiTranslationSettings from './AiTranslationSettings.vue'
import MachineTranslationSettings from './MachineTranslationSettings.vue'
import CommonSettings from './CommonSettings.vue'
const activeTab = ref('ai')
</script>

<style scoped lang="scss">
.translation-settings-wrapper {
  padding: 4px 0;
}

.section-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 24px;


  h3 {
    font-size: 18px;
    font-weight: 600;
    color: #1e293b;
    margin: 0 0 2px;
  }

  .subtitle {
    font-size: 13px;
    color: #94a3b8;
    margin: 0;
  }
}

.settings-tabs {
  :deep(.el-tabs__nav-wrap::after) {
    height: 1px;
    background-color: #e2e8f0;
  }

  :deep(.el-tabs__item) {
    font-size: 14px;
    color: #64748b;
    height: 44px;
    line-height: 44px;
    padding: 0 16px;

    &.is-active {
      color: #3b82f6;
      font-weight: 600;
    }

    &:hover {
      color: #3b82f6;
    }
  }

  :deep(.el-tabs__active-bar) {
    background-color: #3b82f6;
    height: 2px;
    border-radius: 2px;
  }

  :deep(.el-tabs__content) {
    overflow: visible;
  }
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;

  svg {
    flex-shrink: 0;
  }

  span {
    font-size: 14px;
  }
}

@media (max-width: 576px) {
  .settings-tabs {
    :deep(.el-tabs__item) {
      padding: 0 10px;
      font-size: 13px;
    }
  }

  .tab-label span {
    font-size: 13px;
  }
}
</style>
