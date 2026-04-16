<template>
  <div class="dashboard">
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="8">
        <el-card shadow="always" class="gradient-card blue">
          <div class="stat-title">总计办结线索</div>
          <div class="stat-value">{{ stats.total }} <span class="unit">件</span></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="always" class="gradient-card green">
          <div class="stat-title">最高频治理领域</div>
          <div class="stat-value">{{ topDomainName }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="always" class="gradient-card purple">
          <div class="stat-title">治理攻坚重灾区</div>
          <div class="stat-value">{{ topEnterpriseName }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="charts-row" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card header="已办结线索领域分布 (专项指标)" shadow="hover">
          <div ref="barChart" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="高发投诉企业排行榜" shadow="hover">
          <el-table :data="stats.hot_enterprises" style="width: 100%" height="300">
            <el-table-column type="index" label="排名" width="60" />
            <el-table-column prop="name" label="涉案企业/主体" />
            <el-table-column prop="count" label="线索计件" width="100">
               <template #default="s"><el-tag type="danger" effect="plain">{{ s.row.count }}件</el-tag></template>
            </el-table-column>
            <el-table-column prop="personnel" label="关联人数" width="100">
               <template #default="s"><span style="font-weight:bold">{{ s.row.personnel }}</span> 人</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import api from '../api'

const stats = ref({ total: 0, domain_distribution: [], case_type_distribution: [], hot_enterprises: [] })
const barChart = ref(null)

const topDomainName = computed(() => {
  if (!stats.value.domain_distribution || stats.value.domain_distribution.length === 0) return '暂无'
  const max = [...stats.value.domain_distribution].sort((a,b) => b.value - a.value)[0]
  return max.name
})

const topEnterpriseName = computed(() => {
  if (!stats.value.hot_enterprises || stats.value.hot_enterprises.length === 0) return '暂无'
  return stats.value.hot_enterprises[0].name
})

const renderCharts = () => {
  const echarts = window.echarts
  if (!echarts || !barChart.value) return

  const bar = echarts.init(barChart.value)
  const xData = (stats.value.domain_distribution || []).map(d => d.name)
  const yData = (stats.value.domain_distribution || []).map(d => d.value)
  
  bar.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value', boundaryGap: [0, 0.01] },
    yAxis: { type: 'category', data: xData },
    series: [
      {
        name: '办结案件量',
        type: 'bar',
        data: yData,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' }
          ])
        }
      }
    ]
  })

  window.addEventListener('resize', bar.resize)
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
.dashboard { padding: 10px; }
.stat-cards { margin-bottom: 20px; }
.gradient-card { color: #fff; border: none; border-radius: 8px; }
.gradient-card.blue { background: linear-gradient(135deg, #1890ff 0%, #36cfc9 100%); }
.gradient-card.green { background: linear-gradient(135deg, #52c41a 0%, #b7eb8f 100%); }
.gradient-card.purple { background: linear-gradient(135deg, #722ed1 0%, #b37feb 100%); }
.stat-title { font-size: 15px; margin-bottom: 12px; opacity: 0.9; }
.stat-value { font-size: 32px; font-weight: bold; }
.unit { font-size: 14px; font-weight: normal; opacity: 0.8; }
.chart-box { height: 300px; width: 100%; }
</style>
