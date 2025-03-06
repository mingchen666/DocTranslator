<template>
  <!-- v-loading="pageLoad" -->
  <div
    class="page-center"
    v-loading="pageLoad"
    element-loading-text="loading..."
    element-loading-spinner="el-icon-loading"
    element-loading-background="rgba(255, 255, 255, 0.7)"
  >
    <div class="container">
      <div class="tab_box">
        <div class="tab_li" @click="$router.push('/corpus/index')">我的</div>
        <div class="tab_li actived">广场</div>
      </div>
      <div class="content_box">
        <div class="flex_box flex-between">
          <el-button-group>
            <el-button
              :class="tab_active == 'terms' ? 'btn_active' : 'my_button'"
              :plain="tab_active == 'terms' ? false : true"
              :type="tab_active == 'terms' ? 'primary' : ''"
              @click="tab_active = 'terms'"
            >
              术语表
            </el-button>
            <el-button
              :class="tab_active == 'prompt' ? 'btn_active' : 'my_button'"
              :plain="tab_active == 'prompt' ? false : true"
              :type="tab_active == 'prompt' ? 'primary' : ''"
              @click="tab_active = 'prompt'"
            >
              提示语
            </el-button>
          </el-button-group>
          <!-- 术语表过滤条件 -->
          <el-select
            v-if="tab_active == 'terms'"
            v-model="termForm.order"
            style="width: 100px"
            @change="change_terms"
          >
            <el-option value="latest" label="最新发布"></el-option>
            <el-option value="fav" label="收藏量"></el-option>
            <el-option value="added" label="添加量"></el-option>
          </el-select>
          <!-- 提示语过滤条件 -->
          <el-select
            v-if="tab_active == 'prompt'"
            v-model="promptForm.porder"
            style="width: 100px"
            @change="change_prompt"
          >
            <el-option value="latest" label="最新发布"></el-option>
            <el-option value="fav" label="收藏量"></el-option>
            <el-option value="added" label="添加量"></el-option>
          </el-select>
        </div>
        <!-- 公共术语列表 -->
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
                    <el-button type="text" @click="addTerms(item)">加入我的语料库</el-button>
                  </div>
                  <div class="right">
                    <div
                      :class="item.faved == 1 ? 'icon_actived icon_star' : 'icon_star'"
                      @click="favTerms(item)"
                    >
                      <svg-icon :icon-class="item.faved == 1 ? 'favd' : 'fav'" />
                    </div>
                  </div>
                </div>
                <div class="des_box flex_box flex-between">
                  <div class="t_left">{{ item.email }} 被加入{{ item.added_count }}次</div>
                  <div class="t_right">{{ item.created_at }}</div>
                </div>
                <div class="table_box" v-if="item.content.length > 0">
                  <el-table
                    size="small"
                    :data="item.content"
                    style="width: 100%"
                    max-height="160"
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
          <div class="page_box" v-if="termsTotal > 0">
            <el-pagination
              :current-page="termForm.page"
              :page-size="termForm.limit"
              layout="prev, pager, next, jumper"
              :total="termsTotal"
              :pager-count="5"
              @current-change="termCurrentChange"
            />
          </div>
        </div>
        <!-- 公共提示语列表 -->
        <div class="prompt_box" v-if="tab_active == 'prompt'">
          <el-row :gutter="24" v-if="promptData.length > 0">
            <el-col :xs="24" :sm="8" v-for="(item, index) in promptData" :key="index">
              <div class="term_li">
                <div class="flex_box title_box flex-between">
                  <div class="t" :title="item.title">{{ item.title }}</div>
                </div>
                <div class="btn_box flex_box flex-between">
                  <div class="left">
                    <el-button type="text" @click="addPrompt(item)">加入我的提示语</el-button>
                  </div>
                  <div class="right">
                    <div
                      :class="item.faved == 1 ? 'icon_actived icon_star' : 'icon_star'"
                      @click="favPrompt(item)"
                    >
                      <svg-icon :icon-class="item.faved == 1 ? 'favd' : 'fav'" />
                    </div>
                  </div>
                </div>
                <div class="des_box flex_box flex-between">
                  <div class="t_left">{{ item.email }} 被加入{{ item.added_count }}次</div>
                  <div class="t_right">{{ item.created_at }}</div>
                </div>
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
          <div class="page_box" v-if="promptTotal > 0">
            <el-pagination
              :current-page="promptForm.page"
              :page-size="promptForm.limit"
              layout="prev, pager, next, jumper"
              :total="promptTotal"
              :pager-count="5"
              @current-change="promptCurrentChange"
            />
          </div>
        </div>
      </div>

      <!-- 备案信息 -->
      <Filing />
    </div>
  </div>
</template>

<script setup>
import Filing from '@/components/filing.vue'
// import { useRouter } from 'vue-router'
import { store } from '@/store/index'
import SvgIcon from '@/components/SvgIcon/index.vue'
import { reactive, ref, computed,  onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  comparison_share,
  prompt_share,
  comparison_copy,
  comparison_fav,
  prompt_copy,
  prompt_fav
} from '@/api/square'

// const uploadUrl = ref(import.meta.env.VITE_API_URL + '/api/comparison/import?token=' + store.token)
const pageLoad = ref(false)
const termsData = ref([])
const termsTotal = ref(0)
const promptData = ref([])
const promptTotal = ref(0)

const tab_active = ref('terms')
const termForm = ref({
  order: 'latest',
  page: 1,
  limit: 9
})
const promptForm = ref({
  porder: 'latest',
  page: 1,
  limit: 9
})
// 获取术语表数据
const getTermList = async () => {
  pageLoad.value = true
  try {
    const res = await comparison_share(termForm.value)
    if (res.code === 200) {
      termsData.value = res.data.data
    }
  } catch (error) {
    console.error('获取术语表数据时出错:', error)
  }
  pageLoad.value = false
}

function change_terms() {
  termForm.value.page = 1
  getTermList()
}

function change_prompt() {
  promptForm.value.page = 1
  getPromptList()
}

//切换术语分页
function termCurrentChange(val) {
  termForm.value.page = val
  getTermList()
  //回到顶部
  //this.$refs.container_center.scrollTop = 0;
}

// 获取提示语数据
const getPromptList = async () => {
  pageLoad.value = true
  try {
    const res = await prompt_share(promptForm.value)
    if (res.code === 200) {
      promptData.value = res.data.data
    }
  } catch (error) {
    console.error('获取提示语数据时出错:', error)
  }
  pageLoad.value = false
}

//切换提示语分页
function promptCurrentChange(val) {
  termForm.value.page = val
  getPromptList()
  //回到顶部
  //this.$refs.container_center.scrollTop = 0;
}

//加入我的术语
function addTerms(item) {
  pageLoad.value = true
  comparison_copy(item.id)
    .then((data) => {
      pageLoad.value = false
      if (data.code == 200) {
        ElMessage({ message: '添加成功，请到我的术语表中查看', type: 'success' })
        item.added_count++
      } else {
        ElMessage({ message: data.message, type: 'error' })
      }
    })
    .catch((err) => {
      ElMessage({ message: '接口异常', type: 'error' })
    })
}

//加入我的提示语
function addPrompt(item) {
  pageLoad.value = true
  prompt_copy(item.id)
    .then((data) => {
      pageLoad.value = false
      if (data.code == 200) {
        ElMessage({ message: '添加成功，请到我的提示语中查看', type: 'success' })
        item.added_count++
      } else {
        ElMessage({ message: data.message, type: 'error' })
      }
    })
    .catch((err) => {
      ElMessage({ message: '接口异常', type: 'error' })
    })
}

//术语收藏
function favTerms(item) {
  pageLoad.value = true
  comparison_fav(item.id)
    .then((data) => {
      pageLoad.value = false
      if (data.code == 200) {
        ElMessage({ message: '操作成功', type: 'success' })
        if (item.faved == 1) {
          item.faved = 0
        } else {
          item.faved = 1
        }
      } else {
        ElMessage({ message: data.message, type: 'error' })
      }
    })
    .catch((err) => {
      ElMessage({ message: '接口异常', type: 'error' })
    })
}

//收藏 提示语
function favPrompt(item) {
  pageLoad.value = true
  prompt_fav(item.id)
    .then((data) => {
      pageLoad.value = false
      if (data.code == 200) {
        ElMessage({ message: '操作成功', type: 'success' })
        if (item.faved == 1) {
          item.faved = 0
        } else {
          item.faved = 1
        }
      } else {
        ElMessage({ message: data.message, type: 'error' })
      }
    })
    .catch((err) => {
      ElMessage({ message: '接口异常', type: 'error' })
    })
}

onMounted(() => {
  getTermList()
  getPromptList()
})
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
      height: 40px;
      .icon_star {
        font-size: 16px;
        color: #999;
        cursor: pointer;
      }
      .icon_actived {
        color: #055cf9;
      }
    }
    .des_box {
      padding: 0 20px;
      font-weight: 400;
      font-size: 12px;
      color: #666666;
      opacity: 0.9;
      line-height: 18px;
      margin-bottom: 10px;
    }
    .table_box {
      padding: 0 20px;
      height: 182px;
    }
    .text_box {
      padding: 0 20px;
      padding-bottom: 22px;
      .text {
        box-sizing: border-box;
        height: 220px;
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

  .page_box {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 20px;
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
}

@media screen and (max-width: 767px) {
  .des_box {
    flex-direction: column;
    align-items: flex-start;
    .t_right {
      margin-top: 5px;
    }
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
