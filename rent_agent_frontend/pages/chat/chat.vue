<template>
  <view class="page-root">

    <!-- ====== 1. 顶部导航栏 ====== -->
    <view class="navbar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="navbar-inner">
        <view class="nav-back" @tap="goBack">
          <text class="nav-back-text">←</text>
        </view>
        <text class="nav-title">AI 法律助手</text>
        <view class="nav-risk-tag" :style="{ backgroundColor: riskColorLight(overallRisk), borderColor: riskColor(overallRisk) }">
          <text class="nav-risk-text" :style="{ color: riskColor(overallRisk) }">{{ overallRisk || '—' }}</text>
        </view>
      </view>
    </view>

    <!-- ====== 2. 合同摘要卡片（固定，不随消息滚动）====== -->
    <view class="summary-card">
      <text class="summary-label">基于您的合同审查结果</text>
      <view
        class="summary-body"
        :class="summaryExpanded ? 'summary-body--expanded' : 'summary-body--collapsed'"
      >
        <text class="summary-text">{{ contextSummary }}</text>
      </view>
      <text
        v-if="summaryNeedsToggle"
        class="summary-toggle"
        @tap="summaryExpanded = !summaryExpanded"
      >{{ summaryExpanded ? '收起' : '查看全部' }}</text>
    </view>

    <!-- ====== 3. 消息列表 ====== -->
    <scroll-view
      class="msg-list"
      scroll-y
      :scroll-into-view="scrollToId"
      :style="{ height: msgListHeight + 'px' }"
      scroll-with-animation
    >
      <view class="msg-list-inner">
        <!-- 消息气泡 -->
        <view
          v-for="(msg, idx) in messages"
          :key="idx"
          :id="'msg-' + idx"
          class="msg-row"
          :class="msg.role === 'user' ? 'msg-row--right' : 'msg-row--left'"
        >
          <!-- AI 头像 -->
          <view v-if="msg.role === 'assistant'" class="avatar avatar--ai">
            <text class="avatar-text">AI</text>
          </view>

          <!-- 气泡 -->
          <view
            class="bubble"
            :class="msg.role === 'user' ? 'bubble--user' : 'bubble--ai'"
          >
            <text class="bubble-text">{{ msg.content }}</text>
          </view>

          <!-- 用户头像 -->
          <view v-if="msg.role === 'user'" class="avatar avatar--user">
            <text class="avatar-text">我</text>
          </view>
        </view>

        <!-- AI 思考中 -->
        <view v-if="sending" class="msg-row msg-row--left" id="msg-typing">
          <view class="avatar avatar--ai">
            <text class="avatar-text">AI</text>
          </view>
          <view class="bubble bubble--ai bubble--typing">
            <text class="typing-dot">●</text>
            <text class="typing-dot">●</text>
            <text class="typing-dot">●</text>
          </view>
        </view>

        <!-- 列表底部锚点 -->
        <view id="msg-bottom" style="height: 20rpx;"></view>
      </view>
    </scroll-view>

    <!-- ====== 4. 快捷问题区 ====== -->
    <view v-if="messages.length === 0" class="quick-area">
      <view class="quick-label-row">
        <text class="quick-label">💡 您可以这样开始提问</text>
      </view>
      <view class="quick-btns">
        <view
          v-for="(q, i) in quickQuestions"
          :key="i"
          class="quick-btn"
          @tap="sendMessage(q)"
        >
          <text class="quick-btn-text">{{ q }}</text>
        </view>
      </view>
    </view>

    <!-- ====== 5. 输入框区域（fixed）====== -->
    <view class="input-bar" :style="{ bottom: safeAreaBottom + 'px' }">
      <textarea
        class="input-textarea"
        v-model="inputText"
        placeholder="请输入您的问题..."
        placeholder-class="input-placeholder"
        :adjust-position="true"
        :auto-height="false"
        :fixed="true"
        maxlength="500"
        @confirm="handleSend"
      />
      <view
        class="send-btn"
        :class="canSend ? 'send-btn--active' : 'send-btn--disabled'"
        @tap="handleSend"
      >
        <text class="send-btn-text">{{ sending ? '发送中' : '发送' }}</text>
      </view>
    </view>

  </view>
</template>

<script>
export default {
  name: 'ChatPage',

  data() {
    return {
      context: null,           // 从 index 页传入的完整 results
      messages: [],            // 页面展示的消息列表
      history: [],             // 同步给后端的 history
      inputText: '',           // 输入框内容
      sending: false,          // 发送中标志
      scrollToId: '',          // 滚动锚点
      summaryExpanded: false,  // 摘要展开状态
      summaryNeedsToggle: false,// 摘要是否超出 2 行
      statusBarHeight: 0,      // 状态栏高度(px)
      navbarHeight: 45,        // 导航栏内容区高度(px)，90rpx ≈ 45px（750rpx基准下1rpx≈0.5px）
      summaryCardHeight: 0,    // 摘要卡片实际高度(px)
      inputBarHeight: 50,      // 输入框高度(px)，100rpx ≈ 50px
      safeAreaBottom: 0,       // 安全区域底部高度(px)
      screenHeight: 0,         // 屏幕高度(px)
      quickQuestions: [
        '押金条款怎么跟房东谈？',
        '哪些条款可以要求删除？',
        '签了霸王条款怎么办？'
      ]
    }
  },

  computed: {
    overallRisk() {
      return this.context ? this.context.overall_risk : ''
    },

    contextSummary() {
      return this.context ? (this.context.summary || '') : ''
    },

    // 消息列表高度 = 屏幕总高 - 状态栏 - 导航栏内容区 - 摘要卡片 - 输入框 - 快捷区(仅首次)
    msgListHeight() {
      const quickAreaHeight = this.messages.length === 0 ? 160 : 0
      const h = this.screenHeight
            - this.statusBarHeight
            - this.navbarHeight
            - this.summaryCardHeight
            - this.inputBarHeight
            - this.safeAreaBottom
            - quickAreaHeight
      return Math.max(h, 200)
    },

    canSend() {
      return this.inputText.trim().length > 0 && !this.sending
    }
  },

  onLoad(options) {
    // 还原 context 参数
    if (options.context) {
      try {
        this.context = JSON.parse(decodeURIComponent(options.context))
      } catch (e) {
        this.context = null
      }
    }

    // 获取系统信息
    const sysInfo = uni.getSystemInfoSync()
    this.statusBarHeight = sysInfo.statusBarHeight || 0
    this.screenHeight = sysInfo.windowHeight || sysInfo.screenHeight || 667

    // rpx 转 px 比例：设备物理宽度 / 750
    const ratio = sysInfo.windowWidth / 750
    this.navbarHeight = Math.round(90 * ratio)
    this.inputBarHeight = Math.round(100 * ratio)

    // 安全区域
    if (sysInfo.safeAreaInsets) {
      this.safeAreaBottom = sysInfo.safeAreaInsets.bottom || 0
    } else if (sysInfo.safeArea) {
      this.safeAreaBottom = sysInfo.screenHeight - sysInfo.safeArea.bottom || 0
    }

    // 延迟获取摘要卡片高度
    this.$nextTick(() => {
      this.querySummaryHeight()
    })
  },

  methods: {
    // ---- 查询摘要卡片实际高度 ----
    querySummaryHeight() {
      const query = uni.createSelectorQuery().in(this)
      query.select('.summary-card').boundingClientRect(rect => {
        if (rect) {
          this.summaryCardHeight = rect.height

          // 判断是否需要展开按钮（简单估算：超过约 2 行 = 68px）
          const sysInfo = uni.getSystemInfoSync()
          const ratio = sysInfo.windowWidth / 750
          const twoLineHeight = Math.round(48 * ratio) // 28rpx * 1.7 * 2 ≈ 2行高度
          if (this.contextSummary.length > 40) {
            this.summaryNeedsToggle = true
          }
        }
      }).exec()
    },

    // ---- 返回上一页 ----
    goBack() {
      uni.navigateBack({ delta: 1 })
    },

    // ---- 处理发送（由按钮或 confirm 触发）----
    handleSend() {
      this.sendMessage(this.inputText)
    },

    // ---- 核心发送方法 ----
    sendMessage(text) {
      const trimmed = (text || '').trim()
      if (!trimmed || this.sending) return

      // 追加用户消息
      this.messages.push({ role: 'user', content: trimmed })
      this.history.push({ role: 'user', content: trimmed })
      this.inputText = ''
      this.sending = true
      this.scrollToBottom()

      uni.request({
        url: 'http://127.0.0.1:8000/api/chat',
        method: 'POST',
        header: { 'Content-Type': 'application/json' },
        timeout: 60000,
        data: {
          question: trimmed,
          context: this.context || {},
          history: this.history.slice(0, -1) // 最后一条已在 question 中，传历史
        },
        success: (res) => {
          this.sending = false
          if (res.statusCode === 200 && res.data && res.data.answer) {
            const answer = res.data.answer
            this.messages.push({ role: 'assistant', content: answer })
            this.history.push({ role: 'assistant', content: answer })
            this.scrollToBottom()
          } else {
            const msg = (res.data && res.data.error) ? res.data.error : '获取回答失败，请重试'
            uni.showToast({ title: msg, icon: 'none' })
          }
        },
        fail: () => {
          this.sending = false
          uni.showToast({ title: '网络请求失败，请检查网络', icon: 'none' })
        }
      })
    },

    // ---- 滚动到底部 ----
    scrollToBottom() {
      this.$nextTick(() => {
        if (this.sending) {
          this.scrollToId = 'msg-typing'
        } else {
          this.scrollToId = 'msg-' + (this.messages.length - 1)
        }
      })
    },

    // ---- 风险等级颜色 ----
    riskColor(level) {
      if (level === '高风险') return '#E74C3C'
      if (level === '中风险') return '#E67E22'
      if (level === '低风险') return '#27AE60'
      return '#90A4AE'
    },

    riskColorLight(level) {
      if (level === '高风险') return '#FDEDEC'
      if (level === '中风险') return '#FEF5E7'
      if (level === '低风险') return '#EAFAF1'
      return '#F4F6F9'
    }
  }
}
</script>

<style scoped>
/* 防止页面整体滚动 */
/* #ifdef MP-WEIXIN */
page {
  overflow: hidden;
  height: 100%;
}
/* #endif */

.page-root {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #F4F6F9;
  overflow: hidden;
}

/* ===== 导航栏 ===== */
.navbar {
  background-color: #1A3A5C;
  width: 100%;
  box-sizing: border-box;
  flex-shrink: 0;
}

.navbar-inner {
  height: 90rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 0 24rpx;
}

.nav-back {
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.nav-back-text {
  font-size: 36rpx;
  color: #FFFFFF;
  font-weight: 600;
}

.nav-title {
  flex: 1;
  text-align: center;
  font-size: 32rpx;
  font-weight: 700;
  color: #FFFFFF;
  letter-spacing: 2rpx;
}

.nav-risk-tag {
  border-radius: 30rpx;
  border-width: 1rpx;
  border-style: solid;
  padding: 6rpx 18rpx;
  min-width: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-risk-text {
  font-size: 24rpx;
  font-weight: 700;
}

/* ===== 摘要卡片 ===== */
.summary-card {
  background-color: #F4F6F9;
  padding: 24rpx 30rpx 20rpx;
  border-bottom: 1rpx solid #E0E0E0;
  flex-shrink: 0;
}

.summary-label {
  font-size: 24rpx;
  color: #90A4AE;
  display: block;
  margin-bottom: 10rpx;
}

.summary-body--collapsed {
  overflow: hidden;
  max-height: 80rpx; /* 约 2 行 */
}

.summary-body--expanded {
  overflow: visible;
  max-height: none;
}

.summary-text {
  font-size: 28rpx;
  color: #37474F;
  line-height: 1.7;
}

.summary-toggle {
  font-size: 24rpx;
  color: #1A3A5C;
  margin-top: 8rpx;
  display: block;
  text-decoration: underline;
}

/* ===== 消息列表 ===== */
.msg-list {
  flex: 1;
  width: 100%;
  box-sizing: border-box;
}

.msg-list-inner {
  padding: 24rpx 24rpx 0;
}

/* 消息行 */
.msg-row {
  display: flex;
  flex-direction: row;
  align-items: flex-end;
  margin-bottom: 24rpx;
}

.msg-row--right {
  justify-content: flex-end;
}

.msg-row--left {
  justify-content: flex-start;
}

/* 头像 */
.avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar--ai {
  background-color: #1A3A5C;
  margin-right: 16rpx;
}

.avatar--user {
  background-color: #27AE60;
  margin-left: 16rpx;
}

.avatar-text {
  font-size: 22rpx;
  color: #FFFFFF;
  font-weight: 700;
}

/* 气泡 */
.bubble {
  max-width: 70%;
  padding: 20rpx 24rpx;
  border-radius: 12rpx;
}

.bubble--user {
  background-color: #1A3A5C;
  border-bottom-right-radius: 4rpx;
}

.bubble--ai {
  background-color: #FFFFFF;
  border: 1rpx solid #E0E0E0;
  border-bottom-left-radius: 4rpx;
}

.bubble-text {
  font-size: 28rpx;
  line-height: 1.7;
  color: inherit;
}

.bubble--user .bubble-text {
  color: #FFFFFF;
}

.bubble--ai .bubble-text {
  color: #37474F;
}

/* 打字动画气泡 */
.bubble--typing {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 20rpx 28rpx;
}

.typing-dot {
  font-size: 18rpx;
  color: #90A4AE;
  margin: 0 4rpx;
  animation: blink 1.2s infinite;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes blink {
  0%, 80%, 100% { opacity: 0.2; }
  40%           { opacity: 1; }
}

/* ===== 快捷问题区 ===== */
.quick-area {
  background-color: #F4F6F9;
  padding: 16rpx 24rpx 12rpx;
  flex-shrink: 0;
}

.quick-label-row {
  margin-bottom: 12rpx;
}

.quick-label {
  font-size: 24rpx;
  color: #90A4AE;
}

.quick-btns {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
}

.quick-btn {
  border: 1rpx solid #1A3A5C;
  border-radius: 40rpx;
  padding: 12rpx 24rpx;
  margin-right: 16rpx;
  margin-bottom: 12rpx;
  background-color: #FFFFFF;
}

.quick-btn-text {
  font-size: 24rpx;
  color: #1A3A5C;
}

/* ===== 输入框区域（fixed）====== */
.input-bar {
  position: fixed;
  left: 0;
  right: 0;
  height: 100rpx;
  background-color: #FFFFFF;
  border-top: 1rpx solid #E0E0E0;
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 0 20rpx;
  box-sizing: border-box;
  z-index: 100;
}

.input-textarea {
  flex: 1;
  height: 68rpx;
  font-size: 28rpx;
  color: #37474F;
  background-color: #F4F6F9;
  border-radius: 34rpx;
  padding: 14rpx 24rpx;
  line-height: 1.4;
  margin-right: 16rpx;
  box-sizing: border-box;
}

.input-placeholder {
  color: #B0BEC5;
  font-size: 28rpx;
}

.send-btn {
  width: 120rpx;
  height: 68rpx;
  border-radius: 34rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.send-btn--active {
  background-color: #1A3A5C;
}

.send-btn--disabled {
  background-color: #CCCCCC;
}

.send-btn-text {
  font-size: 28rpx;
  font-weight: 600;
  color: #FFFFFF;
}

.send-btn--disabled .send-btn-text {
  color: #F0F0F0;
}
</style>