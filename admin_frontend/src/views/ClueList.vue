<template>
  <el-card>
    <div class="toolbar">
      <el-select v-model="filters.status" placeholder="状态" clearable style="width: 150px">
        <el-option label="待研判" value="待研判" />
        <el-option label="已研判" value="已研判" />
        <el-option label="已推送" value="已推送" />
        <el-option label="已办结" value="已办结" />
      </el-select>
      <el-select v-model="filters.domain" placeholder="领域" clearable style="width: 150px; margin-left: 10px;">
        <el-option label="食品安全" value="食品安全" />
        <el-option label="环境污染" value="环境污染" />
        <el-option label="劳动违法" value="劳动违法" />
      </el-select>
      <el-button type="primary" style="margin-left: 10px;" @click="fetchData">查询</el-button>
      <el-button type="success" style="margin-left: auto;" @click="$router.push('/clues/new')">新增线索</el-button>
    </div>

    <el-table :data="tableData" style="width: 100%; margin-top: 20px;">
      <el-table-column prop="id" label="编号" width="80" />
      <el-table-column prop="title" label="标题" min-width="150" />
      <el-table-column prop="domain" label="领域" width="120" />
      <el-table-column prop="risk_level" label="风险等级" width="100">
        <template #default="scope">
          <el-tag :type="getRiskColor(scope.row.risk_level)">{{ scope.row.risk_level || '未知' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column prop="created_at" label="录入时间" width="180">
        <template #default="scope">{{ new Date(scope.row.created_at).toLocaleString() }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="scope">
          <el-button link type="primary" @click="$router.push(`/clues/${scope.row.id}`)">详情</el-button>
          <el-popconfirm title="确定删除此记录吗？" @confirm="handleDelete(scope.row.id)">
            <template #reference>
              <el-button link type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const filters = ref({ status: '', domain: '' })
const tableData = ref([])

const getRiskColor = (level) => {
  if (level === '高风险') return 'danger'
  if (level === '中风险') return 'warning'
  if (level === '低风险') return 'success'
  return 'info'
}

const fetchData = async () => {
  const params = {}
  if (filters.value.status) params.status = filters.value.status
  if (filters.value.domain) params.domain = filters.value.domain
  const res = await api.listClues(params)
  tableData.value = res.data
}

const handleDelete = async (id) => {
  await api.deleteClue(id)
  fetchData()
}

onMounted(() => fetchData())
</script>
<style scoped>.toolbar { display: flex; }</style>
