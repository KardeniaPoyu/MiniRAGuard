<template>
  <view class="page-wrap">
    <!-- ====== 自定义导航栏 ====== -->
    <view class="nav-bar">
      <view class="status-bar-placeholder"></view>
      <view class="nav-bar-content">
        <view class="nav-back" @tap="goBack">
          <text class="back-icon">‹</text>
        </view>
        <text class="nav-title">审查详情</text>
        <view class="nav-right"></view>
      </view>
    </view>

    <!-- ====== 加载中 ====== -->
    <view v-if="loading" class="state-container">
      <view class="spinner"></view>
      <text class="state-text">加载审查结果中，请稍后...</text>
    </view>
    
    <!-- ====== 记录不存在 ====== -->
    <view v-else-if="!results" class="state-container">
      <text class="empty-icon">⚠️</text>
      <text class="state-text">记录已删除或不存在</text>
    </view>

    <!-- ====== 审查结果区域 ====== -->
    <view v-else class="section results-section">
      <!-- 总结卡片 -->
      <view class="summary-card">
        <view class="summary-risk-row">
          <text class="summary-label">综合风险等级</text>
          <text
            class="summary-risk-text"
            :style="{ color: riskColor(results.overall_risk) }"
          >{{ results.overall_risk }}</text>
        </view>
        <text class="summary-text">{{ results.summary }}</text>
      </view>

      <!-- 合同原文速览 -->
      <view class="raw-text-section">
        <view class="raw-text-header" @tap="rawTextExpanded = !rawTextExpanded">
          <text class="raw-text-title">合同原文速览</text>
          <text class="raw-text-hint">已标注风险关键词</text>
          <text class="raw-text-toggle">{{ rawTextExpanded ? '收起' : '展开' }}</text>
        </view>

        <view v-if="rawTextExpanded">
          <view class="raw-text-legend">
            <view class="legend-item">
              <view class="legend-dot" style="background-color:#FDEDEC;border:1rpx solid #E74C3C;"></view>
              <text class="legend-text" style="color:#C0392B;">高风险</text>
            </view>
            <view class="legend-item">
              <view class="legend-dot" style="background-color:#FEF9E7;border:1rpx solid #E67E22;"></view>
              <text class="legend-text" style="color:#D35400;">中风险</text>
            </view>
            <view class="legend-item">
              <view class="legend-dot" style="background-color:#FFFDE7;border:1rpx solid #F9CA24;"></view>
              <text class="legend-text" style="color:#7D6608;">注意</text>
            </view>
          </view>
          <view class="raw-text-body">
            <rich-text :nodes="highlightedContractText"></rich-text>
          </view>
        </view>
      </view>

      <!-- 分类导航栏 -->
      <view class="category-nav-wrap">
        <scroll-view scroll-x class="category-scroll">
          <view class="category-list">
            <view
              v-for="cat in categoryList"
              :key="cat.key"
              class="category-tab"
              :class="activeCategory === cat.key ? 'category-tab--active' : ''"
              @tap="activeCategory = cat.key"
            >
              <text
                class="category-tab-text"
                :class="activeCategory === cat.key ? 'category-tab-text--active' : ''"
              >{{ cat.label }}</text>
              <view v-if="cat.key !== 'all'" class="category-badge" :class="cat.hasHigh ? 'category-badge--high' : 'category-badge--normal'">
                <text class="category-badge-text">{{ cat.count }}</text>
              </view>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- 过滤后的风险条款列表 -->
      <view v-if="filteredResults.length === 0" class="empty-category">
        <text>该类条款未发现风险</text>
      </view>

      <view
        v-for="(item, idx) in filteredResults"
        :key="item.clause_id"
        class="clause-card"
      >
        <view class="clause-bar" :style="{ backgroundColor: riskColor(item.risk_level) }"></view>

        <view class="clause-content">
          <view class="clause-header">
            <view class="clause-type-tag" :style="{ backgroundColor: riskColorLight(item.risk_level), color: riskColor(item.risk_level) }">
              <text>{{ item.risk_type }}</text>
            </view>
            <text class="clause-risk-level" :style="{ color: riskColor(item.risk_level) }">{{ item.risk_level }}</text>
          </view>

          <view class="clause-original-wrap">
            <text class="clause-label">合同原文</text>
            <view class="clause-original-box">
              <view v-if="!expandedMap[idx]">
                <text class="clause-original-text">{{ truncateText(item.original_text, 60) }}</text>
                <text
                  v-if="item.original_text && item.original_text.length > 60"
                  class="expand-btn"
                  @tap="toggleExpand(idx)"
                >展开</text>
              </view>
              <view v-else>
                <text class="clause-original-text">{{ item.original_text }}</text>
                <text class="expand-btn" @tap="toggleExpand(idx)">收起</text>
              </view>
            </view>
          </view>

          <view class="clause-reason-wrap">
            <text class="clause-label">违规原因</text>
            <text class="clause-reason-text">{{ item.reason }}</text>
          </view>

          <text class="clause-legal">{{ item.legal_basis }}</text>

          <view class="clause-advice-box">
            <text class="clause-label clause-label--blue">修改建议</text>
            <text class="clause-advice-text">{{ item.advice }}</text>
          </view>
        </view>
      </view>

      <!-- 咨询 AI 助手按钮 -->
      <view class="chat-btn" @tap="goToChat">
        <text class="chat-btn-text">咨询 AI 助手</text>
      </view>
    </view>
  </view>
</template>

<script>
import BASE_URL from '../../config.js'

const CATEGORY_MAP = [
  { key: 'rent',    label: '租金',    keywords: ['租金', '租费', '滞纳', '迟延'] },
  { key: 'deposit', label: '押金',    keywords: ['押金', '定金', '保证金', '担保'] },
  { key: 'repair',  label: '维修责任', keywords: ['维修', '修缮', '损坏', '修复'] },
  { key: 'exit',    label: '解约条件', keywords: ['退租', '解除', '终止', '解约', '违约'] },
  { key: 'privacy', label: '居住权利', keywords: ['入户', '检查', '隐私', '安宁', '居住'] },
  { key: 'renew',   label: '续租条款', keywords: ['续租', '续签', '期满', '到期'] },
  { key: 'other',   label: '其他',    keywords: [] }
]

const RISK_KEYWORDS = [
  { level: 'high', words: ['概不退还', '概不负责', '无条件没收', '不予退还',
    '单方解除', '随时解约', '无需通知', '强制搬离', '擅自进入',
    '无限期扣押', '永久不退'] },
  { level: 'medium', words: ['自行承担', '概不赔偿', '不承担任何', '无权要求',
    '视为同意', '视为放弃', '单方面调整', '由甲方决定',
    '不得拒绝', '强制续签'] },
  { level: 'low', words: ['乙方须自行', '乙方负责', '承租人负责',
    '需提前告知', '须经甲方同意', '不得转租'] }
]

const HIGHLIGHT_STYLES = {
  high:   'background-color:#FDEDEC;color:#C0392B;border-radius:3px;padding:0 2px;',
  medium: 'background-color:#FEF9E7;color:#D35400;border-radius:3px;padding:0 2px;',
  low:    'background-color:#FFFDE7;color:#7D6608;border-radius:3px;padding:0 2px;'
}

export default {
  data() {
    return {
      md5: '',
      loading: true,
      results: null,
      expandedMap: {},
      activeCategory: 'all',
      rawTextExpanded: false
    }
  },
  onLoad(options) {
    if (options.md5) {
      this.md5 = options.md5
      this.fetchDetail()
    } else {
      uni.showToast({ title: '参数错误', icon: 'none' })
      this.loading = false
    }
  },
  computed: {
    highlightedContractText() {
      if (!this.results) return ''
      const fullText = this.results.contract_text
        || (this.results.analysis_results || [])
             .map(item => item.original_text || '')
             .filter(t => t.length > 0)
             .join('\n\n')
      return this.buildHighlightHtml(fullText)
    },
    itemCategoryMap() {
      if (!this.results || !this.results.analysis_results) return {}
      const map = {}
      for (const item of this.results.analysis_results) {
        map[item.clause_id] = this.getCategory(item)
      }
      return map
    },
    categoryList() {
      if (!this.results || !this.results.analysis_results) return []
      const countMap = {}
      const highMap = {}
      for (const item of this.results.analysis_results) {
        const key = this.itemCategoryMap[item.clause_id] || 'other'
        countMap[key] = (countMap[key] || 0) + 1
        if (item.risk_level === '高风险') highMap[key] = true
      }
      const list = [{ key: 'all', label: '全部', count: this.results.analysis_results.length, hasHigh: false }]
      for (const cat of CATEGORY_MAP) {
        if (countMap[cat.key]) {
          list.push({ key: cat.key, label: cat.label, count: countMap[cat.key], hasHigh: !!highMap[cat.key] })
        }
      }
      return list
    },
    filteredResults() {
      if (!this.results || !this.results.analysis_results) return []
      if (this.activeCategory === 'all') return this.results.analysis_results
      return this.results.analysis_results.filter(
        item => this.itemCategoryMap[item.clause_id] === this.activeCategory
      )
    }
  },
  methods: {
    goBack() {
      uni.navigateBack()
    },
    fetchDetail() {
      const token = uni.getStorageSync('token')
      if (!token) {
        uni.showToast({ title: '请先登录', icon: 'none' })
        this.loading = false
        return
      }
      uni.request({
        url: BASE_URL + `/api/user/records/${this.md5}`,
        method: 'GET',
        header: { Authorization: `Bearer ${token}` },
        success: (res) => {
          this.loading = false
          if (res.statusCode === 200 && res.data) {
            this.results = res.data
          } else {
            uni.showToast({ title: '记录加载失败', icon: 'none' })
          }
        },
        fail: () => {
          this.loading = false
          uni.showToast({ title: '网络请求失败', icon: 'none' })
        }
      })
    },
    buildHighlightHtml(text) {
      if (!text) return ''
      const replacements = []
      for (const rule of RISK_KEYWORDS) {
        for (const word of rule.words) {
          replacements.push({ word, style: HIGHLIGHT_STYLES[rule.level] })
        }
      }
      let result = text
      const placeholders = []
      for (const { word, style } of replacements) {
        if (result.includes(word)) {
          const ph = `\u0002${placeholders.length}\u0003`
          placeholders.push(`<span style="${style}">${word}</span>`)
          result = result.split(word).join(ph)
        }
      }
      let html = ''
      const parts = result.split(/(\u0002\d+\u0003)/)
      for (const part of parts) {
        if (/^\u0002(\d+)\u0003$/.test(part)) {
          const idx = parseInt(part.match(/\u0002(\d+)\u0003/)[1])
          html += placeholders[idx]
        } else {
          html += part.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br/>')
        }
      }
      return html
    },
    getCategory(item) {
      const text = (item.risk_type || '') + (item.reason || '')
      for (const cat of CATEGORY_MAP) {
        if (cat.keywords.length === 0) continue
        for (const kw of cat.keywords) {
          if (text.includes(kw)) return cat.key
        }
      }
      return 'other'
    },
    goToChat() {
      uni.navigateTo({ url: '/pages/chat/chat?context=' + encodeURIComponent(JSON.stringify(this.results)) })
    },
    riskColor(level) {
      if (level === '高风险') return '#E74C3C'
      if (level === '中风险') return '#E67E22'
      if (level === '低风险') return '#27AE60'
      return '#1A3A5C'
    },
    riskColorLight(level) {
      if (level === '高风险') return '#FDEDEC'
      if (level === '中风险') return '#FEF5E7'
      if (level === '低风险') return '#EAFAF1'
      return '#EAF0F6'
    },
    truncateText(text, maxLen) {
      if (!text) return ''
      return text.length > maxLen ? text.slice(0, maxLen) + '...' : text
    },
    toggleExpand(idx) {
      this.$set(this.expandedMap, idx, !this.expandedMap[idx])
    }
  }
}
</script>

<style scoped>
.page-wrap {
  min-height: 100vh;
  background-color: #F4F6F9;
  padding-bottom: 60rpx;
  display: flex;
  flex-direction: column;
}

/* 导航栏 */
.nav-bar {
  background-color: #1A3A5C;
  width: 100%;
}
.status-bar-placeholder {
  height: var(--status-bar-height, 44px);
}
.nav-bar-content {
  height: 88rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 0 30rpx;
}
.nav-back {
  width: 60rpx;
  height: 100%;
  display: flex;
  align-items: center;
}
.back-icon {
  font-size: 56rpx;
  color: #FFFFFF;
  line-height: 1;
  margin-top: -10rpx;
}
.nav-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #FFFFFF;
}
.nav-right {
  width: 60rpx;
}

.state-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-bottom: 200rpx;
  margin-top: 200rpx;
}
.empty-icon {
  font-size: 100rpx;
  margin-bottom: 20rpx;
}
.state-text {
  font-size: 30rpx;
  color: #546E7A;
  font-weight: 600;
}
.spinner {
  width: 64rpx; height: 64rpx;
  border: 6rpx solid #E0E0E0;
  border-top-color: #1A3A5C;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 24rpx;
}
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* ===== 结果区域 ===== */
.section {
  margin: 30rpx 30rpx 0;
}
.results-section { display: flex; flex-direction: column; }

/* 总结卡片 */
.summary-card {
  background-color: #FFFFFF;
  border-radius: 8rpx;
  padding: 30rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
  margin-bottom: 20rpx;
}
.summary-risk-row { display: flex; flex-direction: row; align-items: center; margin-bottom: 16rpx; }
.summary-label { font-size: 28rpx; color: #546E7A; margin-right: 20rpx; }
.summary-risk-text { font-size: 40rpx; font-weight: 700; }
.summary-text { font-size: 28rpx; color: #37474F; line-height: 1.6; }

/* 高亮速览 */
.raw-text-section {
  background-color: #FFFFFF;
  border-radius: 8rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
  margin-bottom: 20rpx;
  overflow: hidden;
}
.raw-text-header { padding: 24rpx 30rpx; display: flex; flex-direction: row; align-items: center; }
.raw-text-title { font-size: 28rpx; font-weight: 600; color: #37474F; }
.raw-text-hint { font-size: 22rpx; color: #90A4AE; flex: 1; margin-left: 12rpx; }
.raw-text-toggle { font-size: 24rpx; color: #1A3A5C; }
.raw-text-legend { display: flex; flex-direction: row; align-items: center; padding: 0 30rpx 16rpx; }
.legend-item { display: flex; flex-direction: row; align-items: center; margin-right: 24rpx; }
.legend-dot { width: 16rpx; height: 16rpx; border-radius: 50%; margin-right: 8rpx; }
.legend-text { font-size: 22rpx; }
.raw-text-body { padding: 0 30rpx 30rpx; font-size: 26rpx; color: #546E7A; line-height: 1.6; }

/* 分类导航栏 */
.category-nav-wrap {
  background-color: #FFFFFF;
  border-bottom: 1rpx solid #E0E0E0;
  margin-bottom: 20rpx;
  border-radius: 8rpx 8rpx 0 0;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}
.category-scroll { width: 100%; white-space: nowrap; }
.category-list { display: inline-flex; flex-direction: row; align-items: stretch; padding: 0 8rpx; }
.category-tab {
  position: relative;
  display: inline-flex; flex-direction: row; align-items: center;
  padding: 20rpx 28rpx 16rpx;
  border-bottom: 4rpx solid transparent;
  flex-shrink: 0;
}
.category-tab--active { border-bottom: 4rpx solid #1A3A5C; }
.category-tab-text { font-size: 26rpx; color: #90A4AE; white-space: nowrap; }
.category-tab-text--active { color: #1A3A5C; font-weight: 600; }
.category-badge {
  margin-left: 6rpx;
  min-width: 32rpx; height: 32rpx;
  border-radius: 16rpx; padding: 0 8rpx;
  display: flex; align-items: center; justify-content: center;
}
.category-badge--high { background-color: #E74C3C; }
.category-badge--normal { background-color: #B0BEC5; }
.category-badge-text { font-size: 20rpx; color: #FFFFFF; font-weight: 700; line-height: 1; }
.empty-category { padding: 60rpx 0; display: flex; align-items: center; justify-content: center; }
.empty-category text { font-size: 28rpx; color: #90A4AE; text-align: center; }

/* 风险条款卡片 */
.clause-card {
  background-color: #FFFFFF;
  border-radius: 8rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
  margin-bottom: 20rpx;
  display: flex; flex-direction: row; overflow: hidden;
}
.clause-bar { width: 8rpx; flex-shrink: 0; }
.clause-content { flex: 1; padding: 24rpx 24rpx 24rpx 20rpx; }
.clause-header { display: flex; flex-direction: row; align-items: center; margin-bottom: 20rpx; flex-wrap: wrap; }
.clause-type-tag { font-size: 24rpx; font-weight: 600; padding: 6rpx 18rpx; border-radius: 40rpx; margin-right: 16rpx; }
.clause-risk-level { font-size: 28rpx; font-weight: 700; }
.clause-original-wrap { margin-bottom: 16rpx; }
.clause-label { font-size: 24rpx; color: #78909C; display: block; margin-bottom: 8rpx; }
.clause-label--blue { color: #1A5276; }
.clause-original-box { background-color: #ECEFF1; border-radius: 6rpx; padding: 16rpx 18rpx; }
.clause-original-text { font-size: 26rpx; color: #37474F; line-height: 1.6; }
.expand-btn { font-size: 24rpx; color: #1A3A5C; margin-left: 8rpx; text-decoration: underline; }
.clause-reason-wrap { margin-bottom: 14rpx; }
.clause-reason-text { font-size: 28rpx; color: #37474F; line-height: 1.6; }
.clause-legal { font-size: 24rpx; color: #90A4AE; display: block; margin-bottom: 14rpx; }
.clause-advice-box { background-color: #EBF5FB; border-radius: 6rpx; padding: 16rpx 18rpx; }
.clause-advice-text { font-size: 28rpx; color: #1A5276; line-height: 1.6; }

/* 咨询 AI 助手按钮 */
.chat-btn {
  margin-top: 10rpx;
  background-color: #FFFFFF;
  border: 2rpx solid #1A3A5C;
  border-radius: 8rpx;
  padding: 28rpx 0;
  display: flex; align-items: center; justify-content: center;
}
.chat-btn-text { font-size: 32rpx; font-weight: 600; color: #1A3A5C; letter-spacing: 2rpx; }
</style>
