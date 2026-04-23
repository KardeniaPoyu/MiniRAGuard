<template>
  <div class="settings-container">
    <el-page-header @back="$router.go(-1)" title="系统设置" content="平台参数与算法配置" />

    <el-tabs v-model="activeTab" class="settings-tabs">
      <!-- 平台配置 -->
      <el-tab-pane label="平台基础信息" name="base">
        <el-card shadow="never">
          <el-form :model="configForm" label-width="140px" style="max-width: 600px">
            <el-form-item label="系统显示名称">
              <el-input v-model="configForm.system_name" />
            </el-form-item>
            <el-form-item label="所属单位全称">
              <el-input v-model="configForm.dept_name" />
            </el-form-item>
            <el-form-item v-if="role === 'admin'">
              <el-button type="primary" @click="saveSettings">保存基础信息</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 预警规则 -->
      <el-tab-pane label="预警阈值管理" name="rules">
        <el-card shadow="never">
          <div class="alert-info">
            <el-alert title="算法说明" type="info" description="系统将根据此处设置的金额自动判定线索的预警等级（红色/黄色）。" show-icon :closable="false" />
          </div>
          <el-form :model="configForm" label-width="140px" style="max-width: 500px; margin-top: 20px">
            <el-form-item label="红色预警阈值 (元)">
              <el-input-number v-model="configForm.red_alert_threshold" :min="1" />
              <div class="form-tip">涉及金额大于等于此值时触发最高等级预警</div>
            </el-form-item>
            <el-form-item label="黄色预警阈值 (元)">
              <el-input-number v-model="configForm.yellow_alert_threshold" :min="1" />
              <div class="form-tip">涉及金额介于黄色与红色阈值之间时触发</div>
            </el-form-item>
            <el-form-item v-if="role === 'admin'">
              <el-button type="warning" @click="saveSettings">更新研判算法参数</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 算法模型 -->
      <el-tab-pane label="AI 研判模型" name="ai">
        <el-card shadow="never">
          <el-form :model="configForm" label-width="140px" style="max-width: 600px">
            <el-form-item label="当前研判引擎">
              <el-select v-model="configForm.ai_model" disabled>
                <el-option label="DeepSeek-V3 (推荐)" value="deepseek-chat" />
              </el-select>
            </el-form-item>
            <el-form-item label="API 密钥状态">
              <div class="api-key-info">
                <el-tag :type="apiInfo.has_key ? 'success' : 'danger'" size="small">
                  {{ apiInfo.has_key ? '已配置' : '未配置' }}
                </el-tag>
                <span class="masked-key" v-if="apiInfo.has_key">{{ apiInfo.masked_key }}</span>
                <el-button type="primary" link @click="showKeyDialog = true" style="margin-left: 12px">
                  更新密钥
                </el-button>
              </div>
            </el-form-item>
            <el-form-item label="RAG 检索深度">
              <el-slider v-model="ragDepth" :max="10" :min="1" />
              <div class="form-tip">控制 AI 检索相关法条的关联数量</div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- API Key Update Dialog -->
    <el-dialog v-model="showKeyDialog" title="更新 DeepSeek API 密钥" width="450px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="新的 API 密钥">
          <el-input v-model="newApiKey" placeholder="sk-..." type="password" show-password />
          <div class="form-tip">密钥仅保存在本地设备，不会上传至业务服务器。</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showKeyDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateKey" :loading="updatingKey">保存并生效</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const activeTab = ref('base')
const role = ref(localStorage.getItem('role'))
const ragDepth = ref(5)

const showKeyDialog = ref(false)
const newApiKey = ref('')
const updatingKey = ref(false)
const apiInfo = reactive({
  has_key: false,
  masked_key: ''
})

const configForm = reactive({
  system_name: '',
  dept_name: '',
  red_alert_threshold: 100000,
  yellow_alert_threshold: 10000,
  ai_model: 'deepseek-chat'
})

const fetchSettings = async () => {
  try {
    const res = await api.getSettings()
    Object.keys(res.data).forEach(key => {
      if (key in configForm) {
        configForm[key] = isNaN(res.data[key]) ? res.data[key] : Number(res.data[key])
      }
    })
    fetchConfigInfo()
  } catch (e) {
    ElMessage.error('无法同步服务器配置')
  }
}

const fetchConfigInfo = async () => {
  try {
    const res = await api.getConfigInfo()
    apiInfo.has_key = res.data.has_key
    apiInfo.masked_key = res.data.masked_key
  } catch (e) {
    console.error('Failed to fetch config info', e)
  }
}

const handleUpdateKey = async () => {
  if (!newApiKey.value.trim().startsWith('sk-')) {
    return ElMessage.warning('API 密钥格式不正确')
  }
  updatingKey.value = true
  try {
    const res = await api.updateApiKey(newApiKey.value.trim())
    ElMessage.success(res.data.message || 'API 密钥更新成功')
    showKeyDialog.value = false
    newApiKey.value = ''
    fetchConfigInfo()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '更新失败')
  } finally {
    updatingKey.value = false
  }
}

const saveSettings = async () => {
  if (role.value !== 'admin') {
    return ElMessage.error('权限不足：仅管理员可修改配置')
  }
  try {
    await api.updateSettings(configForm)
    ElMessage.success('系统配置已生效')
    fetchSettings()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

onMounted(fetchSettings)
</script>

<style scoped>
.settings-container {
  padding: 20px;
}
.settings-tabs {
  margin-top: 20px;
}
.api-key-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.masked-key {
  font-family: monospace;
  color: #606266;
  font-size: 13px;
  background: #f4f4f5;
  padding: 2px 6px;
  border-radius: 4px;
}
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
.alert-info {
  margin-bottom: 20px;
}
</style>
