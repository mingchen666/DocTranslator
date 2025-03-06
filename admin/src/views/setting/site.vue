<script lang="ts" setup>
import { ref, onMounted } from "vue"
import { type FormInstance, ElMessage } from "element-plus"
import { getSiteSettingData, setSiteSettingData } from "@/api/setting"

defineOptions({
  // 命名当前组件
  name: "接口配置"
})

const setting = ref({
  version: ""
})

const settingForm = ref<FormInstance | null>(null)

const rules = {
  version: [{ required: true, message: "请选择版本", trigger: "blur" }]
}

onMounted(() => {
  getSiteSettingData().then((data) => {
    setting.value = data.data
  })
})

function onSubmit(settingForm: FormInstance | null) {
  console.log(setting.value)
  console.log({
    version: setting.value.version
  })
  settingForm?.validate((valid, messages) => {
    if (valid) {
      setSiteSettingData({
        version: setting.value.version
      })
        .then((data) => {
          if (data.code == 200) {
            ElMessage.success("保存成功")
          } else {
            ElMessage.error(data.message)
          }
        })
        .catch((e) => {
          ElMessage.error(e)
        })
    } else {
      for (const field in messages) {
        messages[field].forEach((message) => {
          ElMessage({
            message: message["message"],
            type: "error"
          })
        })
        break
      }
    }
  })
}
</script>

<template>
  <div class="app-container">
    <el-card shadow="never">
      <el-form class="settingForm" ref="settingForm" :model="setting" label-position="top" :rules="rules">
        <el-form-item label="选择版本" required prop="version">
          <el-select v-model="setting.version" placeholder="请选择服务商">
            <el-option value="community" label="个人版" />
            <el-option value="business" label="企业版" />
          </el-select>
        </el-form-item>
        <el-form-item class="setting-btns">
          <el-button style="width: 88px" type="primary" @click="onSubmit(settingForm)">保存</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style lang="scss" scoped>
.settingForm {
  :deep(.el-form-item__content) {
    max-width: 480px;
    justify-content: left;
  }
}
</style>
