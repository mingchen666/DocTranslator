<template>
  <div class="page-header">
    <div class="head-box">
      <div class="logo">
        <img src="@/assets/logo.png" class="logo_img" alt="EZ-work" />
        <span>{{ store.pTitle }}</span>
        <a class="btn_return" href="https://www.ehemart.com/" v-if="editionInfo == 'community'"
          ><<返回官网</a
        >
        <img
          class="icon_vip phone_show"
          style="height: 16px; margin-left: 10px"
          v-if="store.level == 'vip'"
          src="@/assets/vip.png"
          alt=""
        />
      </div>
      <!-- 社区版 -->
      <div class="btn-box" v-if="editionInfo == 'business'">
        <template v-if="store.token">
          <div class="flex-center">
            <div class="btn_set" @click="funOpenHome">
              <div class="icon_svg"><svg-icon icon-class="home" /></div>
              <span class="pc_show">首页</span>
            </div>
            <div class="btn_set" @click="funOpenCorpus">
              <div class="icon_svg"><svg-icon icon-class="corpus" /></div>
              <span class="pc_show">语料库</span>
            </div>
            <div class="btn_set" @click="funOpenSet">
              <div class="icon_svg"><svg-icon icon-class="setting" /></div>
              <span class="pc_show">翻译设置</span>
            </div>
            <img
              class="icon_vip pc_show"
              v-if="store.level == 'vip'"
              src="@/assets/vip.png"
              alt=""
            />
            <el-dropdown placement="bottom-end" @command="user_action">
              <template #default>
                <div>
                  <el-button class="pc_show">
                    <div class="username" :title="store.username">{{ store.username }}</div>
                    <el-icon class="el-icon--right"><arrow-down /></el-icon>
                  </el-button>
                  <div class="phone_show icon_more">
                    <el-icon><MoreFilled /></el-icon>
                  </div>
                </div>
              </template>

              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="pwd">修改密码</el-dropdown-item>
                  <el-dropdown-item command="exit">退出</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
        <template v-else>
          <el-button class="pc_show" @click="$router.push('/login')">登录/注册</el-button>
          <el-icon class="phone_show icon_user" @click="$router.push('/login')"><User /></el-icon>
        </template>
      </div>
      <!-- 演示版 -->
      <div class="btn-box" v-if="editionInfo == 'community'">
        <div class="flex-center">
          <div class="btn_set" @click="funOpenSet">
            <div class="icon_svg"><svg-icon icon-class="setting" /></div>
            <span class="pc_show">翻译设置</span>
          </div>
          <div
            class="btn_set"
            @click="
              windowOpen('https://github.com/EHEWON/ezwork-ai-doc-translation?tab=readme-ov-file')
            "
          >
            <div class="icon_svg"><svg-icon icon-class="github" /></div>
            <span class="pc_show">Github</span>
          </div>
          <div class="btn_set" @click="windowOpen('https://support.qq.com/product/670074')">
            <div class="icon_svg"><svg-icon icon-class="question" /></div>
            <span class="pc_show">问题反馈</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 退出弹窗 -->
    <el-dialog
      v-model="logoutVisible"
      modal-class="custom_dialog"
      center
      :show-close="false"
      width="90%"
      heigt="240px"
      style="border-radius: 20px"
    >
      <div class="dialog-container">
        <div class="dialog-title">退出登录</div>
        <div class="dialog-content">您确定要退出登录吗？</div>
        <div class="dialog-btns">
          <el-button class="dialog-btn cancel" @click="logoutVisible = false">取消</el-button>
          <el-button
            class="dialog-btn confirm"
            type="primary"
            color="#055CF9"
            @click="confirmLogout"
            >确认</el-button
          >
        </div>
      </div>
    </el-dialog>

    <!-- 翻译设置弹窗 pc -->
    <el-dialog
      v-model="formSetShow"
      title="翻译设置"
      width="90%"
      modal-class="setting_dialog"
      @close="formCancel"
    >
      <el-form ref="transformRef" :model="form" label-width="100px" :rules="rules">
        <el-form-item label="服务商" required prop="server" width="100%">
          <el-select v-model="form.server" placeholder="请选择服务商" disabled @change="saveValue">
            <el-option value="openai" label="OpenAI"></el-option>
            <el-option value="member" label="EZ-work 会员"></el-option>
          </el-select>
        </el-form-item>
        <template v-if="form.server == 'openai'">
          <el-form-item label="接口地址" required prop="api_url" width="100%">
            <el-input v-model="form.api_url" placeholder="请输入接口（base_url）地址"></el-input>
          </el-form-item>
          <el-form-item label="API Key" required prop="api_key" width="100%">
            <el-input v-model="form.api_key" placeholder="请输入OpenAI的API KEY" show-password
              >></el-input
            >
          </el-form-item>
        </template>
        <el-form-item label="模型" required prop="model" width="100%">
          <el-select
            v-model="form.model"
            placeholder="请选择或自定义OpenAI模型"
            clearable
            filterable
            allow-create
          >
            <el-option
              v-for="model in models"
              :key="model"
              :name="model"
              :value="model"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="备用模型" prop="backup_model" width="100%">
          <el-select
            v-model="form.backup_model"
            placeholder="备用模型在翻译模型不可用时自动切换并继续完成翻译。"
            clearable
            filterable
            allow-create
          >
            <el-option
              v-for="model in models"
              :disabled="form.model == model ? true : false"
              :key="model"
              :name="model"
              :value="model"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="翻译语言" required prop="langs" width="100%">
          <div class="language-selection">
            <!--<template v-if="form.scanned">
              <el-select v-model="form.origin_lang" placeholder="请选择起始语言" class="lang-select">
                <el-option v-for="lang in languageOptions" :key="lang.value" :label="lang.label" :value="lang.value"></el-option>
              </el-select>
              <div class="conversion-symbol">→</div>
            </template>-->
            <el-select
              v-model="form.langs"
              placeholder="请选择或自定义翻译语言"
              clearable
              filterable
              allow-create
              :multiple="langMultiSelected"
              :multiple-limit="langMultipleLimit"
              class="lang-select"
            >
              <el-option v-for="lang in langs" :key="lang" :name="lang" :value="lang"></el-option>
            </el-select>
          </div>
        </el-form-item>
        <el-form-item label="译文形式" required prop="type" width="100%">
          <el-cascader
            class="type-cascader"
            placeholder="请选择译文形式"
            v-model="form.type"
            :options="types"
            clearable
            :props="{ expandTrigger: 'hover' }"
            style="width: 100%"
          >
          </el-cascader>
        </el-form-item>
        <!-- <el-form-item label="译文形式" required prop="type">
            <el-select v-model="form.type" placeholder="请选择译文形式">
                <el-option value="translation" label="仅译文"></el-option>
                <el-option value="both" label="原文+译文"></el-option>
            </el-select>
        </el-form-item> -->
        <el-form-item label="术语" width="100%" v-if="editionInfo == 'business'">
          <el-select
            v-model="form.comparison_id"
            placeholder="请选择术语"
            clearable
            filterable
            :fit-input-width="true"
          >
            <el-option
              v-for="item in termsData"
              :key="item.id"
              :value="item.id"
              :label="item.title"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="提示语" prop="prompt_id" width="100%" v-if="editionInfo != 'business'">
          <el-select
            v-model="form.prompt_id"
            placeholder="请选择提示语"
            filterable
            @change="prompt_id_change($event)"
            :fit-input-width="true"
          >
            <el-option
              v-for="item in promptData"
              :key="item.id"
              :value="item.id"
              :label="item.title"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="提示语" prop="prompt" width="100%" v-else>
          <el-input
            v-model="form.prompt"
            autosize
            type="textarea"
            :rows="3"
            resize="none"
            placeholder="请输入系统翻译提示词"
          ></el-input>
        </el-form-item>

        <el-form-item label="线程数" required prop="threads" width="100%">
          <el-input-number
            style="width: 100%"
            :min="10"
            :max="40"
            v-model="form.threads"
            :controls="false"
            placeholder="注意：高线程≥10虽可以缩短翻译时长，但服务器负载较高，易引发异常，请谨慎使用！"
          ></el-input-number>
        </el-form-item>

        <el-form-item label="Doc2x" required prop="threads" width="100%" style="margin-bottom: 0px">
          <el-radio-group v-model="form.doc2x_flag">
            <el-radio value="N" size="large">不启用</el-radio>
            <el-radio value="Y" size="large">启用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item
          label=" "
          prop="doc2x_secret_key"
          width="100%"
          v-if="form.doc2x_flag == 'Y'"
          class="no_label"
        >
          <div class="flex_box">
            <el-input v-model="form.doc2x_secret_key" placeholder="请输入Doc2x的API KEY"></el-input>
            <el-button :disabled="docx2_loading" :loading="docx2_loading" @click="docx2_check">{{
              docx2_title
            }}</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="btn_box">
          <div class="btn_check">
            <el-button class="custom_btn" type="primary" @click="check" :loading="checking">
              <div class="flex_box"><img src="@/assets/warn.png" alt="" />检查</div>
            </el-button>
            <el-tag v-if="check_text && check_text == 'success'" type="success">成功</el-tag>
            <el-tag v-if="check_text && check_text == 'fail'" type="danger">失败</el-tag>
          </div>
          <el-button @click="formReset">重置设置</el-button>
          <el-button type="primary" color="#055CF9" @click="formConfim(transformRef)"
            >确认</el-button
          >
        </div>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { useRouter } from 'vue-router'
import { store } from '@/store/index'
import { authInfo, getSetting } from '@/api/account'
import { translateSetting, checkOpenAI, checkDocx } from '@/api/trans'
import { comparison_my, prompt_my } from '@/api/corpus'
import { ref, computed, watch, defineProps, onMounted } from 'vue'
import SvgIcon from '@/components/SvgIcon/index.vue'
import $bus from '@/bus'
import { ElMessage, ElMessageBox } from 'element-plus'
store.setTitle('DocTranslator AI文档翻译')
const router = useRouter()
const props = defineProps({
  title: String,
  authDialog: Boolean
})
const logoutVisible = ref(false)
const editionInfo = ref(false)

//翻译设置 相关代码提炼
const formSetShow = ref(false)
const translatesSettingData = ref({})
const checking = ref(false)
const check_text = ref('')
const transformRef = ref(null)
const langMultiSelected = ref(true)
const langMultipleLimit = ref(5)
//新增术语、提示语
const termsData = ref([])
const promptData = ref([])

//检查docx2
const docx2_title = ref('检查')
const docx2_loading = ref(false)

const models = ref([])
const types = [
  {
    value: 'trans_text',
    label: '仅文字部分',
    children: [
      {
        value: 'trans_text_only',
        label: '仅译文',
        children: [
          {
            value: 'trans_text_only_new',
            label: '重排版面'
          },
          {
            value: 'trans_text_only_inherit',
            label: '继承原版面'
          }
        ]
      },
      {
        value: 'trans_text_both',
        label: '原文+译文',
        children: [
          {
            value: 'trans_text_both_new',
            label: '重排版面'
          },
          {
            value: 'trans_text_both_inherit',
            label: '继承原版面'
          }
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
          {
            value: 'trans_all_only_new',
            label: '重排版面'
          },
          {
            value: 'trans_all_only_inherit',
            label: '继承原版面'
          }
        ]
      },
      {
        value: 'trans_all_both',
        label: '原文+译文',
        children: [
          {
            value: 'trans_all_both_new',
            label: '重排版面'
          },
          {
            value: 'trans_all_both_inherit',
            label: '继承原版面'
          }
        ]
      }
    ]
  }
]

const langs = ['中文', '英语', '日语', '俄语', '阿拉伯语', '西班牙语']
// 定义语言映射
const languageMap = {
  chi_sim: '中文（简体）',
  chi_tra: '中文（繁体）',
  eng: '英语',
  jpn: '日语',
  kor: '韩语',
  fra: '法语',
  spa: '西班牙语',
  rus: '俄语',
  ara: '阿拉伯语',
  deu: '德语'
  // ... 添加更多 Tesseract 支持的语言
}

// 创建语言选项数组
const languageOptions = computed(() => {
  return Object.entries(languageMap).map(([value, label]) => ({
    value,
    label
  }))
})

const form = ref({
  server: store.level == 'vip' ? 'member' : 'openai',
  api_url: 'https://api.openai.com',
  api_key: '',
  model: '',
  backup_model: '',
  langs: [],
  lang: '',
  type: [],
  uuid: '',
  prompt:
    '你是一个文档翻译助手，请将以下文本、单词或短语直接翻译成{target_lang}，不返回原文本。如果文本中包含{target_lang}文本、特殊名词（比如邮箱、品牌名、单位名词如mm、px、℃等）、无法翻译等特殊情况，请直接返回原文而无需解释原因。遇到无法翻译的文本直接返回原内容。保留多余空格。',
  threads: 10,
  scanned: false, // 添加 scanned 字段
  origin_lang: '', // 添加起始语言字段
  comparison_id: '', //术语id
  prompt_id: '', //提示语id
  doc2x_flag: 'N',
  doc2x_secret_key: ''
})

const rules = {
  files: [{ required: true, message: '请上传文件', trigger: ['blur', 'change'] }],
  api_url: [
    {
      required: true,
      message: '请输入接口地址',
      trigger: ['blur', 'change']
    }
  ],
  api_key: [
    {
      required: true,
      message: '请输入API Key',
      trigger: ['blur', 'change']
    }
  ],
  server: [{ required: true, message: '请选择供应商', trigger: ['blur', 'change'] }],
  type: [{ required: true, message: '请选择译文形式', trigger: ['blur', 'change'] }],
  model: [{ required: true, message: '请选择模型', trigger: ['blur', 'change'] }],
  langs: [{ required: true, message: '请选择翻译目标语言', trigger: ['blur', 'change'] }],
  prompt: [{ required: true, message: '请填写系统提示语', trigger: ['blur', 'change'] }],
  prompt_id: [{ required: true, message: '请选择提示语', trigger: ['blur', 'change'] }],
  threads: [{ required: true, message: '请填写线程数', trigger: ['blur', 'change'] }],
  doc2x_secret_key: [
    { required: true, message: '请输入Doc2x的API KEY', trigger: ['blur', 'change'] }
  ]
}

onMounted(() => {
  getSetting().then((data) => {
    editionInfo.value = data.data.version
    store.setVersion(editionInfo.value)
    if (data.data.version == 'business') {
      authInfo().then((data) => {
        store.setUsername(data.data.email)
        store.setLevel(data.data.level)
        getTranslateSetting()
      })
    } else {
      getTranslateSetting()
    }
  })
})

//监听用户自动登录
watch(
  () => store.token,
  (n, o) => {
    getTranslateSetting()
  }
)

//更新术语数据
watch(
  () => store.comparisonList,
  (n, o) => {
    termsData.value = n
    if (form.value.comparison_id) {
      const obj = termsData.value.find((item) => item.id === form.value.comparison_id)
      if (!obj) {
        form.value.comparison_id = ''
        localStorage.setItem('comparison_id', form.value.comparison_id)
        //通知翻译主页面 更新form设置数值
        $bus.emit('HeadForm', true)
      }
    }
  }
)

//更新提示语数据
watch(
  () => store.promptList,
  (n, o) => {
    promptData.value = n
    if (form.value.prompt_id > 0) {
      const obj = promptData.value.find((item) => item.id === form.value.prompt_id)
      if (!obj) {
        form.value.prompt_id = 0
        form.value.prompt = store.prompt
        localStorage.setItem('prompt', form.value.prompt)
        localStorage.setItem('prompt_id', form.value.prompt_id)
        //通知翻译主页面 更新form设置数值
        $bus.emit('HeadForm', true)
      }
    }
  }
)

//未登录打开登录弹窗
$bus.on('shouldAuth', (param) => {
  authVisible.value = param
})

//打开翻译设置
$bus.on('openTransSet', (param) => {
  funOpenSet()
})

//监听翻译设置
$bus.on('LangLimitVal', (param) => {
  langMultipleLimit.value = param
  if (param == 1) {
    if (form.value.langs.length > 1) {
      form.value.langs = []
    }
  }
})

//提示语选择框选择事件
function prompt_id_change(e) {
  const obj = promptData.value.find((item) => item.id === e)
  form.value.prompt = obj.content
}

//获取设置项信息
function getTranslateSetting() {
  translateSetting().then((data) => {
    if (data.code == 200) {
      let setting = data.data
      if (setting.api_url) {
        form.value.api_url = setting.api_url
      }
      if (setting.api_key) {
        form.value.api_key = setting.api_key
      }
      models.value = setting.models
      form.value.model = setting.default_model
      form.value.backup_model = setting.default_backup
      form.value.prompt = setting.prompt_template
      form.value.threads = setting.threads
      translatesSettingData.value = setting

      store.setPrompt(setting.prompt)

      //社区版获取术语列表
      if (editionInfo.value == 'business') {
        getTermList()
        getPromptList()
      }
    }
    if (localStorage.getItem('api_url')) {
      form.value.api_url = localStorage.getItem('api_url')
    }
    if (localStorage.getItem('api_key')) {
      form.value.api_key = localStorage.getItem('api_key')
    }
    if (localStorage.getItem('model')) {
      form.value.model = localStorage.getItem('model')
    }
    if (localStorage.getItem('backup_model')) {
      form.value.backup_model = localStorage.getItem('backup_model')
    }
    if (localStorage.getItem('langs')) {
      form.value.langs = JSON.parse(localStorage.getItem('langs'))
    }
    if (localStorage.getItem('type')) {
      form.value.type = JSON.parse(localStorage.getItem('type'))
    }
    if (localStorage.getItem('prompt')) {
      form.value.prompt = localStorage.getItem('prompt')
    }
    if (localStorage.getItem('threads')) {
      form.value.threads = localStorage.getItem('threads')
    }
    if (localStorage.getItem('doc2x_flag')) {
      form.value.doc2x_flag = localStorage.getItem('doc2x_flag')
    }
    if (localStorage.getItem('doc2x_secret_key')) {
      form.value.doc2x_secret_key = localStorage.getItem('doc2x_secret_key')
    }
  })
}

//获取术语表数据
function getTermList() {
  comparison_my().then((data) => {
    if (data.code == 0) {
      termsData.value = data.data.data
      if (localStorage.getItem('comparison_id')) {
        form.value.comparison_id = Number(localStorage.getItem('comparison_id'))
      }
    }
  })
}

//获取提示语数据
function getPromptList() {
  prompt_my().then((data) => {
    if (data.code == 0) {
      promptData.value = data.data.data
      if (store.prompt) {
        promptData.value.unshift({ title: '默认提示语', id: 0, content: store.prompt })
        form.value.prompt_id = 0
        form.value.prompt = store.prompt
        if (localStorage.getItem('prompt_id')) {
          form.value.prompt_id = Number(localStorage.getItem('prompt_id'))
          const obj = promptData.value.find((item) => item.id === form.value.prompt_id)
          if (obj) {
            form.value.prompt = obj.content
          } else {
            form.value.prompt_id = 0
            form.value.prompt = store.prompt
          }
        }
      }
    }
  })
}

//翻译设置取消
function formCancel() {
  formSetShow.value = false
}
//翻译重置
function formReset() {
  let setting = translatesSettingData.value
  if (setting.api_url) {
    form.value.api_url = setting.api_url
  } else {
    form.value.api_url = 'https://api.openai.com'
  }
  if (setting.api_key) {
    form.value.api_key = setting.api_key
  } else {
    form.value.api_key = ''
  }
  form.value.model = setting.default_model
  form.value.backup_model = setting.default_backup
  form.value.prompt = setting.prompt
  form.value.threads = setting.threads
  form.value.prompt_id = 0
  form.value.comparison_id = ''
  form.value.doc2x_flag = 'N'
  form.value.doc2x_secret_key = ''

  //清空以下数据
  form.value.langs = []
  form.value.type = []
}

//翻译设置确认
function formConfim(transformRef) {
  transformRef.validate((valid, messages) => {
    if (valid) {
      //确认
      localStorage.setItem('api_url', form.value.api_url)
      localStorage.setItem('api_key', form.value.api_key)
      //模型
      localStorage.setItem('model', form.value.model)
      //备用
      localStorage.setItem('backup_model', form.value.backup_model)
      //翻译语言
      localStorage.setItem('langs', JSON.stringify(form.value.langs))
      //译文形式
      localStorage.setItem('type', JSON.stringify(form.value.type))
      localStorage.setItem('prompt', form.value.prompt)
      localStorage.setItem('threads', form.value.threads)
      localStorage.setItem('comparison_id', form.value.comparison_id)
      localStorage.setItem('prompt_id', form.value.prompt_id)
      localStorage.setItem('doc2x_flag', form.value.doc2x_flag)
      localStorage.setItem('doc2x_secret_key', form.value.doc2x_secret_key)

      formSetShow.value = false
      //通知翻译主页面 更新form设置数值
      $bus.emit('HeadForm', true)
    }
  })
}

//检查功能实现
function check() {
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

//用户操作
function user_action(command) {
  if (command == 'pwd') {
    router.push('/reset')
  }
  if (command == 'exit') {
    logoutVisible.value = !logoutVisible.value
  }
}

function menuSelect(index) {
  activeIndex.value = index
}

//打开设置弹窗
function funOpenSet() {
  formSetShow.value = true
}

//打开语料库
function funOpenCorpus() {
  router.push('/corpus')
}

//回到首页
function funOpenHome() {
  router.push('/')
}

//演示版入口
function windowOpen(url) {
  window.open(url)
}

function goToLogin() {
  router.push('/login')
}

function cancelLogout() {
  logoutVisible.value = false
}
function confirmLogout() {
  store.setToken('')
  logoutVisible.value = false
}
</script>
<style scoped lang="scss">
.page-header {
  width: 100%;
  height: 60px;
  background: #ffffff;
  box-shadow: 0px 0px 12px 0px rgba(0, 22, 52, 0.05);
}
.head-box {
  max-width: 1240px;
  padding: 0 20px;
  margin: 0 auto;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.logo {
  display: flex;
  align-items: center;
  img {
    height: 44px;
  }
  span {
    font-size: 20px;
    font-weight: bold;
    margin-left: 20px;
  }
  .btn_return {
    color: #045cf9;
    margin-left: 10px;
    font-size: 14px;
    text-decoration: none;
    cursor: pointer;
  }
}
::v-deep {
  .btn_set {
    display: flex;
    align-items: center;
    margin-right: 20px;
    font-size: 14px;
    color: #000000;
    cursor: pointer;
    img {
      margin-right: 8px;
    }
    .icon_svg {
      margin-right: 8px;
      font-size: 16px;
      color: #666;
    }
    &:hover {
      color: #045cf9;
      .icon_svg {
        color: #045cf9;
      }
    }
  }
  .icon_vip {
    margin-right: 12px;
  }
  .username {
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 30px;
  }
  .el-dropdown {
    .el-tooltip__trigger {
      outline: none;
    }
    .el-button {
      outline: none;
    }
  }

  .custom_dialog {
    .el-dialog__header {
      padding-bottom: 0;
      font-size: 16px;
      color: #111;
    }
    .el-dialog {
      max-width: 410px;
      padding: 20px;
    }
  }
  .custom_2_dialog {
    .el-dialog {
      max-width: 410px;
    }
  }
  .change_dialog {
    .el-dialog {
      padding: 20px 40px;
    }
    .el-dialog__header {
      margin-top: 10px;
      margin-bottom: 20px;
    }
  }

  .dialog-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }
  .dialog-title {
    font-weight: bold;
    font-size: 20px;
    color: #111111;
    line-height: 24px;
    margin-top: 30px;
    margin-bottom: 20px;
  }
  .dialog-content {
    font-family: 'PingFang SC';
    font-weight: 400;
    font-size: 16px;
    color: #999999;
    line-height: 24px;
    margin-bottom: 40px;
  }
  .dialog-btns {
    margin-bottom: 30px;
  }
  .dialog-btn {
    width: 120px;
  }
  .dialog-btn.cancel {
    margin-right: 4px;
  }
  .dialog-btn.send-confirm {
    width: 327px;
  }
  .login_dialog1 {
    .el-dialog {
      padding: 20px 40px;
    }
    .el-menu {
      border: none;
      height: 65px;
    }
    .el-menu-item {
      padding: 0;
      height: 40px;
      font-size: 20px;
      font-family: PingFang SC;
      margin: 0 15px;
      background: #fff !important;
    }
  }
  .forget-title {
    display: flex;
    justify-content: space-between;
    margin-top: 10px;
    margin-bottom: 30px;
    .el-text {
      font-size: 22px;
      color: #111111;
    }
    .el-icon {
      font-size: 24px;
    }
  }

  .setting_dialog {
    .el-dialog {
      max-width: 800px;
      padding: 30px 70px;
    }
    .el-dialog__title {
      color: #111111;
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
      padding: 0 30px 0 30px;
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
}
</style>
<style type="text/css" lang="scss">
.flex_box {
  display: flex;
  align-items: center;
}
.flex-between {
  justify-content: space-between;
}
.flex-center {
  display: flex;
  align-items: center;
  justify-content: space-around;
}
.menu-center {
  justify-content: center;
}
.menu-title {
  font-family: 'PingFang SC';
  font-weight: bold;
  font-size: 22px;
  color: #8f8f91;
  line-height: 24px;
}
.menu-title.active {
  color: #111111;
}
.phone_show {
  display: none !important;
}

.language-selection {
  display: flex;
  align-items: center;
  gap: 10px; /* 调整元素之间的间距 */
  width: 100%;
}
.lang-select {
  width: 100%; /* 默认宽度为100% */
  transition: width 0.3s ease; /* 添加过渡效果 */
}
.language-selection:has(.conversion-symbol) .lang-select {
  width: 100%; /* 当有转换符号时，设置宽度为45% */
}
.conversion-symbol {
  font-size: 20px;
  color: #409eff; /* 使用 Element Plus 的主色调，可以根据需要调整 */
  flex-shrink: 0; /* 防止符号被压缩 */
}
@media screen and (max-width: 767px) {
  .pc_show {
    display: none !important;
  }
  .phone_show {
    display: inline-block !important;
  }
  .icon_user {
    font-size: 30px !important;
  }
  .logo span {
    font-size: 14px !important;
    margin-left: 10px !important;
  }
  .icon_more {
    font-size: 20px;
  }
  .btn_set {
    margin-right: 6px !important;
  }
  .logo_img {
    height: 30px !important;
  }

  .setting_dialog {
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

  .no_label {
    label {
      display: none;
    }
  }
}
</style>
