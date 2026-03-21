<template>
  <view class="page-wrap">
    <!-- ====== 自定义导航栏 ====== -->
    <view class="nav-bar">
      <view class="status-bar-placeholder"></view>
      <view class="nav-bar-content">
        <view class="nav-back" @tap="goBack">
          <text class="back-icon">‹</text>
        </view>
        <text class="nav-title">审查记录</text>
        <view class="nav-right">
          <text class="record-total" v-if="records.length > 0">共 {{ records.length }} 条</text>
        </view>
      </view>
    </view>

    <!-- ====== 加载中 ====== -->
    <view v-if="loading" class="state-container">
      <text class="state-text">加载中...</text>
    </view>

    <!-- ====== 列表为空 ====== -->
    <view v-else-if="records.length === 0" class="state-container">
      <text class="empty-icon">📄</text>
      <text class="state-text">暂无审查记录</text>
      <text class="state-sub">上传合同图片开始第一次审查</text>
    </view>

    <!-- ====== 记录列表 ====== -->
    <view v-else class="list-container">
      <view
        class="record-card"
        v-for="(item, index) in records"
        :key="item.id"
        @tap="goToDetail(item.image_md5)"
      >
        <!-- 顶部行 -->
        <view class="card-header">
          <text class="risk-label" :style="{ color: riskColor(item.overall_risk) }">
            {{ item.overall_risk }}
          </text>
          <text class="time-label">{{ formatTime(item.created_at) }}</text>
        </view>
        
        <!-- 中间 summary -->
        <view class="card-body">
          <text class="summary-text">{{ item.summary }}</text>
        </view>

        <!-- 底部行 -->
        <view class="card-footer">
          <text class="clause-count">共发现 {{ item.clause_count }} 处风险条款</text>
          <view class="delete-btn" @tap.stop="deleteRecord(item.id, index)">
            <text class="delete-text">删除</text>
          </view>
        </view>
      </view>
      <view class="bottom-spacer"></view>
    </view>
  </view>
</template>

<script>
import BASE_URL from '../../config.js'

export default {
  data() {
    return {
      records: [],
      loading: true
    }
  },
  onLoad() {
    this.fetchRecords()
  },
  methods: {
    goBack() {
      uni.navigateBack()
    },
    fetchRecords() {
      const token = uni.getStorageSync('token')
      if (!token) {
        uni.showToast({ title: '请先登录', icon: 'none' })
        this.loading = false
        return
      }
      uni.request({
        url: BASE_URL + '/api/user/records',
        method: 'GET',
        header: { Authorization: `Bearer ${token}` },
        success: (res) => {
          this.loading = false
          if (res.statusCode === 200 && Array.isArray(res.data)) {
            this.records = res.data
          } else {
            uni.showToast({ title: '获取记录失败', icon: 'none' })
          }
        },
        fail: () => {
          this.loading = false
          uni.showToast({ title: '网络错误', icon: 'none' })
        }
      })
    },
    deleteRecord(id, index) {
      uni.showModal({
        title: '删除记录',
        content: '确定要删除这条审查记录吗？',
        success: (res) => {
          if (res.confirm) {
            const token = uni.getStorageSync('token')
            uni.request({
              url: BASE_URL + `/api/user/records/${id}`,
              method: 'DELETE',
              header: { Authorization: `Bearer ${token}` },
              success: (delRes) => {
                if (delRes.statusCode === 200) {
                  this.records.splice(index, 1)
                  uni.showToast({ title: '删除成功', icon: 'success' })
                } else {
                  uni.showToast({ title: '删除失败', icon: 'none' })
                }
              }
            })
          }
        }
      })
    },
    goToDetail(md5) {
      uni.navigateTo({
        url: '/pages/result/result?md5=' + md5
      })
    },
    riskColor(level) {
      if (level === '高风险') return '#E74C3C'
      if (level === '中风险') return '#E67E22'
      if (level === '低风险') return '#27AE60'
      return '#37474F'
    },
    formatTime(isoStr) {
      const d = new Date(isoStr)
      if (isNaN(d.getTime())) return isoStr
      const now = new Date()
      const pad = n => String(n).padStart(2, '0')
      const hhmm = `${pad(d.getHours())}:${pad(d.getMinutes())}`
      // 今天
      if (d.toDateString() === now.toDateString()) return `今天 ${hhmm}`
      // 本周（7天内）
      const diffDays = Math.floor((now - d) / 86400000)
      if (diffDays < 7 && diffDays >= 0) {
        const days = ['日','一','二','三','四','五','六']
        return `周${days[d.getDay()]} ${hhmm}`
      }
      // 更早
      return `${pad(d.getMonth()+1)}-${pad(d.getDate())} ${hhmm}`
    }
  }
}
</script>

<style scoped>
.page-wrap {
  min-height: 100vh;
  background-color: #F4F6F9;
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
  width: 100rpx;
  display: flex;
  justify-content: flex-end;
}
.record-total {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.6);
}

/* 状态页 */
.state-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-bottom: 200rpx;
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
.state-sub {
  font-size: 26rpx;
  color: #90A4AE;
  margin-top: 10rpx;
}

/* 列表 */
.list-container {
  padding: 30rpx;
}
.record-card {
  background-color: #FFFFFF;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.04);
}
.record-card:active {
  background-color: #FAFAFA;
}
.card-header {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}
.risk-label {
  font-size: 30rpx;
  font-weight: 700;
}
.time-label {
  font-size: 24rpx;
  color: #90A4AE;
}
.card-body {
  margin-bottom: 24rpx;
}
.summary-text {
  font-size: 28rpx;
  color: #37474F;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}
.card-footer {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  border-top: 1rpx solid #F0F0F0;
  padding-top: 20rpx;
}
.clause-count {
  font-size: 24rpx;
  color: #90A4AE;
}
.delete-btn {
  padding: 10rpx 20rpx;
  background-color: #FFF0F0;
  border-radius: 8rpx;
}
.delete-text {
  font-size: 24rpx;
  color: #E74C3C;
}
.bottom-spacer {
  height: 40rpx;
}
</style>
