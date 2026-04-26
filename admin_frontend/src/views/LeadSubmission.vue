<template>
  <div class="portal-container">
    <div class="portal-header">
      <div class="logo-area">
        <el-icon :size="40" color="#fff"><Box /></el-icon>
        <div class="title-text">
          <h1>数律智检</h1>
          <p>基层检察协同与法律线索录入平台</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button link type="primary" style="color: white" @click="$router.push('/login')">检察官登录</el-button>
      </div>
    </div>

    <el-main class="portal-content">
      <el-row :gutter="40" justify="center">
        <!-- 左侧：线索录入表单 -->
        <el-col :xs="24" :sm="24" :md="12">
          <el-card class="form-card" shadow="always">
            <template #header>
              <div class="card-title">
                <el-icon><EditPen /></el-icon>
                <span>录入法律监督线索</span>
              </div>
            </template>

            <el-form :model="form" label-position="top">
              <el-form-item label="线索标题" required>
                <el-input v-model="form.title" placeholder="请简洁描述线索内容（如：某企业拖欠工资）" />
              </el-form-item>

              <el-row :gutter="20">
                <el-col :span="14">
                  <el-form-item label="涉及单位/企业">
                    <el-input v-model="form.enterprise_name" placeholder="请输入单位全称" />
                  </el-form-item>
                </el-col>
                <el-col :span="10">
                  <el-form-item label="涉及人数">
                    <el-input-number v-model="form.personnel_count" :min="1" style="width: 100%" />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item label="涉案总金额 (元)">
                <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%" />
              </el-form-item>

              <el-form-item label="详情诉求" required>
                <el-input
                  v-model="form.content"
                  type="textarea"
                  :rows="6"
                  placeholder="请详细描述事情经过、时间、地点及具体诉求..."
                />
              </el-form-item>

              <el-form-item label="证据上传">
                <el-upload
                  action="#"
                  list-type="picture-card"
                  :auto-upload="false"
                  :on-change="handleImageChange"
                  :file-list="fileList"
                  multiple
                >
                  <el-icon><Plus /></el-icon>
                  <template #tip>
                    <div class="upload-tip">支持上传工资条、欠条、劳动合同照片或截图</div>
                  </template>
                </el-upload>
              </el-form-item>

              <div class="submit-area">
                <el-button type="primary" size="large" :loading="loading" @click="submitLead" class="submit-btn">
                  提交并获取法律评估
                </el-button>
              </div>
            </el-form>
          </el-card>
        </el-col>

        <!-- 右侧：AI 预研判结果 -->
        <el-col :xs="24" :sm="24" :md="12">
          <div v-if="!analysisResult && !loading" class="intro-box">
            <el-empty description="提交线索后，AI 将为您提供初步法律定性分析及权利告知" />
            <div class="guide-list">
              <div class="guide-item">
                <el-icon color="#409eff"><InfoFilled /></el-icon>
                <span><strong>一键提交</strong>：线索将直接进入基层检察室预警库</span>
              </div>
              <div class="guide-item">
                <el-icon color="#67c23a"><Promotion /></el-icon>
                <span><strong>多方协同</strong>：依托行政执法与刑事司法衔接机制处理</span>
              </div>
              <div class="guide-item">
                <el-icon color="#e6a23c"><Checked /></el-icon>
                <span><strong>隐私保护</strong>：所有举报信息均受到严格保密</span>
              </div>
            </div>
          </div>

          <div v-if="loading" class="loading-box">
            <el-skeleton :rows="10" animated />
            <p class="loading-text">数律 AI 正在根据法典检索相关依据并进行研判...</p>
          </div>

          <div v-if="analysisResult" class="result-area">
            <el-card class="result-card" :class="riskClass(analysisResult.overall_risk)">
              <div class="result-header">
                <div class="risk-badge">{{ analysisResult.overall_risk }}</div>
                <h3>初步法律研判结论</h3>
              </div>
              
              <div class="result-body">
                <p class="summary">{{ analysisResult.summary }}</p>
                
                <el-divider content-position="left">法律定性与风险点</el-divider>
                <div 
                  v-for="(item, idx) in analysisResult.analysis_results" 
                  :key="idx"
                  class="risk-point"
                >
                  <div class="point-header">
                    <span class="point-type">{{ item.risk_type }}</span>
                    <el-tag :type="tagType(item.risk_level)" size="small">{{ item.risk_level }}</el-tag>
                  </div>
                  <p class="point-reason">{{ item.reason }}</p>
                  <p class="point-legal" v-if="item.legal_basis">
                    依据：<span class="law-tag">{{ item.legal_basis }}</span>
                  </p>
                </div>

                <div class="advice-box">
                  <h4>💡 法律引导与建议</h4>
                  <p v-for="(item, idx) in analysisResult.analysis_results" :key="'adv'+idx">
                    {{ item.advice }}
                  </p>
                  <p class="procurator-tip">您的线索已存入预警池，检察机关将在 1-3 个工作日内进行核查。</p>
                </div>
              </div>
            </el-card>
          </div>
        </el-col>
      </el-row>
    </el-main>

    <footer class="portal-footer">
      <p>数律智检 - 检察机关法律监督线索智能辅助平台</p>
      <p class="copyright">&copy; 2026 XX人民检察院 | 数字化检察工作室 技术支持</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { Box, EditPen, Plus, InfoFilled, Promotion, Checked } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const loading = ref(false)
const analysisResult = ref(null)
const fileList = ref([])

const form = reactive({
  title: '',
  enterprise_name: '',
  personnel_count: 1,
  amount: 0,
  content: '',
  images: []
})

const handleImageChange = (file, files) => {
  fileList.value = files
}

const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => resolve(reader.result.split(',')[1])
    reader.onerror = error => reject(error)
  })
}

const submitLead = async () => {
  if (!form.title || !form.content) {
    return ElMessage.warning('请填写标题和详细诉求')
  }

  loading.value = true
  analysisResult.value = null

  try {
    // 1. 处理图片
    const base64Images = await Promise.all(
      fileList.value.map(f => fileToBase64(f.raw))
    )
    
    // 2. 将线索提交至后端进行 AI 研判
    const res = await api.analyze({
      title: form.title,
      enterprise_name: form.enterprise_name,
      personnel_count: form.personnel_count,
      amount: form.amount,
      content: form.content,
      images: base64Images
    })

    analysisResult.value = res.data
    ElMessage.success('提交成功，已完成 AI 初步分类研判')
  } catch (err) {
    console.error(err)
    ElMessage.error(err.response?.data?.detail || '引擎响应异常，请重试')
  } finally {
    loading.value = false
  }
}

const riskClass = (level) => {
  if (level === '高风险') return 'risk-red'
  if (level === '中风险') return 'risk-yellow'
  return 'risk-blue'
}

const tagType = (level) => {
  if (level === '高风险') return 'danger'
  if (level === '中风险') return 'warning'
  return 'success'
}
</script>

<style scoped>
.portal-container {
  min-height: 100vh;
  background-color: #f0f2f5;
  display: flex;
  flex-direction: column;
}

.portal-header {
  background: linear-gradient(90deg, #1d3557 0%, #457b9d 100%);
  padding: 20px 50px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
  box-shadow: 0 2px 10px rgba(0,0,0,0.2);
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 15px;
}

.title-text h1 {
  margin: 0;
  font-size: 28px;
  letter-spacing: 2px;
}

.title-text p {
  margin: 5px 0 0;
  font-size: 14px;
  opacity: 0.8;
}

.portal-content {
  max-width: 1400px;
  margin: 40px auto;
  width: 95%;
  flex: 1;
}

.form-card {
  border-radius: 12px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: #1d3557;
}

.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.submit-area {
  margin-top: 30px;
  text-align: center;
}

.submit-btn {
  width: 80%;
  height: 50px;
  font-size: 18px;
  border-radius: 25px;
}

.intro-box {
  background: white;
  border-radius: 12px;
  padding: 60px 40px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  border: 2px dashed #dcdfe6;
}

.guide-list {
  margin-top: 40px;
  padding: 0 20px;
}

.guide-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  font-size: 15px;
  color: #606266;
}

.loading-box {
  padding: 40px;
  background: white;
  border-radius: 12px;
  text-align: center;
}

.loading-text {
  margin-top: 20px;
  color: #409eff;
  font-weight: 500;
}

/* 结果展示样式 */
.result-card {
  border-radius: 12px;
  border-top: 8px solid;
}

.risk-red { border-top-color: #f56c6c; }
.risk-yellow { border-top-color: #e6a23c; }
.risk-blue { border-top-color: #409eff; }

.result-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
}

.risk-badge {
  padding: 5px 15px;
  border-radius: 4px;
  color: white;
  font-weight: 700;
}

.risk-red .risk-badge { background: #f56c6c; }
.risk-yellow .risk-badge { background: #e6a23c; }
.risk-blue .risk-badge { background: #409eff; }

.summary {
  font-size: 16px;
  line-height: 1.6;
  color: #303133;
  margin-bottom: 20px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
}

.risk-point {
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.point-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.point-type {
  font-weight: 600;
  color: #303133;
}

.point-reason {
  font-size: 14px;
  color: #606266;
  margin: 5px 0;
}

.point-legal {
  font-size: 13px;
  color: #909399;
}

.law-tag {
  color: #409eff;
  font-weight: 500;
}

.advice-box {
  margin-top: 25px;
  padding: 15px;
  background: #f0f7ff;
  border-radius: 8px;
}

.advice-box h4 {
  margin: 0 0 10px;
  color: #1d3557;
}

.advice-box p {
  font-size: 14px;
  line-height: 1.6;
  color: #457b9d;
  margin-bottom: 10px;
}

.procurator-tip {
  margin-top: 15px;
  font-weight: 600;
  color: #1d3557 !important;
}

.portal-footer {
  padding: 30px;
  text-align: center;
  color: #606266;
  font-size: 14px;
  background: #fff;
  border-top: 1px solid #dcdfe6;
}

.copyright {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>
