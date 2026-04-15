<template>
  <div v-if="clue">
    <el-row :gutter="20">
      <el-col :span="14">
        <!-- 基础案卷卷宗 -->
        <el-card header="电子卷宗">
          <el-descriptions border :column="2">
            <el-descriptions-item label="企业名称" :span="2">
               <span style="font-weight:bold">{{ clue.enterprise_name }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="涉案人数">{{ clue.personnel_count }}</el-descriptions-item>
            <el-descriptions-item label="标的金额">￥{{ clue.amount }}</el-descriptions-item>
            <el-descriptions-item label="原件内容" :span="2">
              <div style="white-space: pre-wrap; background:#f5f7fa; padding:10px; border-radius:4px;">{{ clue.content }}</div>
            </el-descriptions-item>
            <el-descriptions-item label="预警结论" :span="2">
              <el-tag :type="clue.alert_level==='红色预警'?'danger':(clue.alert_level==='黄色预警'?'warning':'primary')">
                {{clue.alert_level}}
              </el-tag>
              <div style="margin-top:10px;" v-for="(f, i) in clue.alert_factors" :key="i">
                - {{ f.desc }}
              </div>
            </el-descriptions-item>
          </el-descriptions>
          <div style="margin-top: 20px" v-if="clue.status === '待研判'">
            <el-button type="primary" size="large" @click="handleJudge" :loading="judging">提取证据并进行 AI 智能定性分流</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="10">
        <!-- 研判意见与处理建议 -->
        <el-card v-if="clue.risk_detail" header="检察监督定性及处置建议">
          <div style="font-size:20px; font-weight:bold; margin-bottom:15px; color:#409EFF">
            案管分流锚定：{{ clue.risk_detail.case_type }}
          </div>
          <div v-for="(factor, idx) in (clue.risk_detail.risk_factors || [])" :key="idx" style="margin-bottom:10px; border-left:3px solid #F56C6C; padding:10px; background:#fffaf0;">
            <div style="font-weight:bold">{{ factor.factor }}</div>
            <div style="font-size:14px; margin: 5px 0">{{ factor.description }}</div>
            <div style="font-size:12px; color:#909399">依据：{{ factor.legal_basis }}</div>
          </div>
          <el-divider />
          <div style="font-weight:bold; margin-bottom:10px;">智能草拟检察建议/移送信：</div>
          <el-input type="textarea" :rows="5" v-model="clue.risk_detail.procuratorial_advice" />
          
          <div style="margin-top:20px;">
            <div style="font-weight:bold; margin-bottom:10px;">发起跨单位协同流转：</div>
            <el-select v-model="pushDept" style="width:100%; margin-bottom:10px;" placeholder="选择推送单位">
              <el-option label="人力资源与社会保障局(劳动仲裁委)" value="人社局" />
              <el-option label="住房和城乡建设委员会" value="住建委" />
              <el-option label="公安局(拒不支付劳动报酬移送)" value="公安局" />
            </el-select>
            <el-button type="success" style="width:100%" @click="handlePush">核定签发协同工单</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

const route = useRoute()
const router = useRouter()
const clue = ref(null)
const judging = ref(false)
const pushDept = ref('')

const loadClue = async () => {
  const res = await api.getClue(route.params.id)
  clue.value = res.data
}

const handleJudge = async () => {
  judging.value = true
  await api.judgeClue(route.params.id)
  ElMessage.success('AI 已进行定性分流')
  await loadClue()
  judging.value = false
}

const handlePush = async () => {
  if(!pushDept.value) return ElMessage.warning('请选择单位')
  await api.pushTask(route.params.id, { 
    to_dept: pushDept.value, 
    req_content: clue.value.risk_detail.procuratorial_advice || "请核查此线索" 
  })
  ElMessage.success('工单已派发至政法/行政网')
  router.push('/cases')
}

onMounted(() => loadClue())
</script>
