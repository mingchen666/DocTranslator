<template>
  <div class="app-container">
    <el-card v-loading="loading" shadow="never">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="公告内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="4"
            placeholder="请输入公告内容"
          />
        </el-form-item>
        
        <el-form-item label="显示时长(秒)" prop="duration">
          <el-input-number 
            v-model="form.duration" 
            :min="1" 
            :max="60"
            controls-position="right"
          />
        </el-form-item>
        
        <el-form-item label="是否启用" prop="is_active">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSubmit">保存设置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const loading = ref(false)
const formRef = ref(null)

const form = ref({
  content: '',
  duration: 5,
  is_active: false
})

const rules = {
  content: [
    { required: true, message: '请输入公告内容', trigger: 'blur' }
  ],
  duration: [
    { required: true, message: '请设置显示时长', trigger: 'blur' }
  ]
}

// 获取公告设置
const getAnnouncement = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/announcement')
    if (res.code === 200) {
      form.value = res.data
    }
  } catch (error) {
    console.error('获取公告设置失败:', error)
  }
  loading.value = false
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const res = await request.post('/api/announcement', form.value)
        if (res.code === 200) {
          ElMessage.success('保存成功')
        }
      } catch (error) {
        console.error('保存公告设置失败:', error)
        ElMessage.error('保存失败')
      }
      loading.value = false
    }
  })
}

onMounted(() => {
  getAnnouncement()
})
</script>

<style scoped>
.app-container {
  padding: 20px;
}
</style> 