<template>
  <view class="page-root">

    <!-- ====== 顶部导航栏 ====== -->
    <view class="navbar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="navbar-inner">
        <view class="nav-back" @tap="goBack">
          <text class="nav-back-text">←</text>
        </view>
        <text class="nav-title">高频风险规则库</text>
        <view style="width: 72rpx;"></view>
      </view>
    </view>

    <scroll-view scroll-y class="content" :style="{ paddingTop: navbarTotalHeight + 'px' }">

      <!-- 页面说明区 -->
      <view class="desc-card">
        <text class="desc-text">基于系统已审查的合同案例统计，帮助你了解租房合同中最常见的风险条款类型。</text>
      </view>

      <!-- 加载中 -->
      <view v-if="loading" class="center-hint">
        <text class="center-hint-text">数据加载中...</text>
      </view>

      <!-- 空状态 -->
      <view v-else-if="list.length === 0" class="center-hint">
        <text class="center-hint-text">暂无统计数据，审查合同后将自动积累</text>
      </view>

      <!-- 统计列表 -->
      <view v-else class="list-wrap">
        <view
          v-for="(item, idx) in list"
          :key="item.risk_type"
          class="stat-card"
        >
          <!-- 左侧排名 -->
          <view class="rank-wrap">
            <view
              class="rank-circle"
              :style="{ backgroundColor: rankBg(idx) }"
            >
              <text class="rank-text">{{ idx + 1 }}</text>
            </view>
          </view>

          <!-- 中间内容 -->
          <view class="card-body">
            <view class="card-top">
              <text class="risk-type-name">{{ item.risk_type }}</text>
              <text class="risk-count-sub">已出现 {{ item.count }} 次</text>
            </view>

            <!-- 频率条 -->
            <view class="bar-track">
              <view
                class="bar-fill"
                :style="{
                  width: barWidth(item.count) + '%',
                  backgroundColor: idx < 3 ? '#E74C3C' : '#1A3A5C'
                }"
              ></view>
            </view>

            <!-- 最近出现日期 -->
            <text v-if="item.last_seen" class="last-seen">最近出现：{{ item.last_seen }}</text>
          </view>

          <!-- 右侧次数 -->
          <view class="count-wrap">
            <text class="count-num" :style="{ color: idx < 3 ? '#E74C3C' : '#1A3A5C' }">{{ item.count }}</text>
          </view>
        </view>
      </view>

      <view style="height: 60rpx;"></view>
    </scroll-view>

  </view>
</template>

<script>
import BASE_URL from '../../config.js'

export default {
  name: 'RisklibPage',

  data() {
    return {
      statusBarHeight: 0,
      navbarContentHeight: 45,
      loading: true,
      list: []
    }
  },

  computed: {
    navbarTotalHeight() {
      return this.statusBarHeight + this.navbarContentHeight
    },
    maxCount() {
      if (!this.list.length) return 1
      return this.list[0].count || 1
    }
  },

  onLoad() {
    const sysInfo = uni.getSystemInfoSync()
    this.statusBarHeight = sysInfo.statusBarHeight || 0
    const ratio = sysInfo.windowWidth / 750
    this.navbarContentHeight = Math.round(90 * ratio)
    this.loadStats()
  },

  methods: {
    goBack() {
      uni.navigateBack({ delta: 1 })
    },

    loadStats() {
      this.loading = true
      uni.request({
        url: BASE_URL + '/api/risk-stats',
        method: 'GET',
        timeout: 15000,
        success: (res) => {
          this.loading = false
          if (res.statusCode === 200 && Array.isArray(res.data)) {
            this.list = res.data
          } else {
            uni.showToast({ title: '数据加载失败', icon: 'none' })
          }
        },
        fail: () => {
          this.loading = false
          uni.showToast({ title: '网络请求失败', icon: 'none' })
        }
      })
    },

    rankBg(idx) {
      if (idx === 0) return '#F39C12'  // 金
      if (idx === 1) return '#95A5A6'  // 银
      if (idx === 2) return '#CA6F1E'  // 铜
      return '#CFD8DC'
    },

    barWidth(count) {
      return Math.round((count / this.maxCount) * 100)
    }
  }
}
</script>

<style scoped>
.page-root {
  min-height: 100vh;
  background-color: #F4F6F9;
}

/* ===== 导航栏 ===== */
.navbar {
  position: fixed;
  top: 0; left: 0; right: 0;
  background-color: #1A3A5C;
  z-index: 100;
}
.navbar-inner {
  height: 90rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 0 24rpx;
}
.nav-back {
  width: 72rpx; height: 72rpx;
  display: flex; align-items: center; justify-content: flex-start;
}
.nav-back-text { font-size: 36rpx; color: #FFFFFF; font-weight: 600; }
.nav-title { flex: 1; text-align: center; font-size: 32rpx; font-weight: 700; color: #FFFFFF; letter-spacing: 2rpx; }

/* ===== 内容 ===== */
.content { min-height: 100vh; }

/* ===== 说明卡片 ===== */
.desc-card {
  margin: 24rpx 30rpx 0;
  background-color: #FFFFFF;
  border-radius: 10rpx;
  padding: 24rpx 28rpx;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.05);
}
.desc-text { font-size: 26rpx; color: #78909C; line-height: 1.7; }

/* ===== 居中提示 ===== */
.center-hint {
  padding: 100rpx 0;
  display: flex; align-items: center; justify-content: center;
}
.center-hint-text { font-size: 28rpx; color: #90A4AE; text-align: center; }

/* ===== 列表 ===== */
.list-wrap { margin: 20rpx 30rpx 0; }

.stat-card {
  background-color: #FFFFFF;
  border-radius: 10rpx;
  box-shadow: 0 2rpx 10rpx rgba(0,0,0,0.06);
  margin-bottom: 18rpx;
  padding: 24rpx 20rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
}

/* 排名 */
.rank-wrap { flex-shrink: 0; margin-right: 20rpx; }
.rank-circle {
  width: 56rpx; height: 56rpx;
  border-radius: 28rpx;
  display: flex; align-items: center; justify-content: center;
}
.rank-text { font-size: 26rpx; font-weight: 700; color: #FFFFFF; }

/* 主体 */
.card-body { flex: 1; }
.card-top {
  display: flex;
  flex-direction: row;
  align-items: baseline;
  margin-bottom: 12rpx;
}
.risk-type-name { font-size: 28rpx; font-weight: 700; color: #263238; margin-right: 12rpx; }
.risk-count-sub { font-size: 24rpx; color: #90A4AE; }

/* 频率条 */
.bar-track {
  height: 12rpx;
  background-color: #E8EEF5;
  border-radius: 6rpx;
  overflow: hidden;
  margin-bottom: 10rpx;
}
.bar-fill {
  height: 12rpx;
  border-radius: 6rpx;
  transition: width 0.3s;
}

/* 日期 */
.last-seen { font-size: 22rpx; color: #B0BEC5; display: block; text-align: right; }

/* 次数 */
.count-wrap { flex-shrink: 0; margin-left: 16rpx; min-width: 60rpx; text-align: right; }
.count-num { font-size: 36rpx; font-weight: 700; }
</style>
