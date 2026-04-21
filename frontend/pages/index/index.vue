<template>
  <view class="page-wrap">

    <!-- ====== 1. 顶部标题栏 ====== -->
    <view class="header">
      <view class="header-main">
        <view class="header-text">
          <text class="header-title">青居智选</text>
          <text class="header-sub">租房合同智能审查</text>
        </view>
        <view class="header-profile-btn" @tap="goToProfile">
          <text class="header-profile-icon">👤</text>
          <text class="header-profile-text">我的</text>
        </view>
      </view>
    </view>

    <!-- ====== 2. 上传区域 ====== -->
    <view class="section upload-section">

      <!-- 点击选图区域 -->
      <view class="upload-box" @tap="chooseImages">
        <view class="upload-icon-wrap">
          <text class="upload-icon">＋</text>
        </view>
        <text class="upload-hint">点击上传合同图片</text>
        <text class="upload-sub-hint">支持拍照或从相册选择，最多 10 张</text>
      </view>

      <!-- 缩略图横向滚动 -->
      <view v-if="images.length > 0" class="thumb-area">
        <scroll-view scroll-x class="thumb-scroll">
          <view class="thumb-list">
            <view
              v-for="(img, idx) in images"
              :key="idx"
              class="thumb-item"
            >
              <image :src="img" mode="aspectFill" class="thumb-img" />
              <view class="thumb-del" @tap.stop="removeImage(idx)">
                <text class="thumb-del-text">×</text>
              </view>
            </view>
          </view>
        </scroll-view>
        <text class="image-count">已选 {{ images.length }} 张 / 最多 10 张</text>
      </view>

      <!-- 开始审查按钮 -->
      <view
        class="analyze-btn"
        :class="images.length === 0 ? 'analyze-btn--disabled' : ''"
        @tap="startAnalyze"
      >
        <text class="analyze-btn-text">开始审查</text>
      </view>

    </view>

    <!-- ====== 3. 加载遮罩 ====== -->
    <view v-if="loading" class="loading-mask">
      <view class="loading-box">
        <view class="spinner"></view>
        <text class="loading-text">正在分析合同，请耐心等待...</text>
      </view>
    </view>

    <!-- 极速模式标签 -->
    <view v-if="showCacheTag" class="cache-tag">
      <text class="cache-tag-text">⚡ 极速模式</text>
    </view>

    <!-- ====== 4. 审查结果区域 ====== -->
    <view v-if="results && results.analysis_results && results.analysis_results.length > 0" class="section results-section">

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

      <!-- ====== 4.1 合同原文速览 ====== -->
      <view class="raw-text-section">
        <view class="raw-text-header" @tap="rawTextExpanded = !rawTextExpanded">
          <text class="raw-text-title">合同原文速览</text>
          <text class="raw-text-hint">已标注风险关键词</text>
          <text class="raw-text-toggle">{{ rawTextExpanded ? '收起' : '展开' }}</text>
        </view>

        <view v-if="rawTextExpanded">
          <!-- 图例说明 -->
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
          <!-- 高亮正文 -->
          <view class="raw-text-body">
            <rich-text :nodes="highlightedContractText"></rich-text>
          </view>
        </view>
      </view>

      <!-- ====== 4.2 分类导航栏 ====== -->
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

      <!-- ====== 4.3 过滤后的风险条款列表 ====== -->
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

      <!-- 法律求助热线入口 -->
      <view class="helpline-btn" @tap="goToHelpline">
        <text class="helpline-btn-text">法律求助热线</text>
      </view>

      <!-- 高频风险规则库入口 -->
      <view class="helpline-btn" @tap="goToRisklib">
        <text class="helpline-btn-text">高频风险规则库</text>
      </view>

    </view>

  </view>
</template>

<script>
import BASE_URL from '../../config.js'

// 分类映射表（顺序即优先级，先匹配先归类）
const CATEGORY_MAP = [
  { key: 'rent',    label: '租金',    keywords: ['租金', '租费', '滞纳', '迟延'] },
  { key: 'deposit', label: '押金',    keywords: ['押金', '定金', '保证金', '担保'] },
  { key: 'repair',  label: '维修责任', keywords: ['维修', '修缮', '损坏', '修复'] },
  { key: 'exit',    label: '解约条件', keywords: ['退租', '解除', '终止', '解约', '违约'] },
  { key: 'privacy', label: '居住权利', keywords: ['入户', '检查', '隐私', '安宁', '居住'] },
  { key: 'renew',   label: '续租条款', keywords: ['续租', '续签', '期满', '到期'] },
  { key: 'other',   label: '其他',    keywords: [] }
]

// 风险关键词高亮规则（优先级：high > medium > low）
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
  name: 'IndexPage',

  data() {
    return {
      images: [],
      loading: false,
      results: null,
      showCacheTag: false,
      expandedMap: {},
      activeCategory: 'all',
      rawTextExpanded: false
    }
  },

  computed: {
    // 合同原文高亮 HTML
    highlightedContractText() {
      if (!this.results) return ''
      // 优先使用完整合同文本，降级使用拼接片段
      const fullText = this.results.contract_text
        || (this.results.analysis_results || [])
             .map(item => item.original_text || '')
             .filter(t => t.length > 0)
             .join('\n\n')
      return this.buildHighlightHtml(fullText)
    },

    // { clause_id → category_key }
    itemCategoryMap() {
      if (!this.results || !this.results.analysis_results) return {}
      const map = {}
      for (const item of this.results.analysis_results) {
        map[item.clause_id] = this.getCategory(item)
      }
      return map
    },

    // 动态分类导航
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

    // 按分类过滤后的条款
    filteredResults() {
      if (!this.results || !this.results.analysis_results) return []
      if (this.activeCategory === 'all') return this.results.analysis_results
      return this.results.analysis_results.filter(
        item => this.itemCategoryMap[item.clause_id] === this.activeCategory
      )
    }
  },

  methods: {
    // ---- 关键词高亮 ----
    buildHighlightHtml(text) {
      if (!text) return ''
      // 收集所有待替换的词及其样式，按 level 优先级排列（high 先处理）
      const replacements = []
      for (const rule of RISK_KEYWORDS) {
        for (const word of rule.words) {
          replacements.push({ word, style: HIGHLIGHT_STYLES[rule.level] })
        }
      }

      // 用占位符先标记命中位置，防止重复替换
      let result = text
      const placeholders = []
      for (const { word, style } of replacements) {
        if (result.includes(word)) {
          const ph = `\u0002${placeholders.length}\u0003`
          placeholders.push(`<span style="${style}">${word}</span>`)
          result = result.split(word).join(ph) // 替换所有出现的位置
        }
      }

      let html = ''
      const parts = result.split(/(\u0002\d+\u0003)/)
      for (const part of parts) {
        if (/^\u0002(\d+)\u0003$/.test(part)) {
          const idx = parseInt(part.match(/\u0002(\d+)\u0003/)[1])
          html += placeholders[idx]
        } else {
          // 对普通文本 escape 并换行
          html += part
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\n/g, '<br/>')
        }
      }
      return html
    },

    // ---- 条款归类 ----
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

    // ---- 选择图片 ----
    chooseImages() {
      const remaining = 10 - this.images.length
      if (remaining <= 0) {
        uni.showToast({ title: '最多只能选择 10 张图片', icon: 'none' })
        return
      }
      uni.chooseImage({
        count: remaining,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          this.images = this.images.concat(res.tempFilePaths).slice(0, 10)
        },
        fail: () => {}
      })
    },

    // ---- 删除图片 ----
    removeImage(idx) {
      this.images.splice(idx, 1)
      const newMap = {}
      Object.keys(this.expandedMap).forEach(k => {
        const ki = parseInt(k)
        if (ki !== idx) newMap[ki < idx ? ki : ki - 1] = this.expandedMap[k]
      })
      this.expandedMap = newMap
    },

    // ---- 图片转 base64 ----
    readFileAsBase64(path) {
      return new Promise((resolve, reject) => {
        uni.getFileSystemManager().readFile({
          filePath: path,
          encoding: 'base64',
          success: (res) => resolve(res.data),
          fail: (err) => reject(err)
        })
      })
    },

    async convertImagesToBase64(paths) {
      const base64List = []
      for (const path of paths) {
        base64List.push(await this.readFileAsBase64(path))
      }
      return base64List
    },

    // ---- 开始审查 ----
    async startAnalyze() {
      if (this.images.length === 0 || this.loading) return
      this.loading = true
      this.results = null
      this.showCacheTag = false
      this.activeCategory = 'all'
      this.rawTextExpanded = false
      this.expandedMap = {}

      let base64List = []
      try {
        base64List = await this.convertImagesToBase64(this.images)
      } catch (e) {
        this.loading = false
        uni.showToast({ title: '图片读取失败，请重试', icon: 'none' })
        return
      }

      uni.request({
        url: BASE_URL + '/api/analyze',
        method: 'POST',
        header: {
          'Content-Type': 'application/json',
          'Authorization': (() => { const t = uni.getStorageSync('token'); return t ? `Bearer ${t}` : '' })()
        },
        timeout: 180000,
        data: { images: base64List },
        success: (res) => {
          this.loading = false
          if (res.statusCode === 403) {
            uni.showModal({
              title: '审查次数已用完',
              content: '观看一个短视频广告，即可获得3次审查机会',
              confirmText: '去获取',
              cancelText: '取消',
              success: (modal) => {
                if (modal.confirm) {
                  uni.navigateTo({ url: '/pages/profile/profile' })
                }
              }
            })
            return
          }
          if (res.statusCode === 200 && res.data && !res.data.error) {
            this.results = res.data
            this.expandedMap = {}
            if (res.data.cache_hit) {
              this.showCacheTag = true
              setTimeout(() => { this.showCacheTag = false }, 1500)
            }
            uni.pageScrollTo({ scrollTop: 0, duration: 300 })
          } else {
            const msg = (res.data && res.data.error) ? res.data.error : '分析失败，请稍后重试'
            uni.showToast({ title: msg, icon: 'none' })
          }
        },
        fail: () => {
          this.loading = false
          uni.showToast({ title: '网络请求失败，请检查网络', icon: 'none' })
        }
      })

    },

    goToProfile() {
      uni.navigateTo({ url: '/pages/profile/profile' })
    },

    goToChat() {
      uni.navigateTo({ url: '/pages/chat/chat?context=' + encodeURIComponent(JSON.stringify(this.results)) })
    },

    goToHelpline() {
      uni.navigateTo({ url: '/pages/helpline/helpline' })
    },

    // ---- 风险颜色 ----
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
    },

    goToRisklib() {
      uni.navigateTo({ url: '/pages/risklib/risklib' })
    }
  }
}
</script>

<style scoped>
/* ===== 全局 ===== */
.page-wrap {
  min-height: 100vh;
  background-color: #F4F6F9;
  padding-bottom: 60rpx;
}

/* ===== 顶部标题栏 ===== */
.header {
  background-color: #1A3A5C;
  padding: 40rpx 40rpx 36rpx;
}
.header-main {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
}
.header-text {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.header-title {
  font-size: 44rpx;
  font-weight: 700;
  color: #FFFFFF;
  letter-spacing: 4rpx;
}
.header-sub {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.75);
  margin-top: 10rpx;
  letter-spacing: 2rpx;
}
.header-profile-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: rgba(255,255,255,0.12);
  border-radius: 16rpx;
  padding: 12rpx 22rpx;
}
.header-profile-icon {
  font-size: 40rpx;
  line-height: 1;
}
.header-profile-text {
  font-size: 20rpx;
  color: rgba(255,255,255,0.85);
  margin-top: 4rpx;
}

/* ===== 通用 section ===== */
.section {
  margin: 30rpx 30rpx 0;
}

/* ===== 上传区域 ===== */
.upload-section {
  background-color: #FFFFFF;
  border-radius: 8rpx;
  padding: 30rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}
.upload-box {
  border: 3rpx dashed #B0BEC5;
  border-radius: 8rpx;
  padding: 50rpx 30rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: #FAFBFC;
}
.upload-icon-wrap {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background-color: #E8EEF5;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16rpx;
}
.upload-icon { font-size: 48rpx; color: #1A3A5C; line-height: 1; }
.upload-hint { font-size: 30rpx; color: #1A3A5C; font-weight: 600; }
.upload-sub-hint { font-size: 24rpx; color: #90A4AE; margin-top: 8rpx; }

/* 缩略图 */
.thumb-area { margin-top: 24rpx; }
.thumb-scroll { width: 100%; white-space: nowrap; }
.thumb-list { display: inline-flex; flex-direction: row; padding: 4rpx 0; }
.thumb-item {
  position: relative;
  width: 160rpx;
  height: 160rpx;
  margin-right: 16rpx;
  flex-shrink: 0;
  border-radius: 8rpx;
  overflow: visible;
}
.thumb-img { width: 160rpx; height: 160rpx; border-radius: 8rpx; display: block; }
.thumb-del {
  position: absolute;
  top: -16rpx; right: -16rpx;
  width: 40rpx; height: 40rpx;
  border-radius: 50%;
  background-color: #E74C3C;
  display: flex; align-items: center; justify-content: center;
  z-index: 10;
}
.thumb-del-text { color: #FFFFFF; font-size: 28rpx; line-height: 1; font-weight: 700; }
.image-count { font-size: 24rpx; color: #90A4AE; margin-top: 14rpx; display: block; }

/* 审查按钮 */
.analyze-btn {
  margin-top: 30rpx;
  background-color: #1A3A5C;
  border-radius: 8rpx;
  padding: 28rpx 0;
  display: flex; align-items: center; justify-content: center;
}
.analyze-btn--disabled { background-color: #CCCCCC; }
.analyze-btn-text { font-size: 32rpx; font-weight: 600; color: #FFFFFF; letter-spacing: 4rpx; }

/* ===== 加载遮罩 ===== */
.loading-mask {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex; align-items: center; justify-content: center;
  z-index: 9999;
}
.loading-box {
  background-color: #FFFFFF;
  border-radius: 16rpx;
  padding: 50rpx 60rpx;
  display: flex; flex-direction: column; align-items: center;
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
.loading-text { font-size: 28rpx; color: #546E7A; text-align: center; }

/* ===== 极速模式标签 ===== */
.cache-tag {
  position: fixed; top: 160rpx; left: 50%;
  transform: translateX(-50%);
  background-color: #27AE60;
  border-radius: 40rpx; padding: 12rpx 36rpx; z-index: 8888;
}
.cache-tag-text { font-size: 26rpx; color: #FFFFFF; font-weight: 600; }

/* ===== 结果区域 ===== */
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

/* 法律求助热线入口 */
.helpline-btn {
  margin-top: 16rpx;
  background-color: #F8F9FA;
  border: 2rpx solid #DEE2E6;
  border-radius: 8rpx;
  padding: 28rpx 0;
  display: flex; align-items: center; justify-content: center;
}
.helpline-btn-text { font-size: 30rpx; font-weight: 600; color: #1A3A5C; letter-spacing: 2rpx; }

/* ===== 分类导航栏 ===== */
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

/* ===== 空状态 ===== */
.empty-category { padding: 60rpx 0; display: flex; align-items: center; justify-content: center; }
.empty-category text { font-size: 28rpx; color: #90A4AE; text-align: center; }

/* ===== 合同原文速览 ===== */
.raw-text-section {
  background-color: #FFFFFF;
  border-radius: 8rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
  margin-bottom: 20rpx;
  overflow: hidden;
}
.raw-text-header {
  padding: 24rpx 30rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
}
.raw-text-title { font-size: 28rpx; font-weight: 600; color: #37474F; }
.raw-text-hint { font-size: 22rpx; color: #90A4AE; flex: 1; margin-left: 12rpx; }
.raw-text-toggle { font-size: 24rpx; color: #1A3A5C; }

/* 图例 */
.raw-text-legend {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 0 30rpx 16rpx;
  border-bottom: 1rpx solid #F4F6F9;
}
.legend-item { display: flex; flex-direction: row; align-items: center; margin-right: 28rpx; }
.legend-dot { width: 20rpx; height: 20rpx; border-radius: 4rpx; margin-right: 8rpx; }
.legend-text { font-size: 22rpx; }

/* 正文 */
.raw-text-body {
  padding: 20rpx 30rpx 24rpx;
  font-size: 26rpx;
  line-height: 1.8;
  color: #37474F;
}
</style>
