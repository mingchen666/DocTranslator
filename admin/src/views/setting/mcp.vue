<script lang="ts" setup>
import { ref, reactive, onMounted, computed } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import { Plus, CopyDocument, Delete, RefreshRight, Connection, Search } from "@element-plus/icons-vue"
import ResponsiveModal from "@/components/ResponsiveModal/index.vue"
import {
  getAdminMcpKeys,
  createAdminMcpKey,
  getAdminMcpKeyDetail,
  updateAdminMcpKey,
  deleteAdminMcpKey,
  regenerateAdminMcpKey,
  searchCustomers,
  getAdminPromptList
} from "@/api/mcp"

const loading = ref(false)
const keys = ref<any[]>([])
const currentAdminKeys = ref(0)
const maxKeys = ref(3)
const activeTab = ref("user")

const mcpPort = window.__MCP_PORT__ || (window.location.port === "5000" ? "5001" : window.location.port)
const mcpBaseUrl = `${window.location.protocol}//${window.location.hostname}:${mcpPort}`
const adminMcpUrl = computed(() => `${mcpBaseUrl}/mcp/admin`)
const userMcpUrl = computed(() => `${mcpBaseUrl}/mcp/user`)

const fetchKeys = () => {
  loading.value = true
  getAdminMcpKeys()
    .then(({ data }: any) => {
      keys.value = data || []
      currentAdminKeys.value = data.current_admin_keys || 0
      maxKeys.value = data.max_keys || 3
    })
    .finally(() => {
      loading.value = false
    })
}

const userKeys = computed(() => keys.value.filter((k) => k.scope === "user"))
const adminKeys = computed(() => keys.value.filter((k) => k.scope === "admin"))

const typeOptions = [
  {
    value: "trans_text",
    label: "仅文字部分",
    children: [
      {
        value: "trans_text_only",
        label: "仅译文",
        children: [
          { value: "trans_text_only_new", label: "重排版面" },
          { value: "trans_text_only_inherit", label: "继承原版面" }
        ]
      },
      {
        value: "trans_text_both",
        label: "原文+译文",
        children: [
          { value: "trans_text_both_new", label: "重排版面" },
          { value: "trans_text_both_inherit", label: "继承原版面" }
        ]
      }
    ]
  },
  {
    value: "trans_all",
    label: "全部内容",
    children: [
      {
        value: "trans_all_only",
        label: "仅译文",
        children: [
          { value: "trans_all_only_new", label: "重排版面" },
          { value: "trans_all_only_inherit", label: "继承原版面" }
        ]
      },
      {
        value: "trans_all_both",
        label: "原文+译文",
        children: [
          { value: "trans_all_both_new", label: "重排版面" },
          { value: "trans_all_both_inherit", label: "继承原版面" }
        ]
      }
    ]
  }
]

const languageOptions = [
  { label: "中文", value: "中文" },
  { label: "英语", value: "英语" },
  { label: "日语", value: "日语" },
  { label: "韩语", value: "韩语" },
  { label: "法语", value: "法语" },
  { label: "德语", value: "德语" },
  { label: "西班牙语", value: "西班牙语" },
  { label: "俄语", value: "俄语" },
  { label: "葡萄牙语", value: "葡萄牙语" },
  { label: "阿拉伯语", value: "阿拉伯语" }
]

const createVisible = ref(false)
const createLoading = ref(false)
const createForm = reactive({
  name: "",
  scope: "user" as "user" | "admin",
  customer_id: null as number | null,
  config: {
    api_url: "",
    api_key: "",
    model: "",
    type: "trans_all_only_inherit",
    prompt_id: 0,
    backup_model: "",
    threads: 5,
    lang: "中文",
    comparison_id: null as number | null,
    doc2x_flag: "N",
    doc2x_secret_key: ""
  }
})

const customerSearch = ref("")
const customerLoading = ref(false)
const customerList = ref<any[]>([])

const promptList = ref<any[]>([])
const promptLoading = ref(false)
  const default_prompt = ref(`你是一个文档翻译助手，请将以下内容直接翻译成{target_lang}，不返回原文本。如果文本中包含{target_lang}文本、特殊名词（比如邮箱、品牌名、单位名词如mm、px、℃等）、无法翻译等特殊情况，请直接返回原词语而无需解释原因。遇到无法翻译的文本直接返回原内容。保留多余空格。`)

const fetchPromptList = () => {
  promptLoading.value = true
  getAdminPromptList()
    .then(({ data }: any) => {
      promptList.value = [{ id: 0, title: '默认系统提示语', content: default_prompt.value }, ...(data.data || [])]
    })
    .finally(() => {
      promptLoading.value = false
    })
}

const getSelectedPromptContent = (promptId: number) => {
  const p = promptList.value.find(item => item.id === promptId)
  return p ? p.content : ''
}

const searchCustomerList = (keyword: string) => {
  if (!keyword) { customerList.value = []; return }
  customerLoading.value = true
  searchCustomers(keyword)
    .then(({ data }: any) => {
      customerList.value = (data.data?.list || data.data || []).slice(0, 10)
    })
    .finally(() => {
      customerLoading.value = false
    })
}

const resetCreateForm = () => {
  createForm.name = ""
  createForm.scope = "user"
  createForm.customer_id = null
  createForm.config = {
    api_url: "", api_key: "", model: "",
    type: "trans_all_only_inherit", prompt_id: 0, backup_model: "",
    threads: 5, lang: "中文", comparison_id: null,
    doc2x_flag: "N", doc2x_secret_key: ""
  }
  customerSearch.value = ""
  customerList.value = []
}

const openCreateDialog = (scope: "user" | "admin") => {
  resetCreateForm()
  createForm.scope = scope
  createVisible.value = true
}

const handleCreate = () => {
  if (!createForm.name) { ElMessage.warning("请输入密钥名称"); return }
  if (createForm.scope === "user" && !createForm.customer_id) {
    ElMessage.warning("请选择用户"); return
  }
  if (createForm.scope === "admin") {
    if (!createForm.config.api_url || !createForm.config.api_key || !createForm.config.model) {
      ElMessage.warning("管理端密钥必须填写 API 地址、API 密钥和模型"); return
    }
  }
  createLoading.value = true
  createAdminMcpKey({
    name: createForm.name,
    scope: createForm.scope,
    customer_id: createForm.scope === "user" ? createForm.customer_id : undefined,
    config: { ...createForm.config }
  })
    .then((res: any) => {
      if (res.code === 200) {
        createVisible.value = false
        showNewKeyDialog(res.data.key)
        fetchKeys()
      } else {
        ElMessage.error(res.message || "创建失败")
      }
    })
    .finally(() => {
      createLoading.value = false
    })
}

const newKeyVisible = ref(false)
const newKeyValue = ref("")

const showNewKeyDialog = (key: string) => {
  newKeyValue.value = key
  newKeyVisible.value = true
}

const copyText = (text: string) => {
  navigator.clipboard.writeText(text).then(() => ElMessage.success("已复制"))
}

const editVisible = ref(false)
const editLoading = ref(false)
const editKeyPrefix = ref("")
const editForm = reactive({
  name: "",
  scope: "user" as "user" | "admin",
  customer_email: "",
  config: {
    api_url: "", api_key: "", model: "",
    type: "trans_all_only_inherit", prompt_id: 0, backup_model: "",
    threads: 5, lang: "中文", comparison_id: null as number | null,
    doc2x_flag: "N", doc2x_secret_key: ""
  }
})

const openEditDialog = (row: any) => {
  editKeyPrefix.value = row.key_prefix
  getAdminMcpKeyDetail(row.key_prefix).then(({ data }: any) => {
    const d = data
    editForm.name = d.name || ""
    editForm.scope = d.scope || "user"
    editForm.customer_email = d.customer_email || ""
    if (d.config) Object.assign(editForm.config, d.config)
    editVisible.value = true
  })
}

const handleEdit = () => {
  if (!editForm.name) { ElMessage.warning("请输入密钥名称"); return }
  editLoading.value = true
  updateAdminMcpKey(editKeyPrefix.value, {
    name: editForm.name,
    config: { ...editForm.config }
  })
    .then((res: any) => {
      if (res.code === 200) {
        editVisible.value = false
        ElMessage.success("更新成功")
        fetchKeys()
      } else {
        ElMessage.error(res.message || "更新失败")
      }
    })
    .finally(() => {
      editLoading.value = false
    })
}

const handleDelete = (row: any) => {
  ElMessageBox.confirm(
    `确认删除密钥「${row.name || row.key_prefix}」？删除后不可恢复。`,
    "删除确认",
    { confirmButtonText: "确认删除", cancelButtonText: "取消", type: "warning" }
  ).then(() => {
    deleteAdminMcpKey(row.key_prefix).then(() => {
      ElMessage.success("已删除")
      fetchKeys()
    })
  })
}

const handleRegenerate = (row: any) => {
  ElMessageBox.confirm(
    `重新生成密钥「${row.name || row.key_prefix}」？旧密钥将立即失效。`,
    "重新生成确认",
    { confirmButtonText: "确认重新生成", cancelButtonText: "取消", type: "warning" }
  ).then(() => {
    regenerateAdminMcpKey(row.key_prefix).then((res: any) => {
      if (res.data?.key) showNewKeyDialog(res.data.key)
      fetchKeys()
    })
  })
}

const getTypeLabel = (val: string) => {
  const find = (opts: any[]): string => {
    for (const t of opts) {
      if (t.value === val) return t.label
      if (t.children) {
        const child = find(t.children)
        if (child) return t.label + ' / ' + child
      }
    }
    return ''
  }
  return find(typeOptions) || val
}

onMounted(() => {
  fetchKeys()
  fetchPromptList()
})
</script>

<template>
  <div class="app-container">
    <div class="mcp-page" v-loading="loading">
      <div class="mcp-header">
        <div class="mcp-header-left">
          <el-icon :size="22" color="#3b82f6"><Connection /></el-icon>
          <h3 class="mcp-title">MCP 密钥管理</h3>
        </div>
        <div class="mcp-header-right">
          <el-button type="primary" :icon="Plus" @click="openCreateDialog('user')">为用户创建密钥</el-button>
          <el-button type="primary" plain :icon="Plus" @click="openCreateDialog('admin')" :disabled="currentAdminKeys >= maxKeys">
            创建管理端密钥 ({{ currentAdminKeys }}/{{ maxKeys }})
          </el-button>
        </div>
      </div>

      <el-tabs v-model="activeTab" class="mcp-tabs">
        <el-tab-pane label="用户密钥" name="user">
          <div v-if="false" class="tab-info">
            <span>用户端连接地址：</span>
            <el-link type="primary" @click="copyText(userMcpUrl)">{{ userMcpUrl }}</el-link>
            <el-icon style="margin-left:2px;cursor:pointer;" @click="copyText(userMcpUrl)"><CopyDocument /></el-icon>
            <span style="margin-left:16px;">共 {{ userKeys.length }} 个密钥</span>
          </div>
          <div class="key-cards" v-if="userKeys.length">
            <div class="mcp-key-card" v-for="key in userKeys" :key="key.key_prefix">
              <div class="key-meta">
                <div class="key-name">{{ key.name || '未命名' }}</div>
                <div class="key-info">
                  <span class="key-prefix"><code>{{ key.key_prefix }}••••</code></span>
                  <el-tag :type="key.status === 'active' ? 'success' : 'danger'" effect="plain" size="small">
                    {{ key.status === 'active' ? '启用' : '已禁用' }}
                  </el-tag>
                  <span class="key-detail">用户：{{ key.customer_email }}</span>
                  <span class="key-detail" v-if="key.config">模型：{{ key.config.model || '-' }}</span>
                  <span class="key-detail" v-if="key.config">语言：{{ key.config.lang || '-' }}</span>
                  <span class="key-detail" v-if="key.config">类型：{{ getTypeLabel(key.config.type) }}</span>
                </div>
                <div class="key-time">创建：{{ key.created_at }} · 最后使用：{{ key.last_used_at || '从未' }}</div>
              </div>
              <div class="key-actions">
                <el-button type="primary" text size="small" @click="openEditDialog(key)">编辑</el-button>
                <el-button type="warning" text size="small" @click="handleRegenerate(key)">重新生成</el-button>
                <el-button type="danger" text size="small" @click="handleDelete(key)">删除</el-button>
              </div>
            </div>
          </div>
          <div class="no-keys" v-else>
            <div class="empty-visual">🔑</div>
            <p class="empty-title">暂无用户端密钥</p>
            <p class="empty-desc">点击上方「为用户创建密钥」为用户分配 MCP 访问权限</p>
          </div>
        </el-tab-pane>

        <el-tab-pane label="管理端密钥" name="admin">
          <div v-if="false" class="tab-info">
            <span>管理端连接地址：</span>
            <el-link type="primary" @click="copyText(adminMcpUrl)">{{ adminMcpUrl }}</el-link>
            <el-icon style="margin-left:2px;cursor:pointer;" @click="copyText(adminMcpUrl)"><CopyDocument /></el-icon>
            <span style="margin-left:16px;">已创建 {{ currentAdminKeys }} / {{ maxKeys }}</span>
          </div>
          <div class="key-cards" v-if="adminKeys.length">
            <div class="mcp-key-card" v-for="key in adminKeys" :key="key.key_prefix">
              <div class="key-meta">
                <div class="key-name">{{ key.name || '未命名' }}</div>
                <div class="key-info">
                  <span class="key-prefix"><code>{{ key.key_prefix }}••••</code></span>
                  <el-tag :type="key.status === 'active' ? 'success' : 'danger'" effect="plain" size="small">
                    {{ key.status === 'active' ? '启用' : '已禁用' }}
                  </el-tag>
                  <span class="key-detail" v-if="key.config">模型：{{ key.config.model || '-' }}</span>
                  <span class="key-detail" v-if="key.config">语言：{{ key.config.lang || '-' }}</span>
                  <span class="key-detail" v-if="key.config">类型：{{ getTypeLabel(key.config.type) }}</span>
                </div>
                <div class="key-time">创建：{{ key.created_at }} · 最后使用：{{ key.last_used_at || '从未' }}</div>
              </div>
              <div class="key-actions">
                <el-button type="primary" text size="small" @click="openEditDialog(key)">编辑</el-button>
                <el-button type="warning" text size="small" @click="handleRegenerate(key)">重新生成</el-button>
                <el-button type="danger" text size="small" @click="handleDelete(key)">删除</el-button>
              </div>
            </div>
          </div>
          <div class="no-keys" v-else>
            <div class="empty-visual">🔐</div>
            <p class="empty-title">暂无管理端密钥</p>
            <p class="empty-desc">管理端密钥可访问系统管理工具（统计、客户管理、翻译监控等）</p>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 创建密钥弹窗 -->
    <ResponsiveModal v-model="createVisible" :title="createForm.scope === 'admin' ? '创建管理端密钥' : '为用户创建密钥'" width="560px" :close-on-click-overlay="false">
      <el-form :model="createForm" label-position="top" class="mcp-form">
        <el-form-item label="密钥名称">
          <el-input v-model="createForm.name" placeholder="如：生产环境密钥" />
        </el-form-item>

        <el-form-item v-if="createForm.scope === 'user'" label="选择用户" required>
          <el-select
            v-model="createForm.customer_id"
            placeholder="搜索用户邮箱或姓名"
            filterable
            remote
            :remote-method="searchCustomerList"
            :loading="customerLoading"
            style="width: 100%"
          >
            <el-option
              v-for="c in customerList"
              :key="c.id"
              :value="c.id"
              :label="`${c.email} (${c.name || c.id})`"
            />
          </el-select>
        </el-form-item>

        <div class="form-section-title">
          <span class="section-label required-label">翻译配置</span>
        </div>

        <el-form-item label="API 地址" :required="createForm.scope === 'admin'">
          <el-input v-model="createForm.config.api_url" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="API 密钥" :required="createForm.scope === 'admin'">
          <el-input v-model="createForm.config.api_key" placeholder="sk-xxxx" show-password />
        </el-form-item>
        <el-form-item label="模型名称" :required="createForm.scope === 'admin'">
          <el-input v-model="createForm.config.model" placeholder="gpt-4o" />
        </el-form-item>
        <el-form-item label="译文形式">
          <el-cascader v-model="createForm.config.type" :options="typeOptions" :props="{ expandTrigger: 'hover', emitPath: false }" placeholder="选择译文形式" style="width: 100%" clearable />
        </el-form-item>
        <el-form-item label="目标语言">
          <el-select v-model="createForm.config.lang" placeholder="请选择目标语言" style="width: 100%">
            <el-option v-for="lang in languageOptions" :key="lang.value" :label="lang.label" :value="lang.value" />
          </el-select>
        </el-form-item>

        <div class="form-section-title">
          <span class="section-label optional-label">可选配置</span>
        </div>

        <el-form-item label="备用模型">
          <el-input v-model="createForm.config.backup_model" placeholder="备用模型在主模型不可用时自动切换" />
        </el-form-item>
        <el-form-item label="并发线程数">
          <el-input-number v-model="createForm.config.threads" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="术语库 ID">
          <el-input-number v-model="createForm.config.comparison_id" :min="0" />
        </el-form-item>
        <el-form-item label="提示词模板">
          <el-select
            v-model="createForm.config.prompt_id"
            placeholder="请选择提示词模板"
            :loading="promptLoading"
            style="width: 100%"
          >
            <el-option
              v-for="p in promptList"
              :key="p.id"
              :label="`${p.title}${p.content ? ' - ' + (p.content.length > 30 ? p.content.substring(0, 30) + '...' : p.content) : ''}`"
              :value="p.id"
            />
          </el-select>
          <div v-if="createForm.config.prompt_id !== 0 && getSelectedPromptContent(createForm.config.prompt_id)" class="prompt-preview">
            <div class="prompt-preview-label">提示词内容：</div>
            <div class="prompt-preview-content">{{ getSelectedPromptContent(createForm.config.prompt_id) }}</div>
          </div>
          <!-- <div v-else-if="createForm.config.prompt_id === 0" class="prompt-preview">
            <div class="prompt-preview-label">提示词内容：</div>
            <div class="prompt-preview-content" style="color: #94a3b8;">使用系统内置默认提示词</div>
          </div> -->
        </el-form-item>
        <el-form-item label="Doc2X">
          <el-radio-group v-model="createForm.config.doc2x_flag">
            <el-radio-button value="N">禁用</el-radio-button>
            <el-radio-button value="Y">启用</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="createForm.config.doc2x_flag === 'Y'" label="Doc2X 密钥">
          <el-input v-model="createForm.config.doc2x_secret_key" placeholder="输入 Doc2X API Key" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="createLoading">创建密钥</el-button>
      </template>
    </ResponsiveModal>

    <!-- 编辑密钥弹窗 -->
    <ResponsiveModal v-model="editVisible" title="编辑密钥" width="560px" :close-on-click-overlay="false">
      <el-form :model="editForm" label-position="top" class="mcp-form">
        <el-form-item label="密钥名称">
          <el-input v-model="editForm.name" placeholder="密钥名称" />
        </el-form-item>
        <el-form-item v-if="editForm.customer_email && editForm.scope === 'user'" label="所属用户">
          <el-input :model-value="editForm.customer_email" disabled />
        </el-form-item>

        <div class="form-section-title">
          <span class="section-label required-label">翻译配置</span>
        </div>

        <el-form-item label="API 地址">
          <el-input v-model="editForm.config.api_url" placeholder="https://api.ezworkapi.top/v1" />
        </el-form-item>
        <el-form-item label="API 密钥">
          <el-input v-model="editForm.config.api_key" placeholder="sk-xxxx" show-password />
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="editForm.config.model" placeholder="gpt-4o" />
        </el-form-item>
        <el-form-item label="译文形式">
          <el-cascader v-model="editForm.config.type" :options="typeOptions" :props="{ expandTrigger: 'hover', emitPath: false }" placeholder="选择译文形式" style="width: 100%" clearable />
        </el-form-item>
        <el-form-item label="目标语言">
          <el-select v-model="editForm.config.lang" placeholder="请选择目标语言" style="width: 100%">
            <el-option v-for="lang in languageOptions" :key="lang.value" :label="lang.label" :value="lang.value" />
          </el-select>
        </el-form-item>

        <div class="form-section-title">
          <span class="section-label optional-label">可选配置</span>
        </div>

        <el-form-item label="备用模型">
          <el-input v-model="editForm.config.backup_model" placeholder="备用模型" />
        </el-form-item>
        <el-form-item label="并发线程数">
          <el-input-number v-model="editForm.config.threads" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="术语库 ID">
          <el-input-number v-model="editForm.config.comparison_id" :min="0" />
        </el-form-item>
        <el-form-item label="提示词模板">
          <el-select
            v-model="editForm.config.prompt_id"
            placeholder="请选择提示词模板"
            :loading="promptLoading"
            style="width: 100%"
          >
            <el-option
              v-for="p in promptList"
              :key="p.id"
              :label="`${p.title}${p.content ? ' - ' + (p.content.length > 30 ? p.content.substring(0, 30) + '...' : p.content) : ''}`"
              :value="p.id"
            />
          </el-select>
          <div v-if="editForm.config.prompt_id>=0 && getSelectedPromptContent(editForm.config.prompt_id)" class="prompt-preview">
            <div class="prompt-preview-label">提示词内容：</div>
            <div class="prompt-preview-content">{{ getSelectedPromptContent(editForm.config.prompt_id) }}</div>
          </div>
          <div v-else class="prompt-preview">
            <div class="prompt-preview-label">提示词内容：</div>
            <div class="prompt-preview-content" style="color: #94a3b8;">使用系统内置默认提示词</div>
          </div>
        </el-form-item>
        <el-form-item label="Doc2X">
          <el-radio-group v-model="editForm.config.doc2x_flag">
            <el-radio-button value="N">禁用</el-radio-button>
            <el-radio-button value="Y">启用</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="editForm.config.doc2x_flag === 'Y'" label="Doc2X 密钥">
          <el-input v-model="editForm.config.doc2x_secret_key" placeholder="输入 Doc2X API Key" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEdit" :loading="editLoading">保存</el-button>
      </template>
    </ResponsiveModal>

    <!-- 新密钥展示弹窗 -->
    <ResponsiveModal v-model="newKeyVisible" title="密钥已创建" width="460px" :close-on-click-overlay="false" :show-close="false">
      <div class="new-key-display">
        <div class="new-key-icon">🎉</div>
        <p class="new-key-title">密钥创建成功</p>
        <div class="new-key-warning">⚠️ 此密钥仅显示一次，关闭后无法再次查看</div>
        <div class="key-display-box">
          <span class="key-value">{{ newKeyValue }}</span>
          <el-button type="primary" text :icon="CopyDocument" @click="copyText(newKeyValue)" class="copy-key-btn">复制</el-button>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="newKeyVisible = false" class="confirm-saved-btn">我已安全保存</el-button>
      </template>
    </ResponsiveModal>
  </div>
</template>

<style scoped>
.mcp-page {
  /* max-width: 960px; */
  margin: 0 auto;
}

.mcp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;

  .mcp-header-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .mcp-title {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #1e293b;
  }

  .mcp-header-right {
    display: flex;
    gap: 8px;
  }
}

.mcp-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 16px;
  }
}

.tab-info {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 16px;
  padding: 10px 14px;
  background: #f8fafc;
  border-radius: 8px;
  font-size: 13px;
  color: #64748b;
}

.key-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mcp-key-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  }

  .key-meta {
    display: flex;
    flex-direction: column;
    gap: 6px;
    flex: 1;
    min-width: 0;
  }

  .key-name {
    font-size: 15px;
    font-weight: 600;
    color: #1e293b;
  }

  .key-info {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;

    .key-prefix code {
      font-family: 'SF Mono', 'Fira Code', monospace;
      font-size: 12px;
      color: #475569;
      background: #f1f5f9;
      padding: 2px 8px;
      border-radius: 4px;
    }

    .key-detail {
      font-size: 12px;
      color: #64748b;
    }
  }

  .key-time {
    font-size: 12px;
    color: #94a3b8;
  }

  .key-actions {
    display: flex;
    gap: 4px;
    flex-shrink: 0;
  }
}

.no-keys {
  text-align: center;
  padding: 48px 20px;
  background: #f8fafc;
  border-radius: 12px;
  border: 2px dashed #e2e8f0;

  .empty-visual {
    font-size: 40px;
    margin-bottom: 16px;
  }

  .empty-title {
    font-size: 16px;
    font-weight: 500;
    color: #475569;
    margin: 0 0 6px;
  }

  .empty-desc {
    font-size: 13px;
    color: #94a3b8;
    margin: 0;
  }
}

.form-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  margin: 16px 0 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid #f1f5f9;

  .section-label {
    display: flex;
    align-items: center;
    gap: 6px;

    &::before {
      content: '';
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }

    &.required-label::before {
      background: #3b82f6;
    }

    &.optional-label::before {
      background: #94a3b8;
    }
  }
}

.mcp-form {
  .el-form-item {
    margin-bottom: 14px;
  }
}

.prompt-preview {
  margin-top: 8px;
  padding: 10px 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  max-height: 120px;
  overflow-y: auto;

  .prompt-preview-label {
    font-size: 12px;
    color: #94a3b8;
    margin-bottom: 6px;
  }

  .prompt-preview-content {
    font-size: 13px;
    color: #475569;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-all;
  }
}

.new-key-display {
  text-align: center;
  padding: 4px 0;

  .new-key-icon {
    font-size: 48px;
    margin-bottom: 12px;
  }

  .new-key-title {
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
    margin: 0 0 16px;
  }

  .new-key-warning {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #fdf6ec;
    border: 1px solid #faecd8;
    color: #e6a23c;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    margin-bottom: 20px;
  }

  .key-display-box {
    display: flex;
    align-items: center;
    gap: 10px;
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 16px;

    .key-value {
      flex: 1;
      font-family: 'SF Mono', 'Fira Code', monospace;
      font-size: 13px;
      color: #334155;
      word-break: break-all;
      text-align: left;
      line-height: 1.5;
    }

    .copy-key-btn {
      flex-shrink: 0;
    }
  }
}

.confirm-saved-btn {
  width: 100%;
  height: 40px;
  border-radius: 8px;
  font-weight: 500;
}

@media screen and (max-width: 768px) {
  .mcp-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;

    .mcp-header-right {
      width: 100%;
      flex-direction: column;
    }
  }

  .mcp-key-card {
    flex-direction: column;
    gap: 12px;
    padding: 14px;

    .key-info {
      flex-direction: column;
      align-items: flex-start;
      gap: 6px;
    }

    .key-actions {
      width: 100%;
      justify-content: flex-end;
    }
  }
}
</style>
