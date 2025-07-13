<template>
  <div class="custom-alert" :class="[`alert-${type}`]" :style="{ borderLeftColor: borderColor }">
    <div class="alert-content">
      <span v-if="showIcon" class="alert-icon">
        <slot name="icon">
          <component :is="iconComponent" />
        </slot>
      </span>
      <div class="alert-text">
        <h4 v-if="title" class="alert-title">{{ title }}</h4>
        <p v-if="description" class="alert-description">{{ description }}</p>
        <slot></slot>
      </div>
      <button v-if="closable" @click="$emit('close')" class="alert-close">
        &times;
      </button>
    </div>
  </div>
</template>

<script>
import { defineComponent, computed } from 'vue'

export default defineComponent({
  name: 'CustomAlert',
  props: {
    title: String,
    description: String,
    type: {
      type: String,
      default: 'info',
      validator: (val) => ['info', 'success', 'warning', 'error', 'primary'].includes(val)
    },
    showIcon: {
      type: Boolean,
      default: true
    },
    closable: {
      type: Boolean,
      default: false
    },
    borderColor: String
  },
  setup(props) {
    const iconMap = {
      info: 'i-carbon-information',
      success: 'i-carbon-checkmark-filled',
      warning: 'i-carbon-warning',
      error: 'i-carbon-error',
      primary: 'i-carbon-information'
    }

    const iconComponent = computed(() => iconMap[props.type] || 'i-carbon-information')

    return { iconComponent }
  }
})
</script>

<style scoped>
.custom-alert {
  padding: 12px 16px;
  margin: 10px 0;
  border-radius: 4px;
  border-left: 4px solid;
  background-color: #f8f8f8;
  display: flex;
  align-items: flex-start;
}

.alert-content {
  display: flex;
  width: 100%;
}

.alert-icon {
  margin-right: 12px;
  font-size: 18px;
}

.alert-text {
  flex: 1;
}

.alert-title {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
}

.alert-description {
  margin: 0;
  font-size: 13px;
  color: #666;
}

.alert-close {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  padding: 0;
  margin-left: 12px;
}

/* 类型样式 */
.alert-info {
  border-left-color: #1890ff;
  background-color: #e6f7ff;
}

.alert-success {
  border-left-color: #52c41a;
  background-color: #f6ffed;
}

.alert-warning {
  border-left-color: #faad14;
  background-color: #fffbe6;
}

.alert-error {
  border-left-color: #f5222d;
  background-color: #fff1f0;
}

.alert-primary {
  border-left-color: #722ed1;
  background-color: #f9f0ff;
}
</style>
