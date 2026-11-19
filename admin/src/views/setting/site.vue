<script lang="ts" setup>
import { ref, onMounted } from "vue"
import { type FormInstance, ElMessage } from "element-plus"
import { getSiteSettingData, setSiteSettingData } from "@/api/setting"
import { getLegacyPrefix } from "@/utils/siteConfig"

defineOptions({
  // 命名当前组件
  name: "站点设置"
})

type OverrideMode = "auto" | "manual"

const loading = ref(false)
/** 是否「手动指定项目域名（覆盖配置值）」；不勾选就沿用原部署配置。 */
const overrideDomain = ref(false)
const detectedLegacyPrefix = getLegacyPrefix()
const setting = ref({
  version: "",
  domain_mode: "auto" as OverrideMode,
  domain: ""
})

const settingForm = ref<FormInstance | null>(null)

const rules = {
  version: [{ required: true, message: "请选择版本", trigger: "blur" }],
  domain: [
    {
      validator: (_rule: any, value: string, callback: any) => {
        if (overrideDomain.value && setting.value.domain_mode === "manual" && !String(value || "").trim()) {
          callback(new Error("请填写域名或 IP"))
          return
        }
        callback()
      },
      trigger: "blur"
    }
  ]
}

/** 从原有配置前缀里取出 scheme://host[:port]，用于切到手动时预填。 */
function legacyOrigin(): string {
  if (!/^https?:\/\//i.test(detectedLegacyPrefix)) {
    return ""
  }
  try {
    const url = new URL(detectedLegacyPrefix)
    return `${url.protocol}//${url.host}`
  } catch (error) {
    return ""
  }
}

function onModeChange(mode: OverrideMode) {
  if (mode === "manual" && !setting.value.domain) {
    setting.value.domain = legacyOrigin()
  }
}

onMounted(async () => {
  loading.value = true
  await getSiteSettingData().then((data) => {
    const payload = data.data as any
    const stored = payload.domain_mode
    overrideDomain.value = stored === "auto" || stored === "manual"
    setting.value = {
      version: payload.version || "community",
      domain_mode: stored === "manual" ? "manual" : "auto",
      domain: payload.domain || ""
    }
  })
  loading.value = false
})

function onSubmit(settingForm: FormInstance | null) {
  settingForm?.validate((valid, messages) => {
    if (valid) {
      setSiteSettingData({
        version: setting.value.version,
        // 不勾选 = 沿用部署时写入的配置（legacy）；勾选后才写入 auto / manual。
        domain_mode: overrideDomain.value ? setting.value.domain_mode : "legacy",
        domain: setting.value.domain.trim()
      })
        .then((data) => {
          if (data.code == 200) {
            ElMessage.success("保存成功")
          } else {
            ElMessage.error(data.message)
          }
        })
        .catch((e) => {
          ElMessage.error(e?.message || "保存失败")
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
    <el-card shadow="never" v-loading="loading" :element-loading-text="'加载中...'">
      <el-form class="settingForm" ref="settingForm" :model="setting" label-position="top" :rules="rules">
        <el-form-item label="选择版本" required prop="version">
          <el-select v-model="setting.version" placeholder="请选择服务商">
            <el-option value="community" label="个人版" />
            <el-option value="business" label="企业版" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目域名">
          <el-checkbox v-model="overrideDomain">手动指定项目域名（覆盖配置值）</el-checkbox>
        </el-form-item>
        <template v-if="overrideDomain">
          <el-form-item label="指定方式" prop="domain_mode">
            <el-select v-model="setting.domain_mode" @change="onModeChange">
              <el-option value="auto" label="自动（跟随访问地址）" />
              <el-option value="manual" label="手动指定域名 / IP" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="setting.domain_mode === 'manual'" label="域名 / IP" required prop="domain">
            <el-input v-model="setting.domain" placeholder="如 http://192.168.1.10:35555" />
          </el-form-item>
        </template>
        <div v-else class="setting-tip">当前沿用部署配置：{{ detectedLegacyPrefix }}</div>
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

.setting-tip {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.5;
  margin-bottom: 18px;
}
</style>
