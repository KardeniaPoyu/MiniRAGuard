<template>
  <el-card header="协同跟进台账">
    <el-tabs v-model="activeName">
      <el-tab-pane label="流转中协同工单" name="processing">
        <el-table :data="processingClues" style="width: 100%">
          <el-table-column prop="title" label="案件摘要" min-width="150" />
          <el-table-column prop="enterprise_name" label="涉案企业" width="150" />
          <el-table-column prop="case_type" label="定性" width="120" />
          <el-table-column label="协同进度" width="300">
            <template #default="scope">
               <div v-for="task in scope.row.tasks" :key="task.id" style="border:1px solid #EBEEF5; padding:8px; margin-bottom:8px; border-radius:4px; background:#fafafa;">
                  <div style="font-weight:bold; color:#409EFF">目标: {{task.to_dept}}</div>
                  <div style="font-size:12px; color:#909399;">状态: {{task.status}}</div>
                  <div v-if="task.status==='待签收' && (role === '检察官' || role === '管理员')">
                    <el-button type="primary" size="small" style="margin-top:5px" @click="openFeedback(scope.row.id, task.id)">模拟外部单位回传结果</el-button>
                  </div>
                  <div v-else-if="task.status!=='待签收'" style="margin-top:5px; border-top: 1px dashed #dcdfe6; padding-top:5px;">
                    <div style="font-size:13px;"><span style="color: #67C23A; font-weight:bold">回函:</span> {{task.feedback_content}}</div>
                    <div v-if="task.feedback_images && task.feedback_images.length" style="color:#E6A23C; font-size:11px;">
                       已挂载凭证码: {{task.feedback_images.join(', ')}}
                    </div>
                  </div>
               </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-button type="info" size="small" @click="handleResolve(scope.row.id)" v-if="role !== '观察员' && scope.row.status !== '已结案'">完结归档</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="feedbackDialogVisible" title="行政单位证据与反馈回传" width="400px">
      <el-form :model="feedbackForm">
        <el-form-item label="办理结果"><el-input v-model="feedbackForm.feedback" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="证据凭证码"><el-input v-model="evidenceStr" placeholder="例如: EV-1234, 模拟获取电子签章" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="feedbackDialogVisible=false">取消</el-button>
        <el-button type="primary" @click="submitFeedback">回传</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const activeName = ref('processing')
const processingClues = ref([])
const role = ref(localStorage.getItem('role'))

const feedbackDialogVisible = ref(false)
const currentTaskId = ref(null)
const evidenceStr = ref('')
const feedbackForm = reactive({ feedback: '' })

const fetchData = async () => {
  const res = await api.listClues({ status: '流转中' })
  processingClues.value = res.data
}

const openFeedback = (clue_id, task_id) => {
  currentTaskId.value = clue_id // Use clue_id for synergyReply
  feedbackForm.feedback = '行政强制命令已依法送达并履约'
  evidenceStr.value = 'E-Doc-99881'
  feedbackDialogVisible.value = true
}

const submitFeedback = async () => {
  try {
    await api.synergyReply(currentTaskId.value, { 
      feedback: feedbackForm.feedback, 
      evidence_urls: [evidenceStr.value] 
    })
    ElMessage.success("外部单位协同回执已入库")
    feedbackDialogVisible.value = false
    fetchData()
  } catch(e) {
    ElMessage.error(e.response?.data?.detail || '暂无权限或回复失败')
  }
}

const handleResolve = async (clue_id) => {
  try {
    await api.resolveClue(clue_id)
    ElMessage.success('案件已依法完结归档')
    fetchData()
  } catch(e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

onMounted(() => fetchData())
</script>
