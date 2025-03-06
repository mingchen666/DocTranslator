<template>
  <el-dialog
    v-model="visible"
    destroy-on-close
    title="提示语编辑器"
    width="90%"
    modal-class="term_dialog"
  >
    <template #header="{ close, titleId, titleClass }">
      <span class="title">提示语编辑器</span>
      <el-switch v-model="localForm.share_flag" active-value="Y" inactive-value="N" />
      <div class="flag_tips">分享{{ localForm.share_flag == 'Y' ? '开启' : '关闭' }}</div>
    </template>
    <el-form
      ref="promptformRef"
      :model="localForm"
      :rules="rules"
      label-position="top"
      hide-required-asterisk="true"
    >
      <el-row :gutter="20">
        <el-col :span="24">
          <el-form-item label="提示语标题" required prop="title" width="100%">
            <el-input
              v-model="localForm.title"
              type="text"
              placeholder="请输入提示语标题"
              maxlength="50"
            />
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="提示语内容" required prop="content" width="100%">
            <el-input
              v-model="localForm.content"
              type="textarea"
              :rows="5"
              resize="none"
              placeholder="请输入"
            />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
    <div class="btn_box">
      <el-button :disabled="loading" @click="close">取消</el-button>
      <el-button
        type="primary"
        color="#055CF9"
        :disabled="loading"
        :loading="loading"
        @click="confirm"
      >
        保存
      </el-button>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  loading: Boolean
})

const rules = {
  title: [{ required: true, message: '请填写提示语标题', trigger: ['blur', 'change'] }],
  content: [{ required: true, message: '请填写提示语内容', trigger: ['blur', 'change'] }]
}

const emit = defineEmits(['confirm', 'close'])

const promptformRef = ref(null)
const visible = ref(false) // 子组件内部控制显示隐藏

// 深拷贝 使用 localForm 管理表单数据
const localForm = ref({
  title: '', //标题
  share_flag: 'N',
  content: ''
})

const open = () => {
  visible.value = true
}
// 关闭弹窗
const close = () => {
  visible.value = false // 隐藏弹窗
}

// 确认保存
const confirm = () => {
  promptformRef.value.validate((valid) => {
    if (valid) {
      emit('confirm', localForm.value) // 将 localForm 传递给父组件
      close()
    }
  })
}
// 更新form
const updateForm = (newForm) => {
  localForm.value = newForm
}
// 暴露方法
defineExpose({
  open,
  close,
  updateForm,
  localForm
})
</script>

<style scoped lang="scss">
::v-deep {
  //弹窗
  .term_dialog {
    padding-top: 20px;
    .el-dialog {
      max-width: 740px;
      padding: 30px 50px;
    }
    .el-dialog__header {
      font-weight: bold;
      font-size: 18px;
      color: #111;
      padding: 0 20px;
      margin-bottom: 16px;
      .title {
        display: inline-block;
        line-height: 32px;
        margin-right: 30px;
      }
      .flag_tips {
        display: inline-block;
        line-height: 32px;
        font-size: 14px;
        color: #111;
        font-weight: normal;
        margin-left: 10px;
      }
    }
    .el-dialog__headerbtn {
      font-size: 20px;
      right: 10px;
      top: 10px;
      i {
        color: #111;
      }
    }
    .el-dialog__body {
      padding: 0px 20px;
      max-height: 450px;
      overflow-y: auto;
    }
    .el-form-item {
      .el-form-item__label {
        justify-content: flex-start;
        color: #111111;
      }
      .el-input-number .el-input__inner {
        text-align: left;
      }
    }
    .btn_box {
      position: relative;
      text-align: center;
    }

    .term_custom {
      width: 100%;
      .label {
        line-height: 22px;
        margin-bottom: 8px;
      }
      .el-button {
        height: auto;
        margin-bottom: 10px;
        padding: 0;
        margin-right: 20px;
      }
      .button_box {
        display: flex;
      }
      .icon_add {
        font-size: 14px;
        color: #ffffff;
        width: 20px;
        height: 20px;
        line-height: 20px;
        background: #055cf9;
        border-radius: 3px;
        text-align: center;
      }
    }
    .term_set_li {
      width: 100%;
      align-items: flex-start;
      .form {
        flex: 1;
        margin-right: 20px;
      }
      .icon_del {
        font-size: 14px;
        color: #ffffff;
        width: 20px;
        height: 20px;
        line-height: 20px;
        background: #ed4014;
        border-radius: 3px;
        text-align: center;
        margin-top: 5px;
      }
    }
    .tips {
      font-size: 14px;
      color: #111111;
      line-height: 24px;
      margin-bottom: 10px;
    }
    .el-switch__core .el-switch__action {
      top: 1px;
    }
  }
}
</style>
