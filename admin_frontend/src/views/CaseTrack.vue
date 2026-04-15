<template>
  <el-card header="协同跟进台账">
    <el-tabs v-model="activeName">
      <el-tab-pane label="流转中协同工单" name="processing">
        <el-table :data="processingClues" style="width: 100%">
          <el-table-column prop="title" label="案件摘要" min-width="150" />
          <el-table-column prop="enterprise_name" label="涉案企业" width="150" />
          <el-table-column prop="case_type" label="定性" width="120" />
          <el-table-column label="工单进度" width="300">
            <template #default="scope">
               <div v-for="task in scope.row.tasks" :key="task.id" style="border:1px solid #EBEEF5; padding:5px; margin-bottom:5px;">
                  发送至: <b>{{task.to_dept}}</b> [{{task.status}}]<br/>
                  <div v-if="task.status==='待签收'">
                    <el-button type="primary" size="small" @click="openFeedback(scope.row.id, task.id)">模拟外部单位回传结果</el-button>
                  </div>
                  <div v-else>
                    <span style="color: #67C23A">回传: {{task.feedback}}</span>
                  </div>
               </div>
            </template>
          </el-table-column>
          <el-table-column label="闭环操作" width="120">
            <template #default="scope">
              <el-button type="success" size="small" @click="handleResolve(scope.row.id)">完结归档</el-button>
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

const feedbackDialogVisible = ref(false)
const currentTaskId = ref(null)
const evidenceStr = ref('')
const feedbackForm = reactive({ feedback: '' })

const fetchData = async () => {
  const res = await api.listClues({ status: '流转中' })
  processingClues.value = res.data
}

const openFeedback = (clue_id, task_id) => {
  currentTaskId.value = task_id
  feedbackForm.feedback = '行政强制命令已依法送达并履约'
  evidenceStr.value = 'E-Doc-99881'
  feedbackDialogVisible.value = true
}

const submitFeedback = async () => {
  await api.feedbackTask(currentTaskId.value, { 
    feedback: feedbackForm.feedback, 
    evidence_urls: [evidenceStr.value] 
  })
  ElMessage.success("数据共享网回传成功")
  feedbackDialogVisible.value = false
  fetchData()
}

const handleResolve = async (clue_id) => {
  await api.resolveClue(clue_id)
  ElMessage.success('案件已合规结案')
  fetchData()
}

onMounted(() => fetchData())
</script>
