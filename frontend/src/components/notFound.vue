<template>
  <div class="four_container">
    <div class="cener_box">
      <div class="img_box">
        <img src="@/assets/404.png" alt="">
      </div>
      <div class="text_box">
        <div class="title">抱歉，页面走丢了...</div>
        <el-button type="text" @click="back"><span class="btn">返回首页</span></el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
const router = useRouter();
function back(){
  router.push({name:'home'})
}
</script>
<style scoped lang="scss">
.four_container{
  transform: translate(-50%,-50%);
  position: absolute;
  top: 40%;
  left: 50%;
}
.cener_box{
  position: relative;
  width: 100%;
  max-width: 1200px;
  display: flex;
  align-items: center;
  img{
    margin-right: 140px;
  }
  .title{
    font-weight: bold;
    font-size: 24px;
    color: #333333;
    margin-bottom: 30px;
  }
  .btn{
    font-size: 16px;
    color: #045CF9;
    text-decoration-line: underline;
  }
}
@media screen and (max-width: 767px) {
  .cener_box{
    flex-direction: column;
    img{
      margin-right: 0;
      margin-bottom: 30px;
    }
  }
}
</style>
