<template>
  <el-dialog
    v-model="visible"
    destroy-on-close
    title="术语编辑器"
    width="90%"
    modal-class="term_dialog"
  >
    <template #header="{ close, titleId, titleClass }">
      <span class="title">术语编辑器</span>
      <el-switch v-model="localForm.share_flag" active-value="Y" inactive-value="N" />
      <div class="flag_tips">共享{{ localForm.share_flag == 'Y' ? '开启' : '关闭' }}</div>
    </template>
    <el-form
      ref="termformRef"
      :model="localForm"
      :rules="rules"
      label-position="top"
      hide-required-asterisk="true"
    >
      <el-row :gutter="20">
        <el-col :span="24">
          <el-form-item label="术语表标题" required prop="title" width="100%">
            <el-input
              v-model="localForm.title"
              type="text"
              placeholder="请输入术语表标题"
              maxlength="50"
            />
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12">
          <el-form-item label="源语种" required prop="origin_lang" width="100%">
            <el-select
              v-model="localForm.origin_lang"
              placeholder="请选择"
              filterable
              allow-create
              clearable
            >
              <el-option
                v-for="lang in props.langs"
                :key="lang"
                :name="lang"
                :value="lang"
              ></el-option>
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12">
          <el-form-item label="对照语种" required prop="target_lang" width="100%">
            <el-select
              v-model="localForm.target_lang"
              placeholder="请选择"
              filterable
              allow-create
              clearable
            >
              <el-option
                v-for="lang in props.langs"
                :key="lang"
                :name="lang"
                :value="lang"
              ></el-option>
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24">
          <div class="term_custom flex_box flex-between">
            <div class="label">术语</div>
            <div class="button_box">
              <el-button type="text" @click="openQuick">快速编辑</el-button>
              <div class="icon_add" @click="addTermContent">+</div>
            </div>
          </div>
        </el-col>
        <el-col :span="24" v-for="(item, index) in localForm.content" :key="index">
          <div class="term_set_li flex_box flex-between">
            <div class="form">
              <el-row :gutter="20">
                <el-col :xs="24" :sm="12">
                  <el-form-item
                    label=""
                    required
                    :prop="'content.' + index + '.origin'"
                    :rules="rules.origin"
                    width="100%"
                  >
                    <el-input v-model="item.origin" type="text" maxlength="512" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12">
                  <el-form-item
                    label=""
                    required
                    :prop="'content.' + index + '.target'"
                    :rules="rules.target"
                    width="100%"
                  >
                    <el-input v-model="item.target" type="text" maxlength="512" />
                  </el-form-item>
                </el-col>
              </el-row>
            </div>
            <div class="icon_del" @click="delTermContent(index)">-</div>
          </div>
        </el-col>
      </el-row>
    </el-form>
    <template #footer>
      <div class="btn_box">
        <el-button :disabled="props.loading" @click="close">取消</el-button>
        <el-button
          type="primary"
          color="#055CF9"
          :disabled="props.loading"
          :props.loading="props.loading"
          @click="confirm"
        >
          保存
        </el-button>
      </div>
    </template>
  </el-dialog>
  <!-- 快速编辑 -->
  <el-dialog v-model="termQuickShow" title="快速编辑器" width="90%" modal-class="term_dialog">
    <div class="tips">
      一行一个，请输入源语种和目标语种，中间用英文逗号隔开，示例：易和网,EHEWON
    </div>
    <el-form
      ref="quickFormRef"
      :model="quickForm"
      :rules="rules"
      label-position="top"
      hide-required-asterisk="true"
    >
      <el-form-item label="" required prop="textarea" width="100%">
        <el-input
          v-model="quickForm.textarea"
          type="textarea"
          rows="10"
          resize="none"
          placeholder="请输入"
        />
      </el-form-item>
    </el-form>
    <div class="btn_box">
      <el-button @click="termQuickShow = false">取消</el-button>
      <el-button type="primary" color="#055CF9" @click="quickConfim(quickFormRef)">保存</el-button>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
const termformRef = ref(null)
// 快速编辑弹窗
const termQuickShow = ref(false)
//快速编辑器form
const quickForm = ref({
  textarea: ''
})
const validatePass = (rule, value, callback) => {
  termformRef.value.clearValidate(['origin_lang', 'target_lang'])
  if (
    localForm.value.origin_lang != '' &&
    localForm.value.target_lang != '' &&
    localForm.value.origin_lang == localForm.value.target_lang
  ) {
    callback(new Error('源语种与对照语种不能一样'))
  } else {
    callback()
  }
}
const rules = {
  title: [{ required: true, message: '请填写术语标题', trigger: ['blur', 'change'] }],
  origin_lang: [
    { required: true, message: '请选择源语种', trigger: ['blur', 'change'] },
    { validator: validatePass, trigger: ['blur', 'change'] }
  ],
  target_lang: [
    { required: true, message: '请选择对照语种', trigger: ['blur', 'change'] },
    { validator: validatePass, trigger: ['blur', 'change'] }
  ],
  origin: [{ required: true, message: '请填写源语种内容', trigger: ['blur', 'change'] }],
  target: [{ required: true, message: '请填写目标语种内容', trigger: ['blur', 'change'] }],
  textarea: [{ required: true, message: '请填写相应内容', trigger: ['blur', 'change'] }]
}
const props = defineProps({
  langs: Array,
  loading: Boolean
})
// 内部管理 visible 状态
const visible = ref(false)

const localForm = ref({
  content: [{ origin: '示例源语种', target: '示例目标语种' }],
  title: '',
  share_flag: 'N',
  origin_lang: '',
  target_lang: ''
})

const emit = defineEmits(['confirm'])

// 打开对话框
const open = () => {
  visible.value = true
}

// 关闭对话框
const close = () => {
  visible.value = false
}

const confirm = () => {
  termformRef.value.validate((valid) => {
    if (valid) {
      emit('confirm', localForm.value) // 将 localForm 传递给父组件
      close()
    }
  })
}
const quickFormRef = ref(null)
//打开快速编辑
function openQuick() {
  termQuickShow.value = true
}

//快速编辑确认
function quickConfim() {
  quickFormRef.value.validate((valid, messages) => {
    if (valid) {
      // 按行分割文本域内容
      const lines = quickForm.value.textarea.trim().split('\n')
      const newTerms = []

      for (const line of lines) {
        const arr = line.split(',').map((item) => item.trim())
        if (arr.length === 2 && arr.every((item) => item !== '')) {
          newTerms.push({ origin: arr[0], target: arr[1] })
        } else {
          ElMessage({
            message: '第 ' + (lines.indexOf(line) + 1) + ' 行格式有误，无法快速添加！',
            type: 'error'
          })
          return
        }
      }

      // 将解析后的数据批量添加到 localForm.content 数组中
      localForm.value.content.push(...newTerms)
      // 关闭快速编辑弹窗
      termQuickShow.value = false
    }
  })
}

//添加对照翻译方法
function addTermContent() {
  localForm.value.content.push({ origin: '', target: '' })
}
//删除对照语言一组
function delTermContent(index) {
  if (localForm.value.content.length <= 1) {
    ElMessage({
      message: '至少保留一组！',
      type: 'error'
    })
    return false
  }
  localForm.value.content.splice(index, 1)
}
// 更新form
function updateForm(newForm) {
  if (!newForm.content || newForm.content.length === 0) {
    newForm.content = [{ origin: '', target: '' }]
  }
  localForm.value = newForm
}
// 暴露 open 方法给父组件
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
