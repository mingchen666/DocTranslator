<template>
  <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" label-position="top">
    <!-- 术语库选择 -->
    <el-form-item label="默认术语库(AI翻译):" prop="comparison_id">
      <el-select
        v-model="form.comparison_id"
        placeholder="选择术语库"
        clearable
        filterable
        style="width: 100%"
        @focus="fetchTermList"
      >
        <el-option v-for="term in termList" :key="term.id" :label="term.title" :value="term.id" />
      </el-select>
    </el-form-item>

    <!-- 线程数 -->
    <el-form-item label="线程数:" prop="threads">
      <el-input-number v-model="form.threads" :min="1" :max="20" :step="1" />
    </el-form-item>
    <el-alert type="warning" description="启用后，所有pdf将使用doc2x进行处理。doc2x目前是进行pdf解析,将pdf转换成word、md等文件" show-icon :closable="false" />

    <!-- <Alert
      title="操作提示"
      type="success"
      description="文件已成功上传"
      closable
      @close="handleClose"
    >

      <p class="text-xs mt-1">文件大小: 2.4MB</p>
    </Alert> -->

    <!-- Doc2x启用开关 -->
    <el-form-item label="是否使用Doc2x翻译PDF文件:">
      <el-radio-group v-model="form.doc2x_flag" @change="handleDoc2xToggle">
        <el-radio label="N">禁用</el-radio>
        <el-radio label="Y">启用</el-radio>
      </el-radio-group>
    </el-form-item>

    <!-- Doc2x密钥输入 -->
    <el-form-item v-if="form.doc2x_flag === 'Y'" label="Doc2x密钥" prop="doc2x_secret_key">
      <el-input
        v-model="form.doc2x_secret_key"
        placeholder="输入Doc2x API Key"
        clearable
        style="width: 300px; margin-right: 10px"
      />
      <el-button type="primary" plain disabled :loading="testingDoc2x" @click="testDoc2xConnection">
        测试连接
      </el-button>
    </el-form-item>

    <!-- 操作按钮 -->
    <el-form-item>
      <el-button type="primary" @click="submitForm">保存设置</el-button>
      <el-button @click="resetForm">重置</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
// import Alert from '../../../components/alert.vue'
import { comparison_my } from '@/api/corpus'
import { checkDocx } from '@/api/trans'
import { useTranslateStore } from '@/store/translate'
const translateStore = useTranslateStore()

const formRef = ref(null)
const termList = ref([])
const testingDoc2x = ref(false)

// 表单数据
const form = ref({
  // comparison_id: props.settings.comparison_id,
  // type: props.settings.type,
  // threads: props.settings.threads,
  // doc2x_flag: props.settings.doc2x_flag,
  // doc2x_secret_key: props.settings.doc2x_secret_key
})
onMounted(() => {
  form.value = {
    comparison_id: translateStore.aiServer.comparison_id,
    type: translateStore.common.type,
    threads: translateStore.common.threads,
    doc2x_flag: translateStore.common.doc2x_flag,
    doc2x_secret_key: translateStore.common.doc2x_secret_key
  }
})
// 动态验证规则
const rules = reactive({
  comparison_id: [{ required: false }],
  type: [{ required: true, message: '请选择译文形式', trigger: 'change' }],
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
      message: '线程数必须在1-20之间',
      trigger: 'blur'
    }
  ],
  doc2x_secret_key: [
    {
      required: form.doc2x_flag === 'Y',
      message: '请输入Doc2x API Key',
      trigger: 'blur'
    }
  ]
})

// 获取术语列表
const fetchTermList = async () => {
  try {
    const res = await comparison_my()
    if (res.code === 200) {
      termList.value = res.data.data
    }
  } catch (error) {
    console.error('获取术语列表失败:', error)
    ElMessage.error('获取术语列表失败')
  }
}

// 处理Doc2x开关切换
const handleDoc2xToggle = (value) => {
  // 当禁用时清空密钥
  if (value === 'N') {
    form.doc2x_secret_key = ''
  }
  // 动态更新验证规则
  rules.doc2x_secret_key[0].required = value === 'Y'
}

// 测试Doc2x连接
const testDoc2xConnection = async () => {
  if (!form.doc2x_secret_key) {
    ElMessage.warning('请先输入Doc2x API Key')
    return
  }

  try {
    testingDoc2x.value = true
    const res = await checkDocx({
      doc2x_secret_key: form.doc2x_secret_key
    })

    if (res.code === 0) {
      ElMessage.success('Doc2x连接测试成功')
    } else {
      ElMessage.error(res.message || 'Doc2x连接测试失败')
    }
  } catch (error) {
    console.error('Doc2x连接测试异常:', error)
    ElMessage.error('连接测试异常，请检查网络或服务状态')
  } finally {
    testingDoc2x.value = false
  }
}

// 提交表单
const submitForm = async () => {
  try {
    await formRef.value.validate()
    // 准备提交数据
    const submitData = {
      threads: form.value.threads,
      doc2x_flag: form.value.doc2x_flag,
      doc2x_secret_key: form.value.doc2x_secret_key //form.value.doc2x_flag === 'Y' ? form.value.doc2x_secret_key : ''
    }
    translateStore.updateCommonSettings(submitData)
    // 更新术语库id选择
    translateStore.updateAIServerSettings({ comparison_id: form.value.comparison_id })
    ElMessage.success('保存成功!')
  } catch (error) {
    console.error('表单验证失败:', error)
    ElMessage.error('请检查表单填写是否正确')
  }
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(form, props.settings)
}

// 初始化术语列表
onMounted(() => {
  fetchTermList()
})
</script>

<style scoped>
.el-form-item {
  margin-bottom: 22px;
}
</style>
