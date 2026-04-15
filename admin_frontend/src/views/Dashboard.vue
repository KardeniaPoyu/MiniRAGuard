<template>
  <div class="dashboard">
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-title">全域线索总量</div>
          <div class="stat-value">{{ stats.total }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" style="background-color: #fff0f0">
          <div class="stat-title">红色重大预警</div>
          <div class="stat-value text-danger">{{ redAlerts }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" style="background-color: #fffaf0">
          <div class="stat-title">黄色群体预警</div>
          <div class="stat-value text-warning">{{ yellowAlerts }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" style="background-color: #f0f9eb">
          <div class="stat-title">蓝色苗头预警</div>
          <div class="stat-value text-primary">{{ blueAlerts }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="charts-row" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card header="高发涉案企业排行榜 Top 5">
          <el-table :data="stats.hot_enterprises" style="width: 100%">
            <el-table-column type="index" label="排名" width="80" />
            <el-table-column prop="name" label="企业/工程名称" />
            <el-table-column prop="count" label="被诉次数" width="100">
               <template #default="s"><el-tag type="danger">{{ s.row.count }}次</el-tag></template>
            </el-table-column>
            <el-table-column prop="personnel" label="关联人数" width="100" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="线索办理状态分布">
          <div ref="pieChart" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import api from '../api'

const stats = ref({ total: 0, status_distribution: {}, alert_distribution: {}, hot_enterprises: [] })
const pieChart = ref(null)

const redAlerts = computed(() => stats.value.alert_distribution['红色预警'] || 0)
const yellowAlerts = computed(() => stats.value.alert_distribution['黄色预警'] || 0)
const blueAlerts = computed(() => stats.value.alert_distribution['蓝色预警'] || 0)

const renderCharts = () => {
  const echarts = window.echarts
  if (!echarts || !pieChart.value) return

  const pie = echarts.init(pieChart.value)
  const pieData = Object.entries(stats.value.status_distribution || {}).map(([name, value]) => ({ name, value }))
  pie.setOption({
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', left: 'left' },
    series: [{ name: '当前状态', type: 'pie', radius: '60%', data: pieData }]
  })

  window.addEventListener('resize', pie.resize)
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
.stat-title { font-size: 14px; color: #606266; margin-bottom: 10px; }
.stat-value { font-size: 28px; font-weight: bold; }
.text-danger { color: #F56C6C; }
.text-warning { color: #E6A23C; }
.text-primary { color: #409EFF; }
.chart-box { height: 300px; }
</style>
