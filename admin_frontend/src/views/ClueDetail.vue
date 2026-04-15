<template>
  <div v-if="clue">
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card header="线索详情">
          <el-descriptions border :column="2">
            <el-descriptions-item label="标题" :span="2">{{ clue.title }}</el-descriptions-item>
            <el-descriptions-item label="来源">{{ clue.source }}</el-descriptions-item>
            <el-descriptions-item label="领域">{{ clue.domain }}</el-descriptions-item>
            <el-descriptions-item label="当前状态">
              <el-tag type="info">{{ clue.status }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="风险等级" v-if="clue.risk_level">
              <el-tag type="danger" v-if="clue.risk_level === '高风险'">高风险</el-tag>
              <el-tag type="warning" v-else-if="clue.risk_level === '中风险'">中风险</el-tag>
              <el-tag type="success" v-else>低风险</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="详细内容" :span="2">
              <div style="white-space: pre-wrap">{{ clue.content }}</div>
            </el-descriptions-item>
            <el-descriptions-item label="AI 摘要" :span="2" v-if="clue.risk_summary">
              {{ clue.risk_summary }}
            </el-descriptions-item>
          </el-descriptions>
          <div style="margin-top: 20px" v-if="clue.status === '待研判'">
            <el-button type="primary" @click="handleJudge" :loading="judging">触发 AI 研判</el-button>
          </div>
        </el-card>

        <el-card header="AI 研判建议" style="margin-top: 20px" v-if="clue.risk_detail">
          <div v-for="(factor, idx) in (clue.risk_detail.risk_factors || [])" :key="idx" style="margin-bottom:10px; border:1px solid #EBEEF5; padding:10px; border-radius:4px;">
            <div style="font-weight:bold">{{ factor.factor }} <el-tag size="small" type="danger" v-if="factor.severity==='高'">高危</el-tag></div>
            <div style="font-size:14px; margin: 5px 0">{{ factor.description }}</div>
            <div style="font-size:12px; color:#606266">依据：{{ factor.legal_basis }}</div>
          </div>
          <div style="margin-top:20px; font-weight:bold">
            💡 处置建议：{{ clue.risk_detail.recommended_action }} <br/>
            ⏰ 紧急程度：{{ clue.risk_detail.urgency }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card header="处置流程">
          <div v-if="clue.status === '已研判'">
            <el-input v-model="pushDept" placeholder="输入推送部门" style="margin-bottom:10px;" />
            <el-button type="primary" style="width:100%" @click="handlePush">推送</el-button>
          </div>
          <div v-if="clue.status === '已推送'">
            <el-input v-model="feedback" type="textarea" placeholder="填写办结结果" style="margin-bottom:10px;" />
            <el-button type="success" style="width:100%" @click="handleResolve">标记办结</el-button>
          </div>
          <div v-if="clue.status === '已办结'" style="color:#67C23A; font-weight:bold; text-align:center;">
             ✓ 该线索已办结
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

const route = useRoute()
const clue = ref(null)
const judging = ref(false)
const pushDept = ref('')
const feedback = ref('')

const loadClue = async () => {
  const res = await api.getClue(route.params.id)
  clue.value = res.data
}

const handleJudge = async () => {
  judging.value = true
  await api.judgeClue(route.params.id)
  ElMessage.success('研判完成')
  await loadClue()
  judging.value = false
}

const handlePush = async () => {
  await api.pushClue(route.params.id, pushDept.value)
  ElMessage.success('推送成功')
  await loadClue()
}

const handleResolve = async () => {
  await api.resolveClue(route.params.id, feedback.value)
  ElMessage.success('办结成功')
  await loadClue()
}

onMounted(() => loadClue())
</script>
