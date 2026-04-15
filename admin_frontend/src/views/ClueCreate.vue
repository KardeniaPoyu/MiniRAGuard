<template>
  <el-card header="录入新线索">
    <el-form label-width="120px" :model="form" style="max-width: 600px">
      <el-form-item label="线索标题">
        <el-input v-model="form.title" placeholder="一句话概括违法线索" />
      </el-form-item>
      <el-form-item label="线索来源">
        <el-select v-model="form.source" placeholder="请选择">
          <el-option label="群众投诉" value="群众投诉" />
          <el-option label="职能部门移交" value="职能部门移交" />
          <el-option label="网络舆情" value="网络舆情" />
        </el-select>
      </el-form-item>
      <el-form-item label="所属领域">
        <el-select v-model="form.domain" placeholder="请选择">
          <el-option label="食品安全" value="食品安全" />
          <el-option label="环境污染" value="环境污染" />
          <el-option label="劳动违法" value="劳动违法" />
          <el-option label="房产纠纷" value="房产纠纷" />
          <el-option label="金融风险" value="金融风险" />
          <el-option label="其他" value="其他" />
        </el-select>
      </el-form-item>
      <el-form-item label="详细内容">
        <el-input type="textarea" :rows="6" v-model="form.content" placeholder="输入内容..." />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="submit" :loading="loading">提交并触发研判</el-button>
        <el-button @click="$router.push('/clues')">取消</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

const router = useRouter()
const form = reactive({ title: '', source: '', domain: '', content: '' })
const loading = ref(false)

const submit = async () => {
  if (!form.title || !form.content) return ElMessage.warning('请填写完整信息')
  loading.value = true
  try {
    const res = await api.createClue(form)
    ElMessage.success('提交成功！正在后台研判中...')
    router.push(`/clues/${res.data.clue_id}`)
  } catch (e) {
    ElMessage.error('提交失败')
  }
  loading.value = false
}
</script>
