<template>
  <div class="translation-settings-container">
    <el-tabs v-model="activeTab" class="settings-tabs">
      <!-- AI翻译设置 -->
      <el-tab-pane label="AI翻译" name="ai">
        <ai-translation-settings ref="aiSettingsForm" />
      </el-tab-pane>

      <!-- 机器翻译设置 -->
      <el-tab-pane label="机器翻译" name="machine">
        <machine-translation-settings ref="machineSettingsForm" />
      </el-tab-pane>

      <!-- 通用设置 -->
      <el-tab-pane label="通用设置" name="common">
        <common-settings ref="commonSettingsForm" />
      </el-tab-pane>
    </el-tabs>

    <!-- <div class="action-buttons">
      <el-button type="primary" @click="saveAllSettings">保存所有设置</el-button>
    </div> -->
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AiTranslationSettings from './AiTranslationSettings.vue'
import MachineTranslationSettings from './MachineTranslationSettings.vue'
import CommonSettings from './CommonSettings.vue'
const activeTab = ref('ai')

</script>

<style scoped>
.translation-settings-container {
  padding: 20px;
}
.settings-tabs {
  margin-bottom: 20px;
}
.action-buttons {
  text-align: center;
}
</style>
