<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <el-icon class="header-icon"><ShoppingCart /></el-icon>
      <span class="header-text">多维治理大屏</span>
    </div>

    <el-row :gutter="24" class="stat-cards">
      <el-col :span="8">
        <div class="stat-card card-blue">
          <div class="stat-content">
            <div class="stat-title">总计办结线索</div>
            <div class="stat-value">
              <span class="number">{{ stats.total }}</span>
              <span class="unit">件</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card card-light-blue">
          <div class="stat-content">
            <div class="stat-title">最高频治理领域</div>
            <div class="stat-value">
              <span class="text-value">{{ topDomainName }}</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card card-white">
          <div class="stat-content">
            <div class="stat-title">治理攻坚重灾区</div>
            <div class="stat-value">
              <span class="text-value">{{ topEnterpriseName }}</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="24" class="charts-row">
      <el-col :span="12">
        <el-card class="chart-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>已办结线索领域分布（专项指标）</span>
            </div>
          </template>
          <div ref="barChart" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="table-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>高发投诉企业排行榜</span>
            </div>
          </template>
          <el-table :data="stats.hot_enterprises" style="width: 100%" class="custom-table">
            <el-table-column type="index" label="排名" width="80" align="left">
              <template #default="scope">
                <span class="rank-number">{{ scope.$index + 1 }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="name" label="涉案企业/主体" min-width="180" show-overflow-tooltip />
            <el-table-column prop="count" label="线索计件" width="120" align="right">
              <template #default="scope">
                <span class="clue-box">{{ scope.row.count }}件</span>
              </template>
            </el-table-column>
            <el-table-column prop="personnel" label="关联人数" width="120" align="right">
              <template #default="scope">
                <span class="personnel-count">{{ scope.row.personnel }}人</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { ShoppingCart } from '@element-plus/icons-vue'
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
    tooltip: { 
      trigger: 'axis', 
      axisPointer: { type: 'shadow' },
      formatter: '{b}<br/>{a}: {c} 件'
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value', boundaryGap: [0, 0.01] },
    yAxis: { type: 'category', data: xData },
    series: [
      {
        name: '线索量',
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
.dashboard-container {
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.header-icon {
  font-size: 24px;
  color: #1890ff;
}

.header-text {
  font-size: 20px;
  font-weight: 600;
  color: #1890ff;
}

.stat-cards {
  margin-bottom: 24px;
}

.stat-card {
  position: relative;
  height: 150px;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
}

/* Use block.svg as a textured overlay to preserve underlying colors/transparency */
.stat-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('../assets/block.svg') no-repeat center center;
  background-size: cover;
  opacity: 0.85; /* Highly visible lines */
  mix-blend-mode: overlay; /* Blends beautifully with base gradients */
  pointer-events: none;
  z-index: 1;
}

.card-white::before {
  opacity: 0.25;
  filter: invert(0.8); /* Make lines dark on light background */
}

.stat-content {
  position: relative;
  z-index: 2;
}

.card-blue {
  background: linear-gradient(135deg, #1890ff 0%, #36cfc9 100%);
  color: white;
}

.card-light-blue {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.card-white {
  background: linear-gradient(135deg, #e0f2ff 0%, #ffffff 100%);
  color: #1890ff;
  border: 1px solid rgba(24, 144, 255, 0.1) !important;
}

.stat-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 32px rgba(24, 144, 255, 0.15);
}

.card-white:hover {
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.06);
}

.stat-title {
  font-size: 15px;
  font-weight: 500;
  opacity: 0.9;
}

.stat-value {
  margin-top: auto;
}

.number {
  font-size: 42px;
  font-weight: 700;
}

.unit {
  font-size: 16px;
  margin-left: 8px;
  opacity: 0.8;
}

.text-value {
  font-size: 28px;
  font-weight: 600;
}

.charts-row {
  margin-top: 24px;
}

.chart-card, .table-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03) !important;
}

.card-header {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.chart-box {
  height: 380px;
  width: 100%;
}

.custom-table {
  --el-table-header-bg-color: #f8f9fb;
  --el-table-header-text-color: #909399;
  border-radius: 8px;
  overflow: hidden;
}

.rank-number {
  font-weight: bold;
  color: #303133;
}

.clue-box {
  display: inline-block;
  padding: 2px 8px;
  background-color: #fff2f0;
  border: 1px solid #ffccc7;
  color: #ff4d4f;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
}

.personnel-count {
  font-weight: 500;
  color: #606266;
}
</style>
