<template>
  <el-container class="app-container" v-if="$route.name !== 'Login'">
    <el-aside width="240px" class="aside-menu">
      <div class="logo">基层法检协同预警平台</div>
      <el-menu router :default-active="$route.path" background-color="#304156" text-color="#bfcbd9" active-text-color="#409eff" style="border-right:none">
        <el-menu-item index="/"><el-icon><DataBoard /></el-icon><span>多维治理大屏</span></el-menu-item>
        <el-menu-item index="/warnings"><el-icon><Warning /></el-icon><span>风险预警中心</span></el-menu-item>
        <el-menu-item index="/cases"><el-icon><Tickets /></el-icon><span>协同跟进台账</span></el-menu-item>
        <el-menu-item index="/audit"><el-icon><Document /></el-icon><span>安全审计日志</span></el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <span style="font-weight: 600; color: #303133;">工作网内部访问节点端</span>
        </div>
        <div class="header-right">
          <el-tag type="success" effect="dark" style="margin-right: 15px;">{{ role }}</el-tag>
          <span style="margin-right: 20px; font-weight: bold">{{ username }}</span>
          <el-button type="danger" size="small" @click="handleLogout">安全登出</el-button>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
  <div v-else>
    <router-view />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DataBoard, Tickets, Warning, Document } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const username = ref(localStorage.getItem('username'))
const role = ref(localStorage.getItem('role'))

watch(() => route.path, () => {
  username.value = localStorage.getItem('username')
  role.value = localStorage.getItem('role')
})

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  localStorage.removeItem('username')
  router.push('/login')
}
</script>

<style>
body { margin: 0; font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "微软雅黑", Arial, sans-serif; background-color: #f0f2f5; }
.app-container { height: 100vh; }
.aside-menu { background-color: #304156; display: flex; flex-direction: column; }
.logo { height: 60px; line-height: 60px; text-align: center; color: white; font-size: 18px; font-weight: bold; background: #2b3643; box-shadow: 0 1px 4px rgba(0,21,41,.08); }
.app-header { background-color: #fff; box-shadow: 0 1px 4px rgba(0,21,41,.08); display: flex; justify-content: space-between; align-items: center; z-index: 10;}
.header-right { display: flex; align-items: center; }
.el-main { background-color: #f0f2f5; padding: 20px; }
</style>
