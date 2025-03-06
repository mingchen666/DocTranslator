<template>
  <div
    class="page-center"
    v-loading="pageLoad"
    element-loading-text="loading..."
    element-loading-spinner="el-icon-loading"
    element-loading-background="rgba(255, 255, 255, 0.7)"
  >
    <div class="container">
      <div class="tab_box">
        <div class="tab_li actived">我的</div>
        <div class="tab_li" @click="to_square">广场</div>
      </div>
      <div class="content_box">
        <div class="flex_box flex-between phone_box">
          <el-button-group>
            <el-button
              :class="tab_active == 'terms' ? 'btn_active' : 'my_button'"
              :plain="tab_active == 'terms' ? false : true"
              :type="tab_active == 'terms' ? 'primary' : ''"
              @click="tab_active = 'terms'"
            >
              我的术语表
            </el-button>
            <el-button
              :class="tab_active == 'prompt' ? 'btn_active' : 'my_button'"
              :plain="tab_active == 'prompt' ? false : true"
              :type="tab_active == 'prompt' ? 'primary' : ''"
              @click="tab_active = 'prompt'"
            >
              我的提示语
            </el-button>
          </el-button-group>
          <div class="btn_box" v-if="tab_active == 'terms'">
            <el-button type="primary" color="#055CF9" @click="openTerms()">新建</el-button>
            <el-dropdown split-button type="" style="margin: 0 12px" @command="command_terms">
              <el-upload
                name="file"
                :before-upload="upload_before"
                :action="uploadUrl"
                :show-file-list="false"
                :on-success="(response, file, fileList) => upload_success(response)"
                class="blue_color"
              >
                导入
              </el-upload>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="down">模板下载</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button type="" @click="export_terms_all">全部导出</el-button>
          </div>
          <div class="btn_box" v-if="tab_active == 'prompt'">
            <el-button type="primary" color="#055CF9" @click="openPrompt()">新建</el-button>
          </div>
        </div>
        <div class="term_box" v-if="tab_active == 'terms'">
          <el-row :gutter="24" v-if="termsData.length > 0">
            <el-col :xs="24" :sm="8" v-for="(item, index) in termsData" :key="index">
              <div class="term_li">
                <div class="flex_box title_box flex-between">
                  <div class="t" :title="item.title">{{ item.title }}</div>
                  <div class="des">{{ item.origin_lang }}-{{ item.target_lang }}</div>
                </div>
                <div class="btn_box flex_box flex-between">
                  <div class="left">
                    <el-button type="text" @click="openTerms(item)">编辑</el-button>
                    <el-button type="text" style="color: red" @click="delTerms(item)"
                      >删除</el-button
                    >
                    <el-button type="text" @click="export_terms(item)">导出</el-button>
                  </div>
                  <div class="right">
                    <el-switch
                      v-model="item.share_flag"
                      active-value="Y"
                      inactive-value="N"
                      @change="share_change(item)"
                    />
                  </div>
                </div>
                <div class="table_box" v-if="item.content.length > 0">
                  <el-table
                    :data="item.content"
                    style="width: 100%"
                    max-height="340"
                    border
                    header-cell-class-name="table_title"
                    tooltip-effect="light"
                  >
                    <el-table-column
                      prop="origin"
                      :label="item.origin_lang"
                      show-overflow-tooltip
                    />
                    <el-table-column
                      prop="target"
                      :label="item.target_lang"
                      show-overflow-tooltip
                    />
                  </el-table>
                </div>
              </div>
            </el-col>
          </el-row>
          <div v-else class="no_data">
            <img src="@/assets/nodata.png" alt="" />
            <div class="text">暂无数据</div>
          </div>
        </div>
        <div class="prompt_box" v-if="tab_active == 'prompt'">
          <el-row :gutter="24" v-if="promptData.length > 0">
            <el-col :xs="24" :sm="8" v-for="(item, index) in promptData" :key="index">
              <div class="term_li">
                <div class="flex_box title_box flex-between">
                  <div class="t" :title="item.title">{{ item.title }}</div>
                </div>
                <div class="btn_box flex_box flex-between" v-if="!item.undelete">
                  <div class="left">
                    <el-button type="text" @click="openPrompt(item)">编辑</el-button>
                    <el-button type="text" style="color: red" @click="delPrompt(item)"
                      >删除</el-button
                    >
                  </div>
                  <div class="right">
                    <el-switch
                      v-model="item.share_flag"
                      active-value="Y"
                      inactive-value="N"
                      @change="share_change_prompt(item)"
                    />
                  </div>
                </div>
                <div class="btn_box" v-else></div>
                <div class="text_box">
                  <div class="text">{{ item.content }}</div>
                </div>
              </div>
            </el-col>
          </el-row>
          <div v-else class="no_data">
            <img src="@/assets/nodata.png" alt="" />
            <div class="text">暂无数据</div>
          </div>
        </div>
      </div>
      <!-- 备案信息 -->
      <Filing />
    </div>

    <!-- 术语弹窗页面pc -->
    <el-dialog v-model="termSetShow" title="术语编辑器" width="90%" modal-class="term_dialog">
      <template #header="{ close, titleId, titleClass }">
        <span class="title">术语编辑器</span>
        <el-switch v-model="termForm.share_flag" active-value="Y" inactive-value="N" />
        <div class="flag_tips">分享{{ termForm.share_flag == 'Y' ? '开启' : '关闭' }}</div>
      </template>
      <el-form
        ref="termformRef"
        :model="termForm"
        :rules="rules_term"
        label-position="top"
        hide-required-asterisk="true"
      >
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="术语表标题" required prop="title" width="100%">
              <el-input
                v-model="termForm.title"
                type="text"
                placeholder="请输入术语表标题"
                maxlength="50"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="源语种" required prop="origin_lang" width="100%">
              <el-select v-model="termForm.origin_lang" placeholder="请选择" clearable>
                <el-option v-for="lang in langs" :key="lang" :name="lang" :value="lang"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="对照语种" required prop="target_lang" width="100%">
              <el-select v-model="termForm.target_lang" placeholder="请选择" clearable>
                <el-option v-for="lang in langs" :key="lang" :name="lang" :value="lang"></el-option>
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
          <el-col :span="24" v-for="(item, index) in termForm.content" :key="index">
            <div class="term_set_li flex_box flex-between">
              <div class="form">
                <el-row :gutter="20">
                  <el-col :xs="24" :sm="12">
                    <el-form-item
                      label=""
                      required
                      :prop="'content.' + index + '.origin'"
                      :rules="rules_term.origin"
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
                      :rules="rules_term.target"
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
          <el-button :disabled="btnLoad" @click="termSetShow = false">取消</el-button>
          <el-button
            type="primary"
            color="#055CF9"
            :disabled="btnLoad"
            :loading="btnLoad"
            @click="formConfim(termformRef)"
          >
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 快速编辑 -->
    <el-dialog v-model="termQuickShow" title="快速编辑器" width="90%" modal-class="term_dialog">
      <div class="tips">请输入源语种和目标语种，中间用英文逗号隔开，示例：易和网,EHEWON</div>
      <el-form
        ref="quickFormRef"
        :model="quickForm"
        :rules="rules_term"
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
        <el-button type="primary" color="#055CF9" @click="quickConfim(quickFormRef)"
          >保存</el-button
        >
      </div>
    </el-dialog>

    <!-- 提示语编辑器 -->
    <el-dialog v-model="promptShow" title="提示语编辑器" width="90%" modal-class="term_dialog">
      <template #header="{ close, titleId, titleClass }">
        <span class="title">提示语编辑器</span>
        <el-switch v-model="promptForm.share_flag" active-value="Y" inactive-value="N" />
        <div class="flag_tips">分享{{ promptForm.share_flag == 'Y' ? '开启' : '关闭' }}</div>
      </template>
      <el-form
        ref="promptformRef"
        :model="promptForm"
        :rules="rules_prompt"
        label-position="top"
        hide-required-asterisk="true"
      >
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="提示语标题" required prop="title" width="100%">
              <el-input
                v-model="promptForm.title"
                type="text"
                placeholder="请输入提示语标题"
                maxlength="50"
              />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="提示语内容" required prop="content" width="100%">
              <el-input
                v-model="promptForm.content"
                type="textarea"
                rows="5"
                resize="none"
                placeholder="请输入"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <div class="btn_box">
        <el-button :disabled="btnLoad" @click="promptShow = false">取消</el-button>
        <el-button
          type="primary"
          color="#055CF9"
          :disabled="btnLoad"
          :loading="btnLoad"
          @click="promptConfim(promptformRef)"
        >
          保存
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import Filing from '@/components/filing.vue'
import { useRouter } from 'vue-router'
import { store } from '@/store/index'
import { reactive, ref, computed, watch, inject, defineEmits, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  comparison_my,
  comparison,
  comparison_edit,
  comparison_del,
  comparison_share,
  prompt_add,
  prompt_edit,
  prompt_my,
  prompt_share,
  prompt_del
} from '@/api/corpus'

const router = useRouter()
const uploadUrl = ref(import.meta.env.VITE_API_URL + '/api/comparison/import?token=' + store.token)
const pageLoad = ref(false)
const termsData = ref([])
const promptData = ref([])
const promptDataBefore = ref('')
onMounted(() => {
  getTermList()
  getPromptList()
})

watch(
  () => store.prompt,
  (n, o) => {
    if (n) {
      promptData.value.unshift({
        title: '默认提示语(无法删除)',
        content: store.prompt,
        undelete: true
      })
    }
  }
)

const tab_active = ref('terms')

//获取术语表数据
function getTermList() {
  pageLoad.value = true
  comparison_my().then((data) => {
    if (data.code == 200) {
      termsData.value = data.data.data
      store.setComparisonList(data.data.data)
      pageLoad.value = false
    }
  })
  pageLoad.value = false
}

//获取提示语数据
function getPromptList() {
  pageLoad.value = true
  prompt_my().then((data) => {
    if (data.code == 200) {
      promptData.value = JSON.parse(JSON.stringify(data.data.data))
      if (store.prompt) {
        promptData.value.unshift({
          title: '默认提示语(无法删除)',
          content: store.prompt,
          undelete: true
        })
      }
      const new_arr = JSON.parse(JSON.stringify(data.data.data))
      new_arr.unshift({ title: '默认提示语', id: 0, content: store.prompt })
      store.setPromptList(new_arr)
      pageLoad.value = false
    }
  })
  pageLoad.value = false
}

//术语弹窗
const termSetShow = ref(false)
const termQuickShow = ref(false)
const termformRef = ref(null)
const btnLoad = ref(false)
//提示语弹窗
const promptShow = ref(false)
const promptformRef = ref(null)
//翻译语言
const langs = ['中文', '英语', '日语', '俄语', '阿拉伯语', '西班牙语']
const termForm = ref({
  title: '', //标题
  share_flag: 'N',
  origin_lang: '',
  target_lang: '',
  content: [{ origin: '', target: '' }]
})

const validatePass = (rule, value, callback) => {
  termformRef.value.clearValidate(['origin_lang', 'target_lang'])
  if (
    termForm.value.origin_lang != '' &&
    termForm.value.target_lang != '' &&
    termForm.value.origin_lang == termForm.value.target_lang
  ) {
    callback(new Error('源语种与对照语种不能一样'))
  } else {
    callback()
  }
}
const rules_term = {
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

//快速编辑器form
const quickForm = ref({
  textarea: ''
})
const quickFormRef = ref(null)

//提示语form
const promptForm = ref({
  title: '', //标题
  share_flag: 'N',
  content: ''
})
const rules_prompt = {
  title: [{ required: true, message: '请填写提示语标题', trigger: ['blur', 'change'] }],
  content: [{ required: true, message: '请填写提示语内容', trigger: ['blur', 'change'] }]
}

//打开术语弹窗-编辑
function openTerms(item) {
  termSetShow.value = true
  if (item) {
    termForm.value = JSON.parse(JSON.stringify(item))
  } else {
    termForm.value = {
      title: '', //标题
      share_flag: 'N',
      origin_lang: '',
      target_lang: '',
      content: [{ origin: '', target: '' }]
    }
  }
  //重置校验方法
  if (termformRef.value) {
    termformRef.value.resetFields()
  }
}

//添加对照翻译方法
function addTermContent() {
  termForm.value.content.push({ origin: '', target: '' })
}
//删除对照语言一组
function delTermContent(index) {
  if (termForm.value.content.length <= 1) {
    ElMessage({
      message: '至少保留一组！',
      type: 'error'
    })
    return false
  }
  termForm.value.content.splice(index, 1)
}

//术语表单确认
function formConfim(termformRef) {
  termformRef.validate((valid, messages) => {
    if (valid) {
      btnLoad.value = true
      //是否是编辑
      if (termForm.value.id) {
        comparison_edit(termForm.value.id, termForm.value)
          .then((data) => {
            btnLoad.value = false
            if (data.code == 200) {
              ElMessage({ message: '保存成功', type: 'success' })
              termSetShow.value = false
              getTermList()
            } else {
              ElMessage({ message: data.message, type: 'error' })
            }
          })
          .catch((err) => {
            ElMessage({ message: '接口异常', type: 'error' })
          })
      } else {
        comparison(termForm.value)
          .then((data) => {
            btnLoad.value = false
            if (data.code == 200) {
              ElMessage({ message: '保存成功', type: 'success' })
              termSetShow.value = false
              getTermList()
            } else {
              ElMessage({ message: data.message, type: 'error' })
            }
          })
          .catch((err) => {
            ElMessage({ message: '接口异常', type: 'error' })
          })
      }
    }
  })
  // btnLoad.value = false
}
//删除术语表
function delTerms(item) {
  ElMessageBox.confirm('确定要删除？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    pageLoad.value = true
    comparison_del(item.id).then((data) => {
      if (data.code == 200) {
        ElMessage({ message: '删除成功', type: 'success' })
        getTermList()
      } else {
        ElMessage({ message: data.message, type: 'error' })
      }
    })
  })
}

//术语表 分享状态修改
function share_change(item) {
  pageLoad.value = true
  comparison_share(item.id, { share_flag: item.share_flag })
    .then((data) => {
      pageLoad.value = false
      if (data.code == 200) {
        ElMessage({ message: '操作成功', type: 'success' })
      } else {
        ElMessage({ message: data.message, type: 'error' })
        item.share_flag == 'Y' ? (item.share_flag = 'N') : (item.share_flag = 'Y')
      }
    })
    .catch((err) => {
      ElMessage({ message: '接口异常', type: 'error' })
      item.share_flag == 'Y' ? (item.share_flag = 'N') : (item.share_flag = 'Y')
    })
}

//导出单个术语表
function export_terms(item) {
  window.open(
    import.meta.env.VITE_API_URL + '/api/comparison/export/' + item.id + '?token=' + store.token
  )
}

//导出所有术语表
function export_terms_all() {
  window.open(import.meta.env.VITE_API_URL + '/api/comparison/export/all?token=' + store.token)
}

//术语表模板下载
function command_terms(type) {
  if (type == 'down') {
    window.open(import.meta.env.VITE_API_URL + '/api/comparison/template?token=' + store.token)
  }
}

//上传文件
function upload_success(response) {
  if (response.code == 200) {
    ElMessage({ message: '导入成功', type: 'success' })
    getTermList()
  } else {
    ElMessage({ message: data.message, type: 'error' })
  }
}
//上传文件校验
function upload_before(file) {
  const fileType = file.name.substring(file.name.lastIndexOf('.') + 1)
  const isXlsx = fileType === 'xlsx'
  if (!isXlsx) {
    ElMessage({ message: '请上传模板格式的文件', type: 'error' })
    return false
  }
  return isXlsx
}

//打开快速编辑
function openQuick() {
  termQuickShow.value = true
}
//快速编辑确认
function quickConfim(quickFormRef) {
  quickFormRef.validate((valid, messages) => {
    if (valid) {
      const arr = [...quickForm.value.textarea.split(',')]
      if (arr.length == 2) {
        termForm.value.content.push({ origin: arr[0], target: arr[1] })
        termQuickShow.value = false
      } else {
        ElMessage({ message: '输入格式有误，无法快速添加！', type: 'error' })
      }
    }
  })
}

//打开提示语
function openPrompt(item) {
  promptShow.value = true
  if (item) {
    promptForm.value = JSON.parse(JSON.stringify(item))
  } else {
    promptForm.value = {
      title: '', //标题
      share_flag: 'N',
      content: ''
    }
  }
  //重置校验方法
  if (promptformRef.value) {
    promptformRef.value.resetFields()
  }
}

//提示语确定
function promptConfim(promptformRef) {
  promptformRef.validate((valid, messages) => {
    if (valid) {
      btnLoad.value = true
      //是否是编辑
      if (promptForm.value.id) {
        prompt_edit(promptForm.value.id, promptForm.value)
          .then((data) => {
            btnLoad.value = false
            if (data.code == 200) {
              ElMessage({ message: '保存成功', type: 'success' })
              promptShow.value = false
              getPromptList()
            } else {
              ElMessage({ message: data.message, type: 'error' })
            }
          })
          .catch((err) => {
            ElMessage({ message: '接口异常', type: 'error' })
          })
      } else {
        prompt_add(promptForm.value)
          .then((data) => {
            btnLoad.value = false
            if (data.code == 200) {
              ElMessage({ message: '保存成功', type: 'success' })
              promptShow.value = false
              getPromptList()
            } else {
              ElMessage({ message: data.message, type: 'error' })
            }
          })
          .catch((err) => {
            ElMessage({ message: '接口异常', type: 'error' })
          })
      }
    }
  })
}

//提示语 分享状态修改
function share_change_prompt(item) {
  pageLoad.value = true
  if (item.id) {
    prompt_share(item.id, { share_flag: item.share_flag })
      .then((data) => {
        pageLoad.value = false
        if (data.code == 200) {
          ElMessage({ message: '操作成功', type: 'success' })
        } else {
          ElMessage({ message: data.message, type: 'error' })
          item.share_flag == 'Y' ? (item.share_flag = 'N') : (item.share_flag = 'Y')
        }
      })
      .catch((err) => {
        ElMessage({ message: '接口异常', type: 'error' })
        item.share_flag == 'Y' ? (item.share_flag = 'N') : (item.share_flag = 'Y')
      })
  }
}

//删除提示语
function delPrompt(item) {
  ElMessageBox.confirm('确定要删除？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    pageLoad.value = true
    prompt_del(item.id).then((data) => {
      if (data.code == 200) {
        ElMessage({ message: '删除成功', type: 'success' })
        getPromptList()
      } else {
        ElMessage({ message: data.message, type: 'error' })
      }
    })
  })
}

function to_square() {
  router.push({ name: 'square' })
}
</script>

<style scoped lang="scss">
.page-center {
  flex: 1;
  overflow-y: auto;
}
.container {
  max-width: 1240px;
  margin: 0 auto;
  padding: 0 20px;
  padding-bottom: 20px;
}
//tab标签
.tab_box {
  width: 100%;
  height: 68px;
  display: flex;
  align-items: center;
  .tab_li {
    width: 80px;
    height: 36px;
    box-sizing: border-box;
    border-radius: 4px;
    text-align: center;
    line-height: 34px;
    cursor: pointer;
    font-size: 16px;
    color: #284272;
    box-shadow: 0px 2px 4px 0px rgba(5, 92, 249, 0.1);
    border-radius: 4px;
    border: 1px solid #e0e5ed;
    margin-right: 16px;
    background: #fff;
    &.actived {
      background: #055cf9;
      border-color: #055cf9;
      color: #ffffff;
      font-weight: bold;
    }
  }
}
//中间内容区域
.content_box {
  background: #fff;
  padding: 28px;
  padding-bottom: 8px;
  .term_box {
    margin-top: 20px;
  }
  .prompt_box {
    margin-top: 20px;
  }
  .term_li {
    width: 100%;
    background: #ffffff;
    border-radius: 4px;
    border: 1px solid #b8d3ff;
    overflow: hidden;
    margin-bottom: 20px;
    .title_box {
      height: 40px;
      background: #f1f6ff;
      border-bottom: 1px solid #b8d3ff;
      padding: 0 20px;
      .t {
        flex: 1;
        margin-right: 20px;
        font-weight: bold;
        font-size: 14px;
        color: #055cf9;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .des {
        font-size: 14px;
        color: #111111;
      }
    }
    .btn_box {
      padding: 0 20px;
      height: 50px;
    }
    .table_box {
      height: 364px;
      padding: 0 20px;
    }
    .text_box {
      padding: 0 20px;
      padding-bottom: 22px;
      .text {
        box-sizing: border-box;
        height: 340px;
        border: 1px solid #dcdee2;
        padding: 10px 20px;
        font-size: 14px;
        color: #111111;
        line-height: 28px;
        word-break: break-word;
        overflow-y: auto;
        &.disabled {
          color: #284272;
          background: #b8d3ff;
        }
      }
      // 滚动条样式
      .text::-webkit-scrollbar {
        width: 4px;
      }
      .text::-webkit-scrollbar-thumb {
        border-radius: 10px;
        -webkit-box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.2);
        opacity: 0.2;
        background: fade(#d8d8d8, 60%);
      }
      .text::-webkit-scrollbar-track {
        -webkit-box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.2);
        border-radius: 0;
        background: fade(#d8d8d8, 30%);
      }
    }
  }
}

.no_data {
  text-align: center;
  img {
    margin-top: 50px;
    max-width: 100%;
  }
  .text {
    font-size: 16px;
    color: #8b8c9f;
    margin-top: 30px;
    margin-bottom: 120px;
  }
}

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

  .table_title {
    color: #111111;
  }
  .btn_active {
    background: #eff5ff;
    border-color: #eff5ff;
    color: #055cf9;
  }
  .my_button {
    border-color: #eef3fa;
  }
  tbody {
    outline: none;
  }

  .el-popper {
    max-width: 300px;
  }
}
@media screen and (max-width: 767px) {
  .phone_box {
    flex-direction: column;
    align-items: flex-start;
    .btn_box {
      margin-top: 12px;
    }
  }
  ::v-deep {
    .term_dialog {
      .el-dialog {
        padding: 20px !important;
      }
      .el-dialog__body {
        max-height: 300px;
      }
    }
  }
  .table_box {
    height: auto !important;
    margin-bottom: 20px;
  }
  .no_data {
    .text {
      margin-bottom: 20px;
    }
  }

  /*手机端布局调整*/
  .container {
    padding: 0 16px;
  }
  .content_box {
    padding: 20px 14px;
  }
  .term_box {
    margin-top: 16px;
  }
  .term_li .title_box {
    padding: 0 13px !important;
  }
  .term_li .table_box {
    padding: 0 13px !important;
  }
  .term_li .text_box {
    padding: 0 13px !important;
    padding-bottom: 20px !important;
  }
  .term_li .btn_box {
    padding: 0 13px !important;
  }
  .term_box .el-col:last-child .term_li {
    margin-bottom: 0;
  }
}
</style>
