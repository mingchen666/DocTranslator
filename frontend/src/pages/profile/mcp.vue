<template>
  <div class="mcp-config">
    <div class="mcp-header">
      <div class="header-content">
        <div>
          <h3>MCP 密钥管理</h3>
          <p class="mcp-desc">创建 MCP 密钥以通过 Claude Desktop、Cursor 等 AI 工具调用翻译服务。每个密钥绑定你的翻译配置，调用时自动注入。</p>
        </div>
      </div>
      <el-button v-if="keyList.length < maxKeys" type="primary" @click="showCreateDialog" class="create-btn">
        <el-icon><Plus /></el-icon>
        创建新密钥
      </el-button>
      <el-tag v-else type="info" effect="plain" class="limit-tag">已达上限 ({{ maxKeys }})</el-tag>
    </div>

    <div class="mcp-keys">
      <div v-for="key in keyList" :key="key.key_prefix" class="mcp-key-card">
        <div class="key-top">
          <div class="key-identity">
            <div class="key-name-row">
              <span class="key-name">{{ key.name || '未命名密钥' }}</span>
              <span class="key-status-dot" :class="key.status === 'active' ? 'active' : 'inactive'"></span>
              <el-tag :type="key.status === 'active' ? 'success' : 'danger'" size="small" round effect="light">
                {{ key.status === 'active' ? '启用中' : '已停用' }}
              </el-tag>
            </div>
            <div class="key-meta">
              <span class="key-prefix">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                {{ key.key_prefix }}••••••••
              </span>
              <span class="key-time">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                创建于 {{ key.created_at }}
              </span>
              <span v-if="key.last_used_at" class="key-time">
                最后使用 {{ key.last_used_at }}
              </span>
            </div>
          </div>
        </div>
        <div class="key-actions">
          <el-button size="small" @click="showDetail(key)" class="action-btn">
            <el-icon><Setting /></el-icon><span class="action-text">配置</span>
          </el-button>
          <el-button size="small" type="warning" plain @click="handleRegenerate(key)" class="action-btn">
            <el-icon><RefreshRight /></el-icon><span class="action-text">重置</span>
          </el-button>
          <el-button size="small" :type="key.status === 'active' ? 'default' : 'success'" @click="handleToggleStatus(key)" class="action-btn">
            <el-icon><component :is="key.status === 'active' ? 'SwitchButton' : 'CircleCheck'" /></el-icon><span class="action-text">{{ key.status === 'active' ? '停用' : '启用' }}</span>
          </el-button>
          <el-button size="small" type="danger" plain @click="handleDelete(key)" class="action-btn">
            <el-icon><Delete /></el-icon><span class="action-text">删除</span>
          </el-button>
        </div>
      </div>

      <div v-if="keyList.length === 0" class="no-keys">
        <div class="empty-visual">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#c0c4cc" stroke-width="1.5">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
        </div>
        <p class="empty-title">暂无 MCP 密钥</p>
        <p class="empty-desc">创建一个密钥，即可在 Claude Desktop、Cursor、Dify等 AI 工具中使用翻译服务</p>
        <el-button type="primary" @click="showCreateDialog" style="margin-top: 16px;">
          <el-icon><Plus /></el-icon>创建第一个密钥
        </el-button>
      </div>
    </div>

    <div class="mcp-usage">
      <h4>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        使用方式
      </h4>
      <div class="usage-blocks">
        <div class="usage-block">
          <div class="usage-block-header">
            <span class="usage-badge remote">远程</span>
            <h5>Streamable HTTP</h5>
          </div>
          <p>在 Claude Desktop 配置文件中添加：</p>
          <div class="code-block-wrapper">
            <pre class="code-block">{
  "mcpServers": {
    "doctranslator": {
      "url": "{{ mcpUrl }}/mcp/user",
      "headers": {
        "Authorization": "Bearer {{ currentKey || '你的密钥' }}"
      }
    }
  }
}</pre>
            <el-button class="copy-code-btn" size="small" text @click="copyCode('remote')">
              <el-icon><CopyDocument /></el-icon>
            </el-button>
          </div>
        </div>
        <div class="usage-block">
          <div class="usage-block-header">
            <span class="usage-badge local">本地</span>
            <h5>stdio</h5>
          </div>
          <p>下载 mcp_local_server.py 并在 Claude Desktop 配置文件中添加：</p>
          <div class="code-block-wrapper">
            <pre class="code-block">{
  "mcpServers": {
    "doctranslator-local": {
      "command": "python",
      "args": ["mcp_local_server.py"],
      "env": {
        "DOCTRANSLATOR_URL": "{{ serverUrl }}",
        "DOCTRANSLATOR_API_KEY": "{{ currentKey || '你的密钥' }}",
        "API_URL": "你的API地址",
        "API_KEY": "你的API密钥",
        "MODEL": "gpt-4o",
        "TYPE": "trans_all_only_inherit",
        "THREADS": "5",
        "LANG": "中文"
      }
    }
  }
}</pre>
            <el-button class="copy-code-btn" size="small" text @click="copyCode('local')">
              <el-icon><CopyDocument /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <ResponsiveModal v-model="createVisible" title="创建 MCP 密钥" width="560px" :close-on-click-overlay="false">
      <el-form :model="createForm" label-position="top" class="mcp-form">
        <el-form-item label="密钥名称">
          <el-input v-model="createForm.name" placeholder="如：我的 Claude Desktop" />
        </el-form-item>

        <div class="form-section-title">
          <span class="section-label required-label">翻译配置</span>
        </div>

        <el-form-item label="API 地址" required>
          <el-input v-model="createForm.config.api_url" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="API 密钥" required>
          <el-input v-model="createForm.config.api_key" placeholder="sk-xxxx" show-password />
        </el-form-item>
        <el-form-item label="模型名称" required>
          <el-input v-model="createForm.config.model" placeholder="gpt-4o" />
        </el-form-item>
        <el-form-item label="译文形式" required>
          <el-cascader
            v-model="createForm.config.type"
            :options="typeOptions"
            placeholder="选择译文形式"
            style="width: 100%"
            :props="{ expandTrigger: 'hover' }"
            clearable
          />
        </el-form-item>
        <el-form-item label="目标语言" required>
          <el-select v-model="createForm.config.lang" placeholder="请选择目标语言" style="width: 100%">
            <el-option
              v-for="lang in languageOptions"
              :key="lang.value"
              :label="lang.label"
              :value="lang.value"
            />
          </el-select>
        </el-form-item>

        <div class="form-section-title">
          <span class="section-label optional-label">可选配置</span>
        </div>

        <el-form-item label="选择提示语">
          <el-select
            v-model="createForm.config.prompt_id"
            placeholder="请选择提示语"
            filterable
            clearable
            @change="handleCreatePromptChange"
            @focus="loadPrompts"
            :loading="promptLoading"
            style="width: 100%"
          >
            <el-option
              v-for="item in promptData"
              :key="item.id"
              :value="item.id"
              :label="item.title"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="createPromptContent" label="提示语内容">
          <el-input
            v-model="createPromptContent"
            type="textarea"
            :rows="4"
            resize="none"
            readonly
            class="prompt-preview"
          />
        </el-form-item>
        <el-form-item label="术语库">
          <el-select
            v-model="createForm.config.comparison_id"
            placeholder="请选择术语库"
            clearable
            filterable
            @focus="loadComparisons"
            style="width: 100%"
          >
            <el-option
              v-for="term in comparisonData"
              :key="term.id"
              :label="term.title"
              :value="term.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备用模型">
          <el-input v-model="createForm.config.backup_model" placeholder="备用模型在主模型不可用时自动切换" />
        </el-form-item>
        <el-form-item label="并发线程数">
          <el-input-number v-model="createForm.config.threads" :min="1" :max="20" />
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

    <ResponsiveModal v-model="detailVisible" title="密钥配置" width="560px" :close-on-click-overlay="false">
      <el-form v-if="detailData" :model="detailForm" label-position="top" class="mcp-form">
        <el-form-item label="密钥名称">
          <el-input v-model="detailForm.name" />
        </el-form-item>

        <div class="form-section-title">
          <span class="section-label required-label">翻译配置</span>
        </div>

        <el-form-item label="API 地址" required>
          <el-input v-model="detailForm.config.api_url" />
        </el-form-item>
        <el-form-item label="API 密钥" required>
          <el-input v-model="detailForm.config.api_key" show-password />
        </el-form-item>
        <el-form-item label="模型名称" required>
          <el-input v-model="detailForm.config.model" />
        </el-form-item>
        <el-form-item label="译文形式" required>
          <el-cascader
            v-model="detailForm.config.type"
            :options="typeOptions"
            placeholder="选择译文形式"
            style="width: 100%"
            :props="{ expandTrigger: 'hover' }"
            clearable
          />
        </el-form-item>
        <el-form-item label="目标语言" required>
          <el-select v-model="detailForm.config.lang" placeholder="请选择目标语言" style="width: 100%">
            <el-option
              v-for="lang in languageOptions"
              :key="lang.value"
              :label="lang.label"
              :value="lang.value"
            />
          </el-select>
        </el-form-item>

        <div class="form-section-title">
          <span class="section-label optional-label">可选配置</span>
        </div>

        <el-form-item label="选择提示语">
          <el-select
            v-model="detailForm.config.prompt_id"
            placeholder="请选择提示语"
            filterable
            clearable
            @change="handleDetailPromptChange"
            @focus="loadPrompts"
            :loading="promptLoading"
            style="width: 100%"
          >
            <el-option
              v-for="item in promptData"
              :key="item.id"
              :value="item.id"
              :label="item.title"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="detailPromptContent" label="提示语内容">
          <el-input
            v-model="detailPromptContent"
            type="textarea"
            :rows="4"
            resize="none"
            readonly
            class="prompt-preview"
          />
        </el-form-item>
        <el-form-item label="术语库">
          <el-select
            v-model="detailForm.config.comparison_id"
            placeholder="请选择术语库"
            clearable
            filterable
            @focus="loadComparisons"
            style="width: 100%"
          >
            <el-option
              v-for="term in comparisonData"
              :key="term.id"
              :label="term.title"
              :value="term.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备用模型">
          <el-input v-model="detailForm.config.backup_model" />
        </el-form-item>
        <el-form-item label="并发线程数">
          <el-input-number v-model="detailForm.config.threads" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="Doc2X">
          <el-radio-group v-model="detailForm.config.doc2x_flag">
            <el-radio-button value="N">禁用</el-radio-button>
            <el-radio-button value="Y">启用</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="detailForm.config.doc2x_flag === 'Y'" label="Doc2X 密钥">
          <el-input v-model="detailForm.config.doc2x_secret_key" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="detailVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdate" :loading="updateLoading">保存配置</el-button>
      </template>
    </ResponsiveModal>

    <ResponsiveModal v-model="newKeyVisible" title="密钥创建成功" width="480px" :close-on-click-overlay="false" :show-close="true">
      <div class="new-key-display">
        <div class="new-key-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#67c23a" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        </div>
        <h3 class="new-key-title">密钥创建成功</h3>
        <div class="new-key-warning">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#e6a23c" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <span>请立即保存密钥，关闭后将无法再次查看完整密钥</span>
        </div>
        <div class="key-display-box">
          <code class="key-value">{{ newKeyData.key }}</code>
          <el-button type="primary" size="small" @click="copyKey(newKeyData.key)" class="copy-key-btn">
            <el-icon><CopyDocument /></el-icon>复制
          </el-button>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="newKeyVisible = false" class="confirm-saved-btn">我已安全保存密钥</el-button>
      </template>
    </ResponsiveModal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Setting, RefreshRight, Delete, CopyDocument, SwitchButton, CircleCheck } from '@element-plus/icons-vue'
import ResponsiveModal from '@/components/ResponsiveModal.vue'
import { getMcpKeys, createMcpKey, updateMcpKey, deleteMcpKey, regenerateMcpKey, getMcpKeyDetail } from '@/api/mcp'
import { prompt_my, comparison_my } from '@/api/corpus'
import { useSettingsStore } from '@/store/settings'

const settingsStore = useSettingsStore()
const serverUrl = window.location.origin
const mcpPort = window.__MCP_PORT__ || (window.location.port === '5000' ? '5002' : window.location.port)
const mcpUrl = window.__MCP_URL__ || `${window.location.protocol}//${window.location.hostname}:${mcpPort}`
const keyList = ref([])
const maxKeys = ref(5)

const promptData = ref([])
const promptLoading = ref(false)
const comparisonData = ref([])

const createPromptContent = ref('')
const detailPromptContent = ref('')

const languageOptions = [
  { value: '中文', label: '中文' },
  { value: '英语', label: '英语' },
  { value: '日语', label: '日语' },
  { value: '韩语', label: '韩语' },
  { value: '法语', label: '法语' },
  { value: '德语', label: '德语' },
  { value: '西班牙语', label: '西班牙语' },
  { value: '俄语', label: '俄语' },
  { value: '阿拉伯语', label: '阿拉伯语' },
]

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

const getDefaultConfig = () => ({
  api_url: '',
  api_key: '',
  model: '',
  type: ['trans_all', 'trans_all_only', 'trans_all_only_inherit'],
  prompt_id: 0,
  backup_model: '',
  threads: 5,
  lang: '中文',
  comparison_id: null,
  doc2x_flag: 'N',
  doc2x_secret_key: '',
})

const createVisible = ref(false)
const createLoading = ref(false)
const createForm = ref({
  name: '',
  config: getDefaultConfig()
})

const detailVisible = ref(false)
const updateLoading = ref(false)
const detailData = ref(null)
const detailForm = ref({ name: '', config: {} })

const newKeyVisible = ref(false)
const newKeyData = ref({})

const currentKey = computed(() => keyList.value.length > 0 ? keyList.value[0].key_prefix + '...' : '')

const fetchKeys = async () => {
  try {
    const res = await getMcpKeys()
    if (res && res.code === 200) {
      keyList.value = res.data || []
      maxKeys.value = res.max_keys || 5
    }
  } catch (e) {
    console.error('获取MCP密钥失败', e)
  }
}

const loadPrompts = async () => {
  if (promptData.value.length > 0) return
  promptLoading.value = true
  try {
    const res = await prompt_my()
    if (res.code === 200) {
      const defaultPrompt = {
        id: 0,
        title: '默认系统提示语',
        content: settingsStore.system_settings.prompt_template || ''
      }
      const prompts = Array.isArray(res.data?.data) ? res.data.data : []
      promptData.value = [defaultPrompt, ...prompts]
    }
  } catch (e) {
    console.error('获取提示语失败', e)
  } finally {
    promptLoading.value = false
  }
}

const loadComparisons = async () => {
  if (comparisonData.value.length > 0) return
  try {
    const res = await comparison_my()
    if (res.code === 200) {
      comparisonData.value = res.data?.data || []
    }
  } catch (e) {
    console.error('获取术语库失败', e)
  }
}

const handleCreatePromptChange = (id) => {
  const selected = promptData.value.find(item => String(item.id) === String(id))
  createPromptContent.value = selected ? selected.content : ''
}

const handleDetailPromptChange = (id) => {
  const selected = promptData.value.find(item => String(item.id) === String(id))
  detailPromptContent.value = selected ? selected.content : ''
}

const flattenTypeToValue = (typeVal) => {
  if (Array.isArray(typeVal)) {
    return typeVal[typeVal.length - 1] || 'trans_all_only_inherit'
  }
  return typeVal || 'trans_all_only_inherit'
}

const expandTypeToArray = (typeVal) => {
  if (Array.isArray(typeVal)) return typeVal
  const flat = typeVal || 'trans_all_only_inherit'
  for (const g of typeOptions) {
    for (const m of g.children || []) {
      for (const l of m.children || []) {
        if (l.value === flat) return [g.value, m.value, flat]
      }
    }
  }
  return ['trans_all', 'trans_all_only', 'trans_all_only_inherit']
}

const showCreateDialog = () => {
  createForm.value = {
    name: '',
    config: getDefaultConfig()
  }
  createPromptContent.value = ''
  promptData.value = []
  comparisonData.value = []
  createVisible.value = true
}

const handleCreate = async () => {
  const config = createForm.value.config
  if (!config.api_url || !config.api_key || !config.model) {
    ElMessage.error('API地址、API密钥、模型名称为必填项')
    return
  }
  createLoading.value = true
  try {
    const submitConfig = { ...config }
    submitConfig.type = flattenTypeToValue(submitConfig.type)
    const res = await createMcpKey({
      name: createForm.value.name,
      scope: 'user',
      config: submitConfig
    })
    createLoading.value = false
    if (res && res.code === 200) {
      createVisible.value = false
      newKeyData.value = res.data || {}
      newKeyVisible.value = true
      await fetchKeys()
    } else {
      ElMessage.error(res?.message || '创建失败')
    }
  } catch (e) {
    createLoading.value = false
    ElMessage.error('创建失败')
  }
}

const showDetail = async (key) => {
  try {
    const res = await getMcpKeyDetail(key.key_prefix)
    if (res && res.code === 200) {
      const data = res.data || {}
      detailData.value = key
      const config = data.config || {}
      config.type = expandTypeToArray(config.type)
      detailForm.value = {
        name: data.name || '',
        config: { ...config }
      }
      detailPromptContent.value = ''
      promptData.value = []
      comparisonData.value = []
      detailVisible.value = true

      await loadPrompts()
      if (config.prompt_id != null) {
        const selected = promptData.value.find(item => String(item.id) === String(config.prompt_id))
        detailPromptContent.value = selected ? selected.content : ''
      }
    }
  } catch (e) {
    ElMessage.error('获取详情失败')
  }
}

const handleUpdate = async () => {
  updateLoading.value = true
  try {
    const submitConfig = { ...detailForm.value.config }
    submitConfig.type = flattenTypeToValue(submitConfig.type)
    const res = await updateMcpKey(detailData.value.key_prefix, {
      name: detailForm.value.name,
      config: submitConfig
    })
    updateLoading.value = false
    if (res && res.code === 200) {
      ElMessage.success('配置已更新')
      detailVisible.value = false
      await fetchKeys()
    } else {
      ElMessage.error(res?.message || '更新失败')
    }
  } catch (e) {
    updateLoading.value = false
    ElMessage.error('更新失败')
  }
}

const handleRegenerate = async (key) => {
  try {
    await ElMessageBox.confirm(
      '重置密钥后旧密钥将立即失效，确定要重置吗？',
      '重置密钥',
      { type: 'warning' }
    )
    const res = await regenerateMcpKey(key.key_prefix)
    if (res && res.code === 200) {
      newKeyData.value = res.data || {}
      newKeyVisible.value = true
      await fetchKeys()
    } else {
      ElMessage.error(res?.message || '重置失败')
    }
  } catch {}
}

const handleToggleStatus = async (key) => {
  const newStatus = key.status === 'active' ? 'revoked' : 'active'
  try {
    const res = await updateMcpKey(key.key_prefix, { status: newStatus })
    if (res && res.code === 200) {
      ElMessage.success(newStatus === 'active' ? '已启用' : '已停用')
      await fetchKeys()
    } else {
      ElMessage.error('操作失败')
    }
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (key) => {
  try {
    await ElMessageBox.confirm('删除后无法恢复，确定删除吗？', '删除密钥', { type: 'danger' })
    const res = await deleteMcpKey(key.key_prefix)
    if (res && res.code === 200) {
      ElMessage.success('已删除')
      await fetchKeys()
    } else {
      ElMessage.error('删除失败')
    }
  } catch {}
}

const copyKey = (text) => {
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败，请手动复制')
  })
}

const copyCode = (type) => {
  let code = ''
  if (type === 'remote') {
    code = JSON.stringify({
      mcpServers: {
        doctranslator: {
          url: `${mcpUrl}/mcp/user`,
          headers: {
            Authorization: `Bearer ${currentKey.value || '你的密钥'}`
          }
        }
      }
    }, null, 2)
  } else {
    code = JSON.stringify({
      mcpServers: {
        'doctranslator-local': {
          command: 'python',
          args: ['mcp_local_server.py'],
          env: {
            DOCTRANSLATOR_URL: serverUrl,
            DOCTRANSLATOR_API_KEY: currentKey.value || '你的密钥',
            API_URL: '你的API地址',
            API_KEY: '你的API密钥',
            MODEL: 'gpt-4o',
            TYPE: 'trans_all_only_inherit',
            THREADS: '5',
            LANG: '中文'
          }
        }
      }
    }, null, 2)
  }
  navigator.clipboard.writeText(code).then(() => {
    ElMessage.success('已复制配置')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

onMounted(async () => {
  await fetchKeys()
})
</script>

<style scoped lang="scss">
.mcp-config {
  padding: 4px 0;
}

.mcp-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;

  .header-content {
    display: flex;
    gap: 14px;
  }

  h3 {
    margin: 0 0 4px;
    font-size: 18px;
    font-weight: 600;
    color: #1e293b;
  }

  .mcp-desc {
    color: #64748b;
    font-size: 13px;
    margin: 0;
    line-height: 1.5;
  }

  .create-btn {
    flex-shrink: 0;
    border-radius: 8px;
  }

  .limit-tag {
    flex-shrink: 0;
    margin-top: 4px;
  }
}

.mcp-keys {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 32px;
}

.mcp-key-card {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 18px 20px;
  background: white;
  transition: all 0.2s ease;

  &:hover {
    border-color: #cbd5e1;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  }

  .key-identity {
    flex: 1;
    min-width: 0;

    .key-name-row {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
    }

    .key-name {
      font-weight: 600;
      font-size: 15px;
      color: #1e293b;
    }

    .key-status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      flex-shrink: 0;

      &.active {
        background: #67c23a;
        box-shadow: 0 0 6px rgba(103, 194, 58, 0.4);
      }

      &.inactive {
        background: #f56c6c;
      }
    }

    .key-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      color: #94a3b8;
      font-size: 13px;
    }

    .key-prefix {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-family: 'SF Mono', 'Fira Code', monospace;
      color: #475569;
      background: #f1f5f9;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 12px;
    }

    .key-time {
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
  }

  .key-actions {
    display: flex;
    gap: 8px;
    flex-shrink: 0;

    .action-btn {
      border-radius: 6px;
    }
  }
}

.no-keys {
  text-align: center;
  padding: 48px 20px;
  background: #f8fafc;
  border-radius: 12px;
  border: 2px dashed #e2e8f0;

  .empty-visual {
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

.mcp-usage {
  h4 {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 16px;
  }

  .usage-blocks {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 16px;
  }

  .usage-block {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 18px;

    .usage-block-header {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 10px;

      .usage-badge {
        font-size: 11px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;

        &.remote {
          background: #eff6ff;
          color: #3b82f6;
        }

        &.local {
          background: #f0fdf4;
          color: #22c55e;
        }
      }

      h5 {
        margin: 0;
        font-size: 14px;
        font-weight: 600;
        color: #334155;
      }
    }

    p {
      color: #64748b;
      font-size: 13px;
      margin: 0 0 10px;
    }
  }

  .code-block-wrapper {
    position: relative;

    .copy-code-btn {
      position: absolute;
      top: 8px;
      right: 8px;
      color: #94a3b8;

      &:hover {
        color: #475569;
      }
    }
  }

  .code-block {
    background: #1e293b;
    color: #e2e8f0;
    border: none;
    border-radius: 8px;
    padding: 14px;
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 12px;
    line-height: 1.6;
    white-space: pre-wrap;
    overflow-x: auto;
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

    &:last-child {
      margin-bottom: 0;
    }
  }

  .el-form-item__label {
    padding-bottom: 4px;
    font-size: 13px;
    font-weight: 500;
    color: #475569;
  }
}

.prompt-preview {
  :deep(.el-textarea__inner) {
    background: #f8fafc;
    color: #475569;
    font-size: 13px;
    line-height: 1.6;
  }
}

.new-key-display {
  text-align: center;
  padding: 4px 0;

  .new-key-icon {
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

    .create-btn {
      width: 100%;
    }
  }

  .mcp-key-card {
    flex-direction: column;
    gap: 12px;
    padding: 14px;

    .key-meta {
      flex-direction: column;
      gap: 6px;
    }

    .key-actions {
      flex-wrap: wrap;
      width: 100%;
      justify-content: space-between;

      .action-btn {
        flex: 0 0 auto;
        min-width: 0;
        padding: 8px;
      }

      .action-text {
        display: none;
      }
    }
  }

  .mcp-usage .usage-blocks {
    grid-template-columns: 1fr;
  }

  .new-key-display .key-display-box {
    flex-direction: column;

    .copy-key-btn {
      width: 100%;
    }
  }

  .mcp-form {
    .el-form-item {
      margin-bottom: 10px;
    }
  }
}

@media screen and (max-width: 480px) {
  .mcp-config {
    padding: 0;
  }

  .mcp-key-card .key-actions {
    gap: 6px;

    .action-btn {
      flex: 1 1 calc(25% - 6px);
      padding: 6px 4px;
    }
  }

  .mcp-form {
    .el-form-item {
      margin-bottom: 8px;
    }
  }
}
</style>
