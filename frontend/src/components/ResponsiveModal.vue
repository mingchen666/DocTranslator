<template>
  <teleport to="body">
    <transition name="overlay-fade">
      <div v-if="modelValue" class="responsive-overlay" @click.self="handleOverlayClick"></div>
    </transition>
    <transition :name="isMobile ? 'drawer-slide-up' : 'dialog-zoom'">
      <div v-if="modelValue" :class="['responsive-modal', isMobile ? 'mobile-drawer' : 'desktop-dialog']" :style="dialogStyle">
        <div class="modal-header">
          <slot name="header">
            <h3 class="modal-title">{{ title }}</h3>
          </slot>
          <button class="modal-close" @click="handleClose" v-if="showClose">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <div class="modal-body">
          <slot></slot>
        </div>
        <div class="modal-footer" v-if="$slots.footer">
          <slot name="footer"></slot>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '' },
  width: { type: String, default: '560px' },
  showClose: { type: Boolean, default: true },
  closeOnClickOverlay: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue'])

const windowWidth = ref(window.innerWidth)
const isMobile = computed(() => windowWidth.value < 768)

const dialogStyle = computed(() => {
  if (isMobile.value) return {}
  return { width: props.width }
})

const handleResize = () => {
  windowWidth.value = window.innerWidth
}

const handleClose = () => {
  emit('update:modelValue', false)
}

const handleOverlayClick = () => {
  if (props.closeOnClickOverlay) {
    handleClose()
  }
}

watch(() => props.modelValue, (val) => {
  document.body.style.overflow = val ? 'hidden' : ''
}, { immediate: true })

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  document.body.style.overflow = ''
})
</script>

<style scoped>
.overlay-fade-enter-active,
.overlay-fade-leave-active {
  transition: opacity 0.25s ease;
}
.overlay-fade-enter-from,
.overlay-fade-leave-to {
  opacity: 0;
}

.dialog-zoom-enter-active,
.dialog-zoom-leave-active {
  transition: all 0.25s ease;
}
.dialog-zoom-enter-from,
.dialog-zoom-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(-10px);
}

.drawer-slide-up-enter-active,
.drawer-slide-up-leave-active {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.drawer-slide-up-enter-from,
.drawer-slide-up-leave-to {
  transform: translateY(100%);
}

.responsive-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 2000;
}

.responsive-modal {
  z-index: 2001;
  background: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.desktop-dialog {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  max-height: 85vh;
}

.mobile-drawer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  border-radius: 16px 16px 0 0;
  box-shadow: 0 -8px 30px rgba(0, 0, 0, 0.12);
  max-height: 92vh;
}

.mobile-drawer::before {
  content: '';
  display: block;
  width: 36px;
  height: 4px;
  border-radius: 2px;
  background: #d1d5db;
  margin: 8px auto 0;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 12px;
  border-bottom: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.mobile-drawer .modal-header {
  padding-top: 12px;
}

.modal-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: #f1f5f9;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #64748b;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.modal-close:hover {
  background: #e2e8f0;
  color: #334155;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
}

.modal-body::-webkit-scrollbar {
  width: 4px;
}

.modal-body::-webkit-scrollbar-thumb {
  background-color: rgba(100, 116, 139, 0.2);
  border-radius: 2px;
}

.modal-footer {
  padding: 12px 20px 16px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  flex-shrink: 0;
}

.mobile-drawer .modal-body {
  padding: 14px 16px;
}

.mobile-drawer .modal-footer {
  padding: 10px 16px 20px;
}

.mobile-drawer .modal-footer .el-button {
  flex: 1;
}
</style>
