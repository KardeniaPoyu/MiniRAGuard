<template>
  <div class="security-container">
    <el-page-header @back="$router.go(-1)" title="安全中心" content="账号保护与身份审计" />

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="16">
        <el-card header="修改登录密码">
          <el-form :model="passForm" label-width="120px" style="max-width: 460px">
            <el-form-item label="原密码" required>
              <el-input v-model="passForm.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" required>
              <el-input v-model="passForm.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认新密码" required>
              <el-input v-model="passForm.confirm_password" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="danger" @click="changePassword" :loading="loading">立即更新密码</el-button>
            </el-form-item>
          </el-form>
          <div class="pass-tips">
            <p><el-icon><InfoFilled /></el-icon> 提示：建议密码包含字母与数字，且长度不少于 8 位。</p>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card header="当前身份信息">
          <div class="user-info">
            <div class="info-item">
              <span class="label">账户名：</span>
              <span class="value">{{ username }}</span>
            </div>
            <div class="info-item">
              <span class="label">真实姓名：</span>
              <span class="value">{{ realName }}</span>
            </div>
            <div class="info-item">
              <span class="label">权限角色：</span>
              <el-tag>{{ role }}</el-tag>
            </div>
          </div>
          <el-divider />
          <div class="security-level">
            <p>安全等级：<span class="level-text" style="color: #67c23a">高</span></p>
            <el-progress :percentage="100" status="success" />
          </div>
        </el-card>

        <el-card header="二要素增强 (演示)" style="margin-top: 20px">
          <el-switch v-model="mfaEnabled" active-text="开启 USB Key 硬件验签" />
          <p class="mfa-desc">开启后，在线索协同工单签发时需插入硬件盾。</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import api from '../api'

const username = ref(localStorage.getItem('username'))
const realName = ref(localStorage.getItem('real_name') || '未录入')
const role = ref(localStorage.getItem('role'))
const loading = ref(false)
const mfaEnabled = ref(false)

const passForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const changePassword = async () => {
  if (!passForm.old_password || !passForm.new_password) {
    return ElMessage.warning('请填写完整密码信息')
  }
  if (passForm.new_password !== passForm.confirm_password) {
    return ElMessage.error('两次输入的新密码不一致')
  }
  if (passForm.new_password.length < 6) {
    return ElMessage.error('新密码长度至少需要 6 位')
  }

  loading.value = true
  try {
    await api.changePassword(passForm.old_password, passForm.new_password)
    ElMessageBox.alert('密码修改成功，请重新登录。', '提示', {
      confirmButtonText: '确定',
      callback: () => {
        localStorage.clear()
        window.location.href = '/login'
      }
    })
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '修改失败，请检查原密码是否正确')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.security-container {
  padding: 20px;
}
.user-info .info-item {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
}
.user-info .label {
  color: #909399;
  width: 80px;
}
.user-info .value {
  font-weight: 600;
  color: #303133;
}
.pass-tips {
  margin-top: 20px;
  color: #909399;
  font-size: 13px;
}
.mfa-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 10px;
}
.level-text {
  font-weight: 700;
}
</style>
