<template>
  <el-dialog
    v-model="formSetShow"
    title="翻译设置"
    width="90%"
    modal-class="setting_dialog"
    :close-on-click-modal="false"
    @close="formCancel"
  >
    <!-- 当前服务显示 -->
    <div class="current-service-display">
      <span class="current-service-label">当前翻译服务：</span>
      <span class="current-service-value">{{ getServiceName(settingsForm.currentService) }}</span>
    </div>

    <el-form ref="transformRef" :model="settingsForm" label-width="100px">
      <el-form-item label="翻译服务" required width="100%">
        <el-select v-model="settingsForm.currentService" placeholder="请选择翻译服务">
          <el-option value="ai" label="AI翻译"></el-option>
          <el-option value="baidu" label="百度翻译"></el-option>
          <el-option value="google" label="谷歌翻译"></el-option>
        </el-select>
      </el-form-item>

      <!-- AI翻译设置 -->
      <template v-if="settingsForm.currentService === 'ai'">
        <el-form-item label="模型" required width="100%">
          <el-select
            v-model="settingsForm.aiServer.model"
            placeholder="请选择或自定义模型"
            clearable
            filterable
            allow-create
          >
            <el-option
              v-for="model in settingsStore.system_settings.models"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备用模型" width="100%">
          <el-select
            v-model="settingsForm.aiServer.backup_model"
            placeholder="备用模型在翻译模型不可用时自动切换"
            clearable
            filterable
            allow-create
          >
            <el-option
              v-for="model in settingsStore.system_settings.models"
              :disabled="settingsForm.aiServer.model === model"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目标语言" required width="100%">
          <el-select v-model="settingsForm.aiServer.lang" placeholder="请选择目标语言">
            <el-option
              v-for="lang in languageOptions"
              :key="lang.value"
              :label="lang.label"
              :value="lang.value"
            />
          </el-select>
        </el-form-item>
        <!-- 译文形式 -->
        <el-form-item label="译文形式" required>
          <el-cascader
            v-model="settingsForm.common.type"
            :options="typeOptions"
            placeholder="选择译文形式"
            style="width: 100%"
            :props="{ expandTrigger: 'hover' }"
            clearable
          />
        </el-form-item>
        <!-- 提示语选择 -->
        <el-form-item label="选择提示语" required width="100%">
          <el-select
            v-model="settingsForm.aiServer.prompt_id"
            placeholder="请选择提示语"
            filterable
            @change="prompt_id_change"
            @focus="prompt_id_focus"
          >
            <el-option
              v-for="item in promptData"
              :key="item.id"
              :value="item.id"
              :label="item.title"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="提示语内容" width="100%">
          <el-input
            v-model="settingsForm.aiServer.prompt"
            type="textarea"
            :rows="4"
            resize="none"
            placeholder="请输入系统翻译提示词"
          />
        </el-form-item>
        <el-form-item label="术语库" width="100%">
          <el-select
            v-model="settingsForm.aiServer.comparison_id"
            placeholder="请选择术语"
            clearable
            filterable
            @focus="comparison_id_focus"
          >
            <el-option
              v-for="term in translateStore.terms"
              :key="term.id"
              :label="term.title"
              :value="term.id"
            />
          </el-select>
        </el-form-item>
      </template>

      <!-- 百度翻译设置 -->
      <template v-else-if="settingsForm.currentService === 'baidu'">
        <el-form-item label="源语言" required width="100%">
          <el-select v-model="settingsForm.baidu.from_lang" placeholder="请选择源语言">
            <el-option
              v-for="lang in translateStore.langOptions"
              :key="lang.value"
              :label="lang.label"
              :value="lang.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目标语言" required width="100%">
          <el-select v-model="settingsForm.baidu.to_lang" placeholder="请选择目标语言">
            <el-option
              v-for="lang in translateStore.langOptions.filter((l) => l.value !== 'auto')"
              :key="lang.value"
              :label="lang.label"
              :value="lang.value"
            />
          </el-select>
        </el-form-item>
        <!-- 是否使用术语库 -->
        <el-form-item label="使用术语库">
          <el-switch
            v-model="settingsForm.baidu.needIntervene"
            inline-prompt
            active-text="是"
            inactive-text="否"
          />
        </el-form-item>
      </template>

      <!-- 谷歌翻译设置 -->
      <template v-else-if="settingsForm.currentService === 'google'">
        <el-form-item label="项目ID" required width="100%">
          <el-input v-model="settingsForm.google.project_id" placeholder="请输入谷歌翻译项目ID" />
        </el-form-item>
        <el-form-item label="源语言" required width="100%">
          <el-select v-model="settingsForm.google.from_lang" placeholder="请选择源语言">
            <el-option
              v-for="lang in translateStore.langOptions"
              :key="lang.value"
              :label="lang.label"
              :value="lang.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目标语言" required width="100%">
          <el-select v-model="settingsForm.google.to_lang" placeholder="请选择目标语言">
            <el-option
              v-for="lang in translateStore.langOptions.filter((l) => l.value !== 'auto')"
              :key="lang.value"
              :label="lang.label"
              :value="lang.value"
            />
          </el-select>
        </el-form-item>
      </template>

      <!-- 通用设置 -->
      <el-divider />

      <el-form-item label="线程数" required width="100%">
        <el-input-number
          v-model="settingsForm.aiServer.threads"
          :min="1"
          :max="20"
          :controls="true"
          style="width: 50%"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="btn_box">
        <div class="btn_check">
          <el-button class="custom_btn" type="primary" @click="check" :loading="checking">
            <div class="flex_box">
              <img src="@/assets/warn.png" alt="" />
              检查
            </div>
          </el-button>
          <el-tag v-if="check_text && check_text === 'success'" type="success">成功</el-tag>
          <el-tag v-if="check_text && check_text === 'fail'" type="danger">失败</el-tag>
        </div>
        <el-button @click="formReset">重置设置</el-button>
        <el-button type="primary" color="#055CF9" @click="formConfim(transformRef)">确认</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useTranslateStore } from '@/store/translate'
import { useSettingsStore } from '@/store/settings'
import { ElMessage } from 'element-plus'
import { prompt_my, comparison_my } from '@/api/corpus'
import {  checkOpenAI, checkDocx } from '@/api/trans'
const translateStore = useTranslateStore()
const settingsStore = useSettingsStore()
const formSetShow = ref(false)
const checking = ref(false)
const check_text = ref('')
const transformRef = ref(null)
const promptData = ref([])
const termsData = ref([])
//检查docx2
const docx2_title = ref('检查')
const docx2_loading = ref(false)
// 本地表单数据
const settingsForm = ref({
  currentService: translateStore.currentService,
  aiServer: { ...translateStore.aiServer },
  baidu: { ...translateStore.baidu },
  google: { ...translateStore.google },
  common: { ...translateStore.common }
})
// 定义语言映射
const languageMap = {
  chi_sim: '中文',
  // chi_tra: '中文（繁体）',
  eng: '英语',
  jpn: '日语',
  kor: '韩语',
  fra: '法语',
  spa: '西班牙语',
  rus: '俄语',
  ara: '阿拉伯语',
  deu: '德语'
}
// 创建语言选项数组
const languageOptions = computed(() => {
  return Object.values(languageMap).map((label) => ({
    value: label, // key 和 value 都使用中文名称
    label: label
  }))
})
// 译文形式选项
const typeOptions = [
  {
    value: 'trans_text',
    label: '仅文字部分',
    children: [
      {
        value: 'trans_text_only',
        label: '仅译文',
        children: [
          { value: 'trans_text_only_new', label: '重排版面' },
          { value: 'trans_text_only_inherit', label: '继承原版面' }
        ]
      },
      {
        value: 'trans_text_both',
        label: '原文+译文',
        children: [
          { value: 'trans_text_both_new', label: '重排版面' },
          { value: 'trans_text_both_inherit', label: '继承原版面' }
        ]
      }
    ]
  },
  {
    value: 'trans_all',
    label: '全部内容',
    children: [
      {
        value: 'trans_all_only',
        label: '仅译文',
        children: [
          { value: 'trans_all_only_new', label: '重排版面' },
          { value: 'trans_all_only_inherit', label: '继承原版面' }
        ]
      },
      {
        value: 'trans_all_both',
        label: '原文+译文',
        children: [
          { value: 'trans_all_both_new', label: '重排版面' },
          { value: 'trans_all_both_inherit', label: '继承原版面' }
        ]
      }
    ]
  }
]
// 监听当前服务变化
watch(
  () => settingsForm.value.currentService,
  (newVal) => {
    translateStore.updateCurrentService(newVal)
  }
)

// 服务名称映射
const getServiceName = (service) => {
  const names = {
    ai: 'AI翻译',
    baidu: '百度翻译',
    google: '谷歌翻译'
  }
  return names[service] || service
}

// 获取术语库
const comparison_id_focus = async () => {
  try {
    const res = await comparison_my()
    if (res.code === 200) {
      translateStore.terms = res.data.data
    }
  } catch (error) {
    console.error('获取术语库失败:', error)
  }
}

// 获取提示语数据
const prompt_id_focus = async () => {
  try {
    const res = await prompt_my()
    if (res.code === 200) {
      // promptData.value.push(res.data.data)
      promptData.value = res.data.data
      // 添加默认提示词
      promptData.value.unshift({
        id: 0,
        title: '默认系统提示语',
        content: settingsStore.system_settings.prompt_template,
      })
    }
  } catch (error) {
    console.error('获取提示语数据失败:', error)
  }
}

const rules = {
  server: [{ required: true, message: '请选择翻译服务', trigger: 'blur' }],
  model: [{ required: true, message: '请选择模型', trigger: 'blur' }],
  backup_model: [{ required: false }],
  prompt: [{ required: true, message: '请输入提示语', trigger: 'blur' }],
  prompt_id: [{ required: false }],
  project_id: [
    {
      required: settingsForm.value.currentService === 'google',
      message: '请输入谷歌翻译项目ID',
      trigger: 'blur'
    }
  ],
  from_lang: [
    {
      required: settingsForm.value.currentService !== 'ai',
      message: '请选择源语言',
      trigger: 'blur'
    }
  ],
  to_lang: [
    {
      required: settingsForm.value.currentService !== 'ai',
      message: '请选择目标语言',
      trigger: 'blur'
    }
  ],
  comparison_id: [{ required: false }],
  threads: [
    {
      required: true,
      message: '请设置线程数',
      trigger: 'blur'
    },
    {
      type: 'number',
      min: 1,
      max: 20,
      message: '线程数必须在1到20之间',
      trigger: 'blur'
    }
  ]
}

// 提示语选择变化
const prompt_id_change = (id) => {
  const selectedPrompt = promptData.value.find((item) => item.id === id)
  if (selectedPrompt) {
    settingsForm.value.aiServer.prompt = selectedPrompt.content
    settingsForm.value.aiServer.prompt_id = id
  }
}
//检查功能实现
function check1() {
  checking.value = true
  check_text.value = ''
  checkOpenAI(form.value)
    .then((data) => {
      checking.value = false
      if (data.code == 200) {
        check_text.value = 'success'
      } else {
        check_text.value = 'fail'
        ElMessage({
          message: data.message,
          type: 'error'
        })
      }
    })
    .catch((err) => {
      checking.value = false
      check_text.value = 'fail'
      ElMessage({
        message: '接口异常',
        type: 'error'
      })
    })
}
// doc2x检查
function docx2_check1() {
  docx2_loading.value = true
  let _prarms = {
    doc2x_secret_key: form.value.doc2x_secret_key
  }
  checkDocx(_prarms)
    .then((data) => {
      docx2_loading.value = false
      if (data.code == 0) {
        docx2_title.value = '成功'
      } else if (data.code == 1) {
        docx2_title.value = '失败'
        ElMessage({
          message: 'key值无效',
          type: 'error'
        })
      } else {
        docx2_title.value = '失败'
        ElMessage({
          message: data.message,
          type: 'error'
        })
      }
    })
    .catch((err) => {
      docx2_loading.value = false
      docx2_title.value = '失败'
      ElMessage({
        message: '接口异常',
        type: 'error'
      })
    })
}
// 检查连接
const check = async () => {
  checking.value = true
  check_text.value = ''

  try {
    // 根据当前服务调用不同的检查API
    let res
    if (settingsForm.value.currentService === 'ai') {
      // res = await checkOpenAI({...})
    } else if (settingsForm.value.currentService === 'baidu') {
      // res = await checkBaidu({...})
    } else if (settingsForm.value.currentService === 'google') {
      // res = await checkGoogle({...})
    }

    check_text.value = res?.code === 200 ? 'success' : 'fail'
  } catch (error) {
    check_text.value = 'fail'
    ElMessage.error('检查失败: ' + error.message)
  } finally {
    checking.value = false
  }
}

// 重置设置
const formReset = () => {
  settingsForm.value = {
    currentService: translateStore.currentService,
    aiServer: { ...translateStore.aiServer },
    baidu: { ...translateStore.baidu },
    google: { ...translateStore.google },
    common: { ...translateStore.common },
    comparison_id: ''
  }
  check_text.value = ''
}

// 保存弹窗翻译设置
const formConfim = (formEl) => {
  if (!formEl) return
  formEl.validate((valid) => {
    if (valid) {
      // 更新store中的数据
      translateStore.updateCurrentService(settingsForm.value.currentService)

      if (settingsForm.value.currentService === 'ai') {
        translateStore.updateAIServerSettings(settingsForm.value.aiServer)
      } else if (settingsForm.value.currentService === 'baidu') {
        translateStore.updateBaiduSettings(settingsForm.value.baidu)
      } else if (settingsForm.value.currentService === 'google') {
        translateStore.updateGoogleSettings(settingsForm.value.google)
      }
console.log('settingsForm.value.common',settingsForm.value.common);

      translateStore.updateCommonSettings(settingsForm.value.common)
      ElMessage.success('设置保存成功')
      formSetShow.value = false
    }
  })
}

// 取消设置
const formCancel = () => {
  formSetShow.value = false
}
const open = () => {
  formSetShow.value = true
  // 初始化表单数据
  settingsForm.value = {
    currentService: translateStore.currentService,
    aiServer: { ...translateStore.aiServer },
    baidu: { ...translateStore.baidu },
    google: { ...translateStore.google },
    common: { ...translateStore.common },
  }
}

function docx2_check() {
  docx2_loading.value = true
  let _prarms = {
    doc2x_secret_key: form.value.doc2x_secret_key
  }
  checkDocx(_prarms)
    .then((data) => {
      docx2_loading.value = false
      if (data.code == 0) {
        docx2_title.value = '成功'
      } else if (data.code == 1) {
        docx2_title.value = '失败'
        ElMessage({
          message: 'key值无效',
          type: 'error'
        })
      } else {
        docx2_title.value = '失败'
        ElMessage({
          message: data.message,
          type: 'error'
        })
      }
    })
    .catch((err) => {
      docx2_loading.value = false
      docx2_title.value = '失败'
      ElMessage({
        message: '接口异常',
        type: 'error'
      })
    })
}
// 暴露方法
defineExpose({
  open
})
</script>

<style scoped lang="scss">
/* 当前服务显示样式 */
.current-service-display {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding: 8px 0;
  border-bottom: 1px solid #eee;

  .current-service-label {
    font-size: 14px;
    color: #666;
    margin-right: 10px;
  }

  .current-service-value {
    font-size: 14px;
    font-weight: bold;
    color: #055cf9;
  }
}

/* 原有弹窗样式 */
.setting_dialog {
  .el-dialog {
    max-width: 800px;
    padding: 30px 70px;

    &__title {
      color: #111111;
    }

    &__headerbtn {
      font-size: 20px;
      right: 10px;
      top: 10px;

      i {
        color: #111;
      }
    }

    &__body {
      padding: 0 30px 0 30px;
    }
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

    .btn_check {
      position: absolute;
      left: 0;

      .el-tag {
        height: 28px;
        margin-left: 10px;
      }
    }

    .custom_btn {
      background: #fff;
      color: #055cf9;
      height: 28px;
      padding: 0 10px;

      &:hover {
        color: #055cf9;
        background: var(--el-color-primary-light-9);
      }
    }
  }
}

.no_label {
  label {
    opacity: 0;
  }

  .flex_box {
    width: 100%;

    .el-input {
      flex: 1;
      margin-right: 10px;
    }
  }
}
</style>

<style lang="scss">
/* 全局样式 - 完全按照原项目写法 */
@media screen and (max-width: 767px) {
  .current-service-display {
    margin-bottom: 15px;
    padding: 6px 0;

    .current-service-label,
    .current-service-value {
      font-size: 13px;
    }
  }

  .setting_dialog {
    .el-dialog {
      padding: 20px !important;

      &__body {
        padding: 0 !important;
        max-height: 300px;
        overflow-y: auto;

        .el-form-item {
          display: block !important;
          margin-bottom: 10px;
        }
      }
    }

    .btn_box {
      text-align: right !important;
    }
  }

  .no_label {
    label {
      display: none;
    }
  }
}
.setting_dialog1 {
  .el-dialog {
    padding: 20px !important;
  }
  .el-dialog__body {
    padding: 0 !important;
    max-height: 300px;
    overflow-y: auto;
    .el-form-item {
      display: block !important;
      margin-bottom: 10px;
    }
  }
  .btn_box {
    text-align: right !important;
  }
}
</style>
