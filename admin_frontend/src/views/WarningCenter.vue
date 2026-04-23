<template>
  <el-card>
    <div class="toolbar" style="margin-bottom: 20px;">
      <h3>12345流水拦截预警池</h3>
      <div style="display:flex; justify-content: space-between;">
        <div>
          <el-select v-model="filters.alert_level" placeholder="预警级别" clearable style="width: 150px">
            <el-option label="红色预警" value="红色预警" />
            <el-option label="黄色预警" value="黄色预警" />
            <el-option label="蓝色预警" value="蓝色预警" />
          </el-select>
          <el-button type="primary" style="margin-left: 10px;" @click="fetchData">查询预警</el-button>
        </div>
        <el-button type="success" @click="dialogVisible = true">模拟 12345 导入</el-button>
      </div>
    </div>

    <!-- 模拟导入用弹窗 -->
    <el-dialog v-model="dialogVisible" title="模拟12345流转线索单传入" width="500px">
      <el-form label-width="100px" :model="mockForm">
        <el-form-item label="企业/单位"><el-input v-model="mockForm.enterprise_name" /></el-form-item>
        <el-form-item label="涉案人数"><el-input-number v-model="mockForm.personnel_count" :min="1"/></el-form-item>
        <el-form-item label="涉案金额"><el-input v-model="mockForm.amount" type="number"/></el-form-item>
        <el-form-item label="诉求隐私">
          <el-radio-group v-model="mockForm.claimant_privacy">
            <el-radio label="公开">公开</el-radio>
            <el-radio label="保密">保密</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="简明诉求"><el-input v-model="mockForm.content" type="textarea" :rows="3"/></el-form-item>
        <el-form-item label="证据说明">
           <el-checkbox v-model="includeMockImage">包含一张工资条图片(模拟图像识别)</el-checkbox>
        </el-form-item>
        <el-form-item label="上传附随文档">
          <input type="file" ref="docFile" @change="handleDocUpload" accept=".txt,.pdf,.docx,.doc" style="width: 100%" />
          <div style="font-size:12px; color:#909399; margin-top:5px">支持直接解析 PDF/Word，系统将自动混流进案卷</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleMockIngest">推送至本平台</el-button>
      </template>
    </el-dialog>

    <el-table :data="tableData" style="width: 100%;">
      <el-table-column prop="id" label="编号" width="60" />
      <el-table-column label="预警级别" width="120">
        <template #default="scope">
          <el-tag :type="getAlertColor(scope.row.alert_level)" effect="dark">
            {{ scope.row.alert_level || '拦截中...' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="enterprise_name" label="涉及企业" width="200" />
      <el-table-column label="群体/金额" width="150">
        <template #default="scope">
           <div><i class="el-icon-user"></i> {{scope.row.personnel_count}} 人</div>
           <div style="color:#F56C6C; font-size:12px;">￥{{scope.row.amount}}</div>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="所处流程" width="120">
        <template #default="scope">
          <el-tag type="info">{{scope.row.status}}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button v-if="scope.row.status === '待研判'" type="primary" size="small" @click="$router.push(`/clues/${scope.row.id}/workbench`)">
            提取卷宗研发
          </el-button>
          <el-button v-else type="default" size="small" disabled>已研发或未阻截</el-button>
          
          <el-popconfirm title="确定彻底删除此案例吗？" @confirm="handleDelete(scope.row.id)">
            <template #reference>
              <el-button link type="danger" size="small" style="margin-left: 10px;">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const filters = ref({ alert_level: '' })
const tableData = ref([])
const dialogVisible = ref(false)
const includeMockImage = ref(false)

const mockForm = reactive({
  title: '市政热线流转单', source:'12345热线', domain:'劳动诉求', 
  enterprise_name: '', personnel_count: 1, amount: 0, content: '',
  claimant_privacy: '公开', images: []
})

const getAlertColor = (level) => {
  if (level === '红色预警') return 'danger'
  if (level === '黄色预警') return 'warning'
  if (level === '蓝色预警') return 'primary'
  return 'info'
}

const fetchData = async () => {
  const params = {}
  if (filters.value.alert_level) params.alert_level = filters.value.alert_level
  const res = await api.listClues(params)
  tableData.value = res.data
}

const handleMockIngest = async () => {
  try {
    if (includeMockImage.value) {
      mockForm.images = ["mock_img_base64_data"]
    } else {
      mockForm.images = []
    }
    await api.ingestClue(mockForm)
    ElMessage.success("12345流转线索下发成功，关键词拦截已通过")
    dialogVisible.value = false
    setTimeout(fetchData, 1000)
  } catch(e) {
    ElMessage.error(e.response?.data?.detail || "流转失败(可能触发关键词拦截)")
  }
}

const handleDocUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const res = await api.uploadDoc(formData)
    if (res.data && res.data.parsed_text) {
      mockForm.content += `\n【附件提纯内容】\n${res.data.parsed_text}`
      ElMessage.success("文档解析成功并混入流转诉求中")
    }
  } catch(e) {
    ElMessage.error("文档解析发生异常或格式不支持")
  }
}

const handleDelete = async (id) => {
  await api.deleteClue(id)
  fetchData()
}

onMounted(() => fetchData())
</script>
