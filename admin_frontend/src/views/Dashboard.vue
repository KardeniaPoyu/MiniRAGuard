<template>
  <div class="dashboard">
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-title">线索总数</div>
          <div class="stat-value">{{ stats.total }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-title">高风险数</div>
          <div class="stat-value text-danger">{{ highRiskCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-title">已推送数</div>
          <div class="stat-value text-primary">{{ pushedCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-title">办结率</div>
          <div class="stat-value text-success">{{ resolvedRate }}%</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="charts-row">
      <el-col :span="12">
        <el-card header="各领域线索分布">
          <div ref="pieChart" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="线索流转漏斗">
          <div ref="funnelChart" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import api from '../api'

const stats = ref({ total: 0, status_distribution: {}, risk_distribution: {}, domain_distribution: {} })
const pieChart = ref(null)
const funnelChart = ref(null)

const highRiskCount = computed(() => stats.value.risk_distribution['高风险'] || 0)
const pushedCount = computed(() => stats.value.status_distribution['已推送'] || 0)
const resolvedCount = computed(() => stats.value.status_distribution['已办结'] || 0)
const resolvedRate = computed(() => {
  if (stats.value.total === 0) return 0
  return ((resolvedCount.value / stats.value.total) * 100).toFixed(1)
})

const renderCharts = () => {
  const echarts = window.echarts
  if (!echarts) return

  // Pie Chart
  const pie = echarts.init(pieChart.value)
  const pieData = Object.entries(stats.value.domain_distribution || {}).map(([name, value]) => ({ name, value }))
  pie.setOption({
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', left: 'left' },
    color: ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399'],
    series: [{ name: '领域分布', type: 'pie', radius: '50%', data: pieData }]
  })

  // Funnel Chart
  const funnel = echarts.init(funnelChart.value)
  funnel.setOption({
    tooltip: { trigger: 'item', formatter: '{a} <br/>{b} : {c}' },
    series: [{
      name: '处置流程', type: 'funnel', left: '10%', top: 60, bottom: 60, width: '80%',
      min: 0, max: stats.value.total === 0 ? 1 : stats.value.total, minSize: '0%', maxSize: '100%',
      sort: 'descending', gap: 2,
      data: [
        { value: stats.value.total, name: '录入线索' },
        { value: stats.value.total - (stats.value.status_distribution['待研判']||0), name: '已研判' },
        { value: pushedCount.value + resolvedCount.value, name: '已推送' },
        { value: resolvedCount.value, name: '已办结' }
      ]
    }]
  })

  window.addEventListener('resize', () => {
    pie.resize()
    funnel.resize()
  })
}

onMounted(async () => {
  try {
    const res = await api.getStats()
    stats.value = res.data
    await nextTick()
    setTimeout(renderCharts, 100)
  } catch (e) {
    console.error("Failed to load stats", e)
  }
})
</script>

<style scoped>
.stat-cards { margin-bottom: 20px; }
.stat-title { font-size: 14px; color: #909399; margin-bottom: 10px; }
.stat-value { font-size: 24px; font-weight: bold; }
.text-danger { color: #F56C6C; }
.text-primary { color: #409EFF; }
.text-success { color: #67C23A; }
.chart-box { height: 350px; }
.charts-row { margin-bottom: 20px; }
</style>
