<script lang="ts" setup>
import { reactive, ref, watch } from "vue"
import { changeCustomerStatusApi, updateCustomerDataApi, getCustomerDataApi } from "@/api/customer"
import { type CreateOrUpdateCustomerRequestData, type GetCustomerData } from "@/api/customer/types/customer"
import { type FormInstance, type FormRules, ElMessage } from "element-plus"
import { Search, Refresh, CirclePlus } from "@element-plus/icons-vue"
import { usePagination } from "@/hooks/usePagination"
import { cloneDeep } from "lodash-es"
import Register from "./components/register.vue"

defineOptions({
  // 命名当前组件
  name: "ElementPlus"
})

const loading = ref<boolean>(false)
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()

//#region 增
const DEFAULT_FORM_DATA: CreateOrUpdateCustomerRequestData = {
  id: undefined,
  email: "",
  password: "",
  level: "common"
}

const dialogVisible = ref<boolean>(false)
const formRef = ref<FormInstance | null>(null)
const formData = ref<CreateOrUpdateCustomerRequestData>(cloneDeep(DEFAULT_FORM_DATA))
const formRules: FormRules<CreateOrUpdateCustomerRequestData> = {
  email: [{ required: true, trigger: "blur", message: "请输入注册邮箱" }],
  password: [{ min: 6, max: 16, message: "长度在 6 到 16 个字符", trigger: "blur" }],
  level: [{ required: true, trigger: "blur", message: "请选择用户等级" }]
}
const handleCreateOrUpdate = () => {
  formRef.value?.validate((valid: boolean, fields) => {
    if (!valid) return console.error("表单校验不通过", fields)
    loading.value = true
    // const api = formData.value.id === undefined ? createTableDataApi : updateTableDataApi
    updateCustomerDataApi(formData.value)
      .then(() => {
        ElMessage.success("操作成功")
        dialogVisible.value = false
        getCustomerData()
      })
      .finally(() => {
        loading.value = false
      })
  })
}
const resetForm = () => {
  formRef.value?.clearValidate()
  formData.value = cloneDeep(DEFAULT_FORM_DATA)
  dialogVisible.value = false
}
//#endregion

//#region 删
const handleStatus = (id: number, status: string) => {
  changeCustomerStatusApi(id, status).then(() => {
    ElMessage.success("更改状态成功")
    getCustomerData()
  })
}
//#endregion

//#region 改
const handleUpdate = (row: GetCustomerData) => {
  dialogVisible.value = true
  // formData.value = cloneDeep(row)
  formData.value = Object.assign(cloneDeep(row), { password: "" })
}
//#endregion

//#region 查
const customerData = ref<GetCustomerData[]>([])
const searchFormRef = ref<FormInstance | null>(null)
const searchData = reactive({
  keyword: ""
})
const getCustomerData = () => {
  loading.value = true
  getCustomerDataApi({
    page: paginationData.currentPage,
    limit: paginationData.pageSize,
    keyword: searchData.keyword || undefined
  })
    .then(({ data }) => {
      paginationData.total = data.total
      customerData.value = data.data
    })
    .catch(() => {
      customerData.value = []
    })
    .finally(() => {
      loading.value = false
    })
}
const handleSearch = () => {
  paginationData.currentPage === 1 ? getCustomerData() : (paginationData.currentPage = 1)
}

const resetSearch = () => {
  searchData.keyword = ""
  handleSearch()
}
//#endregion
// 新增用户
const registerVisible = ref<boolean>(false)
const newUser = () => {
  registerVisible.value = true
}

const registerSuccess = () => {
  registerVisible.value = false
  getCustomerData()
}

/** 监听分页参数的变化 */
watch([() => paginationData.currentPage, () => paginationData.pageSize], getCustomerData, { immediate: true })
</script>
<template>
  <div class="app-container">
    <el-card v-loading="loading" shadow="never">
      <el-form ref="searchFormRef" :inline="true" :model="searchData">
        <el-form-item prop="username" label="" style="width: 320px; max-width: 100%">
          <el-input v-model="searchData.keyword" placeholder="输入查询" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="CirclePlus" @click="newUser">新增用户</el-button>
        </el-form-item>
      </el-form>

      <div class="table-wrapper">
        <el-table :data="customerData">
          <!-- <el-table-column type="selection" width="50" align="center" /> -->
          <el-table-column prop="customer_no" label="用户编号" align="left" />
          <el-table-column prop="email" label="注册邮箱" align="left" />
          <el-table-column prop="level" label="用户等级" align="left">
            <template #default="scope">
              <el-tag v-if="scope.row.level == 'vip'" type="primary" effect="plain">会员用户</el-tag>
              <el-tag v-else type="warning" effect="plain">普通用户</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="账户状态" align="left">
            <template #default="scope">
              <el-tag v-if="scope.row.status == 'enabled'" type="success" effect="plain">启用</el-tag>
              <el-tag v-else type="danger" effect="plain">禁用</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="注册时间" align="left" />
          <el-table-column fixed="right" label="操作" width="100" align="left">
            <template #default="scope">
              <el-button type="primary" text size="small" @click="handleUpdate(scope.row)">编辑</el-button>
              <el-button
                type="danger"
                v-if="scope.row.status == 'enabled'"
                text
                size="small"
                @click="handleStatus(scope.row.id, 'disabled')"
                >禁用</el-button
              >
              <el-button type="success" v-else text size="small" @click="handleStatus(scope.row.id, 'enabled')"
                >启用</el-button
              >
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
    <!-- 新增/修改 -->
    <el-dialog modal-class="custom_dialog" v-model="dialogVisible" :show-close="false">
      <template #header>
        <div class="dialog_head">
          <div class="title">{{ formData.id === undefined ? "新增用户" : "编辑用户信息" }}</div>
          <el-icon @click="resetForm"><Close /></el-icon>
        </div>
      </template>
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px" label-position="left">
        <el-form-item prop="email" label="注册邮箱">
          <el-input v-model="formData.email" placeholder="请输入注册邮箱" />
        </el-form-item>
        <el-form-item prop="level" label="用户等级">
          <el-select v-model="formData.level" placeholder="">
            <el-option label="会员用户" value="vip" />
            <el-option label="普通用户" value="common" />
          </el-select>
        </el-form-item>
        <el-form-item prop="password" label="密码">
          <el-input type="password" v-model="formData.password" placeholder="请输入" />
        </el-form-item>
      </el-form>
      <div class="btn_box">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateOrUpdate" :loading="loading">确认</el-button>
      </div>
    </el-dialog>
    <!-- 注册弹窗 -->
    <el-dialog
      v-model="registerVisible"
      center
      width="90%"
      modal-class="custom_dialog login_dialog"
      :show-close="false"
    >
      <template #header> 添加用户 </template>
      <Register @success="registerSuccess" />
    </el-dialog>
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
:deep(.custom_dialog) {
  .el-dialog {
    padding: 30px 50px;
    width: 90%;
    max-width: 600px;
    .el-form-item__label {
      justify-content: right;
    }
  }
  .btn_box {
    text-align: right;
  }
  .dialog_head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
    .title {
      font-weight: bold;
      font-size: 16px;
      color: #333333;
    }
    .el-icon {
      font-size: 20px;
    }
  }
  @media screen and (max-width: 750px) {
    .el-dialog {
      padding: 20px;
    }
  }
}
</style>
