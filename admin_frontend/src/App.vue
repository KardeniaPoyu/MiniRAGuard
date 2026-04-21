<template>
  <el-container class="app-container" v-if="$route.name !== 'Login' && $route.name !== 'LeadSubmission'">
    <el-aside width="240px" class="aside-menu">
      <div class="logo">
        <span class="logo-text">数律智检</span>
      </div>
      <el-menu
        router
        :default-active="$route.path"
        background-color="#001529"
        text-color="#ffffffb3"
        active-text-color="#ffffff"
        class="custom-menu"
      >
        <div class="menu-group-title">首页</div>
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <span>多维治理大屏</span>
        </el-menu-item>
        <el-menu-item index="/warnings">
          <el-icon><Warning /></el-icon>
          <span>风险预警中心</span>
        </el-menu-item>
        <el-menu-item index="/cases">
          <el-icon><Tickets /></el-icon>
          <span>协同跟进台账</span>
        </el-menu-item>
        <el-menu-item index="/audit">
          <el-icon><Document /></el-icon>
          <span>安全审计日志</span>
        </el-menu-item>

        <div class="menu-group-title">其他</div>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </el-menu-item>
        <el-menu-item index="/security">
          <el-icon><Lock /></el-icon>
          <span>安全</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <span class="header-title">工作网内部访问节点端</span>
        </div>
        <div class="header-right">
          <div class="user-profile">
            <el-icon class="user-icon"><User /></el-icon>
            <span class="username">{{ displayName }}</span>
            <el-tag size="small" effect="plain" class="role-tag">{{ roleName }}</el-tag>
          </div>
          <el-divider direction="vertical" />
          <el-button link class="logout-btn" @click="handleLogout">安全登出</el-button>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
  <div v-else>
    <router-view />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DataBoard, Tickets, Warning, Document, Setting, Lock, User } from '@element-plus/icons-vue'
import { ElNotification } from 'element-plus'
import api from './api'

const route = useRoute()
const router = useRouter()

const username = ref(localStorage.getItem('username'))
const realName = ref(localStorage.getItem('real_name'))
const role = ref(localStorage.getItem('role'))

const displayName = computed(() => realName.value || username.value || '未知用户')

const roleName = computed(() => {
  const mapping = {
    'admin': '管理员',
    'procurator': '检察官',
    'director': '部门负责人',
    'observer': '观察员',
    '管理员': '管理员',
    '检察官': '检察官',
    '部门负责人': '部门负责人',
    '观察员': '观察员'
  }
  return mapping[role.value] || role.value || '未知角色'
})

let pollTimer = null

const checkNotifications = async () => {
  if (!username.value || !role.value) return;
  try {
    const res = await api.getUnreadNotifications();
    if (res.data && res.data.length > 0) {
      res.data.forEach(n => {
        ElNotification({
          title: '🚨 业务预警通知',
          message: n.message,
          type: 'warning',
          duration: 0 // Require manual close
        })
      });
      // Mark as read after showing
      await api.markNotificationsRead();
    }
  } catch (e) {
    // silently fail
  }
}

onMounted(() => {
  if (username.value) checkNotifications();
  pollTimer = setInterval(checkNotifications, 5000);
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
})

watch(() => route.path, () => {
  username.value = localStorage.getItem('username')
  realName.value = localStorage.getItem('real_name')
  role.value = localStorage.getItem('role')
})

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  localStorage.removeItem('username')
  localStorage.removeItem('real_name')
  router.push('/login')
}
</script>

<style>
:root {
  --sidebar-bg: #001529;
  --header-bg: #ffffff;
  --main-bg: #f5f7fa;
  --accent-color: #1890ff;
  --text-primary: #303133;
  --text-regular: #606266;
  --text-secondary: #909399;
}

body {
  margin: 0;
  font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
  background-color: var(--main-bg);
  -webkit-font-smoothing: antialiased;
}

.app-container {
  height: 100vh;
}

/* Sidebar Styling */
.aside-menu {
  background-color: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 8px rgba(0, 21, 41, 0.08);
  z-index: 100;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  background: #002140;
}

.logo-text {
  color: white;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.custom-menu {
  border-right: none !important;
  flex: 1;
}

.menu-group-title {
  padding: 24px 24px 8px;
  font-size: 12px;
  color: #ffffff66;
  letter-spacing: 1px;
}

.el-menu-item {
  height: 50px !important;
  line-height: 50px !important;
  margin: 4px 0;
}

.el-menu-item.is-active {
  background-color: var(--accent-color) !important;
}

/* Header Styling */
.app-header {
  background-color: var(--header-bg);
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  z-index: 10;
}

.header-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: 4px;
  background: #f8f9fb;
  margin-right: 12px;
}

.user-icon {
  font-size: 16px;
  color: var(--text-secondary);
}

.username {
  font-size: 14px;
  color: var(--text-primary);
}

.role-tag {
  border-radius: 2px;
  background-color: #fff;
  color: var(--text-secondary);
  border-color: #dcdfe6;
}

.logout-btn {
  color: var(--text-secondary) !important;
  font-size: 14px !important;
}

.logout-btn:hover {
  color: var(--accent-color) !important;
}

.main-content {
  background-color: var(--main-bg);
  padding: 24px;
}
</style>
