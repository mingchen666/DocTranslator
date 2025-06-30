<template>
  <div class="file-manager">
    <!-- 顶部标题栏 -->
    <div class="header">
      <h2>
        <el-icon class="header-icon"><FolderOpened /></el-icon>
        文件存储管理
      </h2>
      <el-button type="primary" plain @click="refreshData" :loading="loading" class="refresh-btn">
        <el-icon><Refresh /></el-icon>刷新
      </el-button>
    </div>

    <!-- 主内容区 -->
    <el-card class="content-card" v-loading="loading" :element-loading-text="'加载中...'">
      <!-- 分类标签页 - 强制显示两个tab -->
      <el-tabs v-model="activeTab" class="main-tabs">
        <!-- 上传文档标签页 -->
        <el-tab-pane name="uploads">
          <template #label>
            <div class="tab-label">
              <el-icon class="tab-icon uploads"><Upload /></el-icon>
              <span>上传文档</span>
              <el-tag size="small" effect="light" class="size-tag">
                {{ formatSize(fileData.uploads?.size || 0) }}
              </el-tag>
            </div>
          </template>

          <!-- 上传文档内容区 -->
          <template v-if="hasData('uploads')">
            <div class="category-actions">
              <el-button
                type="danger"
                size="medium"
                @click="confirmDelete('category', 'uploads')"
                class="delete-category-btn"
              >
                <el-icon><Delete /></el-icon>删除全部文件
              </el-button>
            </div>

            <el-collapse v-model="expandedDates.uploads" accordion class="date-collapse">
              <el-collapse-item
                v-for="(dateData, date) in fileData.uploads.dates"
                :key="date"
                :name="date"
                class="date-item"
              >
                <template #title>
                  <div class="date-header">
                    <el-icon size="20" class="date-icon"><Calendar /></el-icon>
                    <span class="date-text">{{ date }}</span>
                    <div class="date-meta">
                      <span class="file-count">{{ dateData.files.length }}个文件</span>
                      <span class="date-size">共{{ formatSize(dateData.size) }}</span>
                    </div>
                    <div class="date-actions">
                      <el-button
                        type="danger"
                        size="small"
                        plain
                        @click.stop="confirmDelete('date', `uploads/${date}`)"
                        class="delete-date-btn"
                      >
                        <el-icon><Delete /></el-icon>删除本日所有文件
                      </el-button>
                    </div>
                  </div>
                </template>

                <div class="file-table-container">
                  <el-table :data="dateData.files" border stripe empty-text="该日期没有文件" class="file-table">
                    <el-table-column label="文件名" width="220">
                      <template #default="{ row }">
                        <div class="file-name-cell">
                          <el-icon class="file-icon">
                            <component :is="getFileIcon(row.name)" />
                          </el-icon>
                          <span class="file-name">{{ row.name }}</span>
                        </div>
                      </template>
                    </el-table-column>

                    <el-table-column label="大小" width="120">
                      <template #default="{ row }">
                        <el-tag size="small" effect="plain">
                          {{ formatSize(row.size) }}
                        </el-tag>
                      </template>
                    </el-table-column>

                    <el-table-column label="文件路径" min-width="300">
                      <template #default="{ row }">
                        <el-tooltip :content="row.path" placement="top">
                          <span class="file-path">{{ row.path }}</span>
                        </el-tooltip>
                      </template>
                    </el-table-column>

                    <el-table-column label="操作" width="120" align="center">
                      <template #default="{ row }">
                        <el-popconfirm title="确定要删除此文件吗？" @confirm="handleDeleteFile(row.path)">
                          <template #reference>
                            <el-button type="danger" size="small" round> 删除 </el-button>
                          </template>
                        </el-popconfirm>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </el-collapse-item>
            </el-collapse>
          </template>
          <div v-else class="empty-container">
            <el-empty description="暂无上传文件" />
          </div>
        </el-tab-pane>

        <!-- 翻译文档标签页 -->
        <el-tab-pane name="translate">
          <template #label>
            <div class="tab-label">
              <el-icon class="tab-icon translate"><Files /></el-icon>
              <span>翻译文档</span>
              <el-tag size="small" effect="light" class="size-tag">
                {{ formatSize(fileData.translate?.size || 0) }}
              </el-tag>
            </div>
          </template>

          <!-- 翻译文档内容区 -->
          <template v-if="hasData('translate')">
            <div class="category-actions">
              <el-button
                type="danger"
                size="small"
                @click="confirmDelete('category', 'translate')"
                class="delete-category-btn"
              >
                <el-icon><Delete /></el-icon>删除全部文件
              </el-button>
            </div>

            <el-collapse v-model="expandedDates.translate" accordion class="date-collapse">
              <el-collapse-item
                v-for="(dateData, date) in fileData.translate.dates"
                :key="date"
                :name="date"
                class="date-item"
              >
                <template #title>
                  <div class="date-header">
                    <el-icon size="20" class="date-icon"><Calendar /></el-icon>
                    <span class="date-text">{{ date }}</span>
                    <div class="date-meta">
                      <span class="file-count">{{ dateData.files.length }}个文件</span>
                      <span class="date-size">共{{ formatSize(dateData.size) }}</span>
                    </div>
                    <div class="date-actions">
                      <el-button
                        type="danger"
                        size="small"
                        @click.stop="confirmDelete('date', `translate/${date}`)"
                        class="delete-date-btn"
                      >
                        <el-icon><Delete /></el-icon>删除本日所有文件
                      </el-button>
                    </div>
                  </div>
                </template>

                <div class="file-table-container">
                  <el-table :data="dateData.files" border stripe empty-text="该日期没有文件" class="file-table">
                    <el-table-column label="文件名" width="220">
                      <template #default="{ row }">
                        <div class="file-name-cell">
                          <el-icon class="file-icon">
                            <component :is="getFileIcon(row.name)" />
                          </el-icon>
                          <span class="file-name">{{ row.name }}</span>
                        </div>
                      </template>
                    </el-table-column>

                    <el-table-column label="大小" width="120">
                      <template #default="{ row }">
                        <el-tag size="small" effect="plain">
                          {{ formatSize(row.size) }}
                        </el-tag>
                      </template>
                    </el-table-column>

                    <el-table-column label="文件路径" min-width="300">
                      <template #default="{ row }">
                        <el-tooltip :content="row.path" placement="top">
                          <span class="file-path">{{ row.path }}</span>
                        </el-tooltip>
                      </template>
                    </el-table-column>

                    <el-table-column label="操作" width="120" align="center">
                      <template #default="{ row }">
                        <el-popconfirm title="确定要删除此文件吗？" @confirm="handleDeleteFile(row.path)">
                          <template #reference>
                            <el-button type="danger" size="small" round> 删除 </el-button>
                          </template>
                        </el-popconfirm>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </el-collapse-item>
            </el-collapse>
          </template>
          <div v-else class="empty-container">
            <el-empty description="暂无翻译文件" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import {
  FolderOpened,
  Refresh,
  Delete,
  Calendar,
  Document,
  Tickets,
  Collection,
  Notebook,
  Upload,
  Files
} from "@element-plus/icons-vue"
import { getFileList, deleteFile } from "@/api/setting/file"
import { ElMessage, ElMessageBox } from "element-plus"

// 响应式数据
const loading = ref(false)
const fileData = ref({
  uploads: { size: 0, dates: {} },
  translate: { size: 0, dates: {} }
})
const activeTab = ref("uploads")
const expandedDates = ref({
  uploads: [],
  translate: []
})

// 计算是否有数据
const hasData = (category) => {
  return fileData.value[category]?.dates && Object.keys(fileData.value[category].dates).length > 0
}

// 初始化加载
onMounted(() => {
  loadData()
})

// 加载数据
const loadData = async () => {
  try {
    loading.value = true
    const res = await getFileList()
    if (res.code === 200) {
      // 合并数据确保两个分类都存在
      fileData.value = {
        uploads: res.data.uploads || { size: 0, dates: {} },
        translate: res.data.translate || { size: 0, dates: {} }
      }

      // 默认展开每个分类的第一个日期
      for (const cat in fileData.value) {
        if (Object.keys(fileData.value[cat].dates).length > 0) {
          expandedDates.value[cat] = [Object.keys(fileData.value[cat].dates)[0]]
        }
      }
    }
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = () => loadData()

// 格式化文件大小
const formatSize = (bytes) => {
  if (bytes === 0) return "0 B"
  const k = 1024
  const sizes = ["B", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
}

// 获取文件图标
const getFileIcon = (filename) => {
  const ext = filename.split(".").pop().toLowerCase()
  return (
    {
      pdf: Document,
      doc: Tickets,
      docx: Tickets,
      xls: Collection,
      xlsx: Collection,
      ppt: Notebook,
      pptx: Notebook
    }[ext] || Document
  )
}

// 删除文件
const handleDeleteFile = async (filePath) => {
  try {
    await deleteFile({ type: "file", target: filePath })
    ElMessage.success("文件删除成功")
    await loadData()
  } catch (error) {
    ElMessage.error("删除失败: " + error.message)
  }
}

// 确认删除
const confirmDelete = (type, target) => {
  const messages = {
    file: `确定要删除文件 "${target.split("/").pop()}" 吗？`,
    date: `确定要删除日期 "${target.split("/")[1]}" 的所有文件吗？`,
    category: `确定要删除整个 "${target}" 分类吗？`
  }

  ElMessageBox.confirm(messages[type], "警告", {
    confirmButtonText: "确定删除",
    cancelButtonText: "取消",
    type: "warning",
    beforeClose: async (action, instance, done) => {
      if (action === "confirm") {
        instance.confirmButtonLoading = true
        try {
          await deleteFile({ type, target })
          ElMessage.success("删除成功")
          await loadData()
          done()
        } catch (error) {
          ElMessage.error("删除失败: " + error.message)
        } finally {
          instance.confirmButtonLoading = false
        }
      } else {
        done()
      }
    }
  }).catch(() => {})
}
</script>

<style scoped>
.file-manager {
  padding: 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 0 10px;
}

.header h2 {
  margin: 0;
  display: flex;
  align-items: center;
  font-size: 20px;
  color: #333;
}

.header-icon {
  margin-right: 10px;
  color: var(--el-color-primary);
}

.refresh-btn {
  margin-left: auto;
}

.content-card {
  flex: 1;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
}

.main-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.tab-label {
  font-size: 20px;
  display: flex;
  align-items: center;
  padding: 0 15px;
  gap: 8px;
}

.tab-icon {
  font-size: 18px;
}

.tab-icon.uploads {
  color: var(--el-color-success);
}

.tab-icon.translate {
  color: var(--el-color-warning);
}

.size-tag {
  margin-left: 8px;
}

.category-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
  padding: 0 10px;
}

.delete-category-btn {
  margin-left: auto;
}

.date-collapse {
  flex: 1;
}

.date-item {
  margin-bottom: 15px;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.date-header {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 12px 15px;
  gap: 15px;
  flex-wrap: wrap;
}

.date-icon {
  color: var(--el-color-primary);
}

.date-text {
  font-size: 16px;
  font-weight: 500;
}

.date-meta {
  display: flex;
  gap: 15px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  margin-left: auto;
  margin-right: 15px;
}

.date-actions {
  flex-shrink: 0;
}

.delete-date-btn {
  white-space: nowrap;
}

.file-table-container {
  padding: 0 10px 15px;
}

.file-table {
  width: 100%;
  margin-bottom: 15px;
}

.file-name-cell {
  display: flex;
  align-items: center;
}

.file-icon {
  margin-right: 8px;
  color: var(--el-color-primary);
}

.file-name {
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-path {
  font-family: monospace;
  font-size: 13px;
  color: #666;
  display: inline-block;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
  border-radius: 8px;
  background-color: #f8f8f8;
  margin: 10px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .date-header {
    gap: 8px;
  }

  .date-meta {
    order: 1;
    width: 100%;
    margin-left: 0;
    justify-content: flex-end;
    margin-top: 8px;
  }
}
</style>
