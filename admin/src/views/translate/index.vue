<script lang="ts" setup>
import { reactive, ref, watch } from "vue"
import { getToken } from "@/utils/cache/cookies"
import {
  getTranslateDataApi,
  deleteTranslateDataApi,
  deleteMoreTranslateDataApi,
  downloadMoreTranslateDataApi
} from "@/api/translate"
import { type GetTranslateData } from "@/api/translate/types/translate"
import { type FormInstance, ElMessage, ElMessageBox } from "element-plus"
import { Search, Refresh, CirclePlus, Download, Delete, RefreshRight } from "@element-plus/icons-vue"
import { usePagination } from "@/hooks/usePagination"
import { cloneDeep } from "lodash-es"
const BASE_URL = import.meta.env.VITE_BASE_API
defineOptions({
  // 命名当前组件
  name: "Translate"
})

const loading = ref<boolean>(false)
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()

//#region 删
const handleDelete = (row: GetTranslateData) => {
  ElMessageBox.confirm(`确认删除当前文档吗？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    deleteTranslateDataApi(row.id).then(() => {
      ElMessage.success("删除成功")
      getTableData()
    })
  })
}

//获取选择项
const selectedItems = ref<number[]>([])
const handleSelectionChange = (selection: any[]) => {
  selectedItems.value = selection.map((item) => item.id)
  console.log(selectedItems.value)
}

//#region 批量删除
const handleMoreDelete = () => {
  if (selectedItems.value.length === 0) {
    ElMessage.warning("请选择要删除的文档")
    return
  }
  ElMessageBox.confirm(`正在批量删除选中文档，确认删除？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    deleteMoreTranslateDataApi({ ids: selectedItems.value }).then(() => {
      ElMessage.success("删除成功")
      getTableData()
    })
  })
}

//#region 批量下载
const handleMoreDownload = () => {
  if (selectedItems.value.length === 0) {
    ElMessage.warning("请选择要下载的文档")
    return
  }

  const ids = selectedItems.value
  const url = `${BASE_URL}/api/admin/translates/download/batch`
  const token = getToken()
  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      token: token
    },
    body: JSON.stringify({ ids })
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok")
      }
      return response.blob()
    })
    .then((blob) => {
      const currentDate = new Date().toISOString().split("T")[0] // 获取当前日期，格式为 YYYY-MM-DD
      const filename = `downloads_${currentDate}.zip`
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    })
    .catch((error) => {
      console.log(error)
      ElMessage.error("下载失败，请稍后重试")
    })
}
//#endregion

//#region 查
const translateData = ref<GetTranslateData[]>([])
const searchFormRef = ref<FormInstance | null>(null)
const searchData = reactive({
  keyword: ""
})
const getTableData = () => {
  loading.value = true
  getTranslateDataApi({
    page: paginationData.currentPage,
    limit: paginationData.pageSize,
    keyword: searchData.keyword || undefined
  })
    .then(({ data }) => {
      paginationData.total = data.total
      translateData.value = data.data
    })
    .catch(() => {
      translateData.value = []
    })
    .finally(() => {
      loading.value = false
    })
}
const handleSearch = () => {
  paginationData.currentPage === 1 ? getTableData() : (paginationData.currentPage = 1)
}
const resetSearch = () => {
  searchFormRef.value?.resetFields()
  handleSearch()
}
//#endregion

/** 监听分页参数的变化 */
watch([() => paginationData.currentPage, () => paginationData.pageSize], getTableData, { immediate: true })
</script>

<template>
  <div class="app-container">
    <el-card v-loading="loading" shadow="never">
      <el-form ref="searchFormRef" :inline="true" :model="searchData">
        <el-form-item prop="keyword" label="" style="width: 320px; max-width: 100%">
          <el-input v-model="searchData.keyword" placeholder="输入查询" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="resetSearch">重置</el-button>
          <el-button :icon="Delete" @click="handleMoreDelete">删除</el-button>
          <el-button :icon="Download" @click="handleMoreDownload">下载</el-button>
        </el-form-item>
      </el-form>
      <div class="table-wrapper">
        <el-table :data="translateData" @selection-change="handleSelectionChange">
          <el-table-column type="selection" width="50" align="left" />
          <el-table-column prop="customer_no" width="80" label="用户ID" align="left" />
          <el-table-column prop="customer_email" label="用户邮箱" width="150" align="left" />
          <el-table-column prop="origin_filename" label="文档名称" align="left" />
          <el-table-column prop="status" label="任务状态" align="left" width="120">
            <template #default="scope">
              <el-tag v-if="scope.row.status == 'none'" type="primary" effect="plain">未完成</el-tag>
              <el-tag v-else-if="scope.row.status == 'process'" type="warning" effect="plain">翻译中</el-tag>
              <el-tag v-else-if="scope.row.status == 'failed'" type="danger" effect="plain">翻译失败</el-tag>
              <el-tag v-else type="success" effect="plain">已完成</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="start_at" label="任务开始时间" align="left" />
          <el-table-column prop="spend_time" label="完成用时" width="100" align="left" />
          <el-table-column prop="deleted_flag" label="用户是否删除" align="left" width="120">
            <template #default="scope">
              <el-tag v-if="scope.row.deleted_flag == 'Y'" type="primary" effect="plain">是</el-tag>
              <el-tag v-else-if="scope.row.deleted_flag == 'N'" type="warning" effect="plain">否</el-tag>
            </template>
          </el-table-column>
          <el-table-column fixed="right" label="操作" width="100" align="left">
            <template #default="scope">
              <el-link
                style="color: #409eff; margin-right: 12px"
                v-if="scope.row.target_filepath"
                :href="BASE_URL + '/api/admin/translate/download/' + scope.row.id"
                >下载</el-link
              >
              <el-button type="danger" text size="small" @click="handleDelete(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div class="pager-wrapper">
        <el-pagination
          background
          :layout="paginationData.layout"
          :page-sizes="paginationData.pageSizes"
          :total="paginationData.total"
          :page-size="paginationData.pageSize"
          :currentPage="paginationData.currentPage"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<style lang="scss" scoped>
.search-wrapper {
  margin-bottom: 20px;
  :deep(.el-card__body) {
    padding-bottom: 2px;
  }
}

.toolbar-wrapper {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.table-wrapper {
  margin-bottom: 20px;
}

.pager-wrapper {
  display: flex;
  justify-content: flex-end;
}
</style>
