<template>
  <div class="login-wrapper">
    <div class="login-box">
      <div class="logo-box">
        <el-icon :size="48" color="#40a9ff"><Box /></el-icon>
        <h2>数律智检</h2>
      </div>
      <el-form :model="form" @submit.prevent="handleLogin" class="login-form">
        <el-form-item>
          <el-input v-model="form.username" placeholder="请输入用户名" size="large" prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="请输入口令" size="large" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-button type="primary" native-type="submit" size="large" class="login-btn" :loading="loading">
          安全登入
        </el-button>
      </el-form>
      <div class="tips">测试账号: admin/admin123, procurator/proc123, observer/obs123</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Box } from '@element-plus/icons-vue'
import api from '../api'

const router = useRouter()
const form = reactive({ username: '', password: '' })
const loading = ref(false)

const handleLogin = async () => {
  if (!form.username || !form.password) return ElMessage.warning('请输入凭证')
  loading.value = true
  try {
    const res = await api.login(form.username, form.password)
    localStorage.setItem('token', res.data.access_token)
    
    // 获取用户身份
    const meRes = await api.getMe()
    localStorage.setItem('username', meRes.data.username)
    localStorage.setItem('role', meRes.data.role)
    
    ElMessage.success(`欢迎回来，${meRes.data.role}`)
    router.push('/')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '登录失败，请检查口令')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #4f6bff 0%, #29388c 100%);
  position: relative;
  overflow: hidden;
}
.login-wrapper::before {
  content: '';
  position: absolute;
  top: -20%; left: -10%;
  width: 50%; height: 50%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 70%);
}
.login-box {
  width: 380px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  box-shadow: 0 15px 35px rgba(0,0,0,0.2);
  transform: translateY(-20px);
}
.logo-box {
  text-align: center;
  margin-bottom: 30px;
}
.logo-box h2 {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', sans-serif;
  color: #303133;
  margin-top: 15px;
  letter-spacing: 1px;
}
.login-btn {
  width: 100%;
  font-size: 16px;
  border-radius: 8px;
  background: linear-gradient(90deg, #409EFF, #3a8ee6);
  border: none;
}
.login-btn:hover {
  background: linear-gradient(90deg, #66b1ff, #53a8ff);
}
.tips {
  margin-top: 15px;
  font-size: 12px;
  color: #909399;
  text-align: center;
}
</style>
