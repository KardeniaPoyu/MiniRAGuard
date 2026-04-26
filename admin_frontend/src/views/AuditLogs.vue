<template>
  <el-card header="系统操作审计日志">
    <el-table :data="logs" style="width: 100%" stripe>
      <el-table-column prop="created_at" label="时间" width="200">
        <template #default="scope">{{ formatTime(scope.row.created_at) }}</template>
      </el-table-column>
      <el-table-column prop="username" label="操作员" width="120">
        <template #default="scope">
           <el-tag size="small">{{ scope.row.username }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="ip_address" label="IP 地址" width="150" />
      <el-table-column prop="action" label="动作类型" width="150" />
      <el-table-column prop="details" label="详细内容" />
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const logs = ref([])

const formatTime = (isoString) => {
  return new Date(isoString).toLocaleString('zh-CN', { timeZoneName: 'short' })
}

onMounted(async () => {
  const res = await api.getLogs()
  logs.value = res.data
})
</script>
