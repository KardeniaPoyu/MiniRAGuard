<template>
  <view class="page-root">

    <!-- ====== 顶部导航栏 ====== -->
    <view class="navbar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="navbar-inner">
        <view class="nav-back" @tap="goBack">
          <text class="nav-back-text">←</text>
        </view>
        <text class="nav-title">法律求助热线</text>
        <view style="width: 72rpx;"></view>
      </view>
    </view>

    <!-- ====== 内容区 ====== -->
    <scroll-view scroll-y class="content" :style="{ paddingTop: navbarTotalHeight + 'px' }">

      <!-- 第一组：业务纠纷相关 -->
      <view class="group-section">
        <text class="group-title">业务纠纷相关</text>
        <view
          v-for="item in rentalLines"
          :key="item.number"
          class="hotline-card"
          @tap="dialNumber(item)"
        >
          <view class="hotline-icon-wrap">
            <text class="hotline-icon">☎</text>
          </view>
          <view class="hotline-info">
            <text class="hotline-name">{{ item.name }}</text>
            <text class="hotline-desc">{{ item.desc }}</text>
          </view>
          <view class="hotline-right">
            <text class="hotline-number">{{ item.number }}</text>
            <text class="hotline-action">点击拨打</text>
          </view>
        </view>
      </view>

      <!-- 第二组：紧急求助 -->
      <view class="group-section">
        <text class="group-title">紧急求助</text>
        <view
          v-for="item in emergencyLines"
          :key="item.number"
          class="hotline-card hotline-card--emergency"
          @tap="dialNumber(item)"
        >
          <view class="hotline-icon-wrap hotline-icon-wrap--emergency">
            <text class="hotline-icon">☎</text>
          </view>
          <view class="hotline-info">
            <text class="hotline-name">{{ item.name }}</text>
            <text class="hotline-desc">{{ item.desc }}</text>
          </view>
          <view class="hotline-right">
            <text class="hotline-number hotline-number--emergency">{{ item.number }}</text>
            <text class="hotline-action">点击拨打</text>
          </view>
        </view>
      </view>

      <!-- 免责声明 -->
      <view class="disclaimer">
        <text class="disclaimer-text">以上号码为公开政府热线，仅供参考。</text>
        <text class="disclaimer-text">具体业务请以实际部门公告为准。</text>
      </view>

    </scroll-view>

  </view>
</template>

<script>
const RENTAL_LINES = [
  { name: '全国住房投诉热线', number: '12345', desc: '城市管理综合执法局' },
  { name: '消费者投诉热线',   number: '12315', desc: '市场监督管理局' },
  { name: '法律援助热线',     number: '12348', desc: '免费法律咨询' },
  { name: '住房公积金热线',   number: '12329', desc: '住房公积金管理中心' }
]

const EMERGENCY_LINES = [
  { name: '报警求助',     number: '110',   desc: '公安机关，适用强制驱逐等紧急情况' },
  { name: '法院立案咨询', number: '12368', desc: '人民法院诉讼服务热线' }
]

export default {
  name: 'HelplinePage',

  data() {
    return {
      statusBarHeight: 0,
      navbarContentHeight: 45,
      rentalLines: RENTAL_LINES,
      emergencyLines: EMERGENCY_LINES
    }
  },

  computed: {
    navbarTotalHeight() {
      return this.statusBarHeight + this.navbarContentHeight
    }
  },

  onLoad() {
    const sysInfo = uni.getSystemInfoSync()
    this.statusBarHeight = sysInfo.statusBarHeight || 0
    const ratio = sysInfo.windowWidth / 750
    this.navbarContentHeight = Math.round(90 * ratio)
  },

  methods: {
    goBack() {
      uni.navigateBack({ delta: 1 })
    },

    dialNumber(item) {
      uni.showModal({
        title: '确认拨打',
        content: `即将拨打 ${item.name}（${item.number}）`,
        confirmText: '拨打',
        cancelText: '取消',
        success: (res) => {
          if (res.confirm) {
            uni.makePhoneCall({
              phoneNumber: item.number,
              fail: () => {
                uni.showToast({ title: '拨打失败，请手动拨号', icon: 'none' })
              }
            })
          }
        }
      })
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

/* ===== 内容区 ===== */
.content {
  min-height: 100vh;
  padding-bottom: 60rpx;
}

/* ===== 分组 ===== */
.group-section {
  margin: 30rpx 30rpx 0;
}
.group-title {
  font-size: 26rpx;
  font-weight: 700;
  color: #546E7A;
  display: block;
  margin-bottom: 16rpx;
  letter-spacing: 1rpx;
}

/* ===== 热线卡片 ===== */
.hotline-card {
  background-color: #FFFFFF;
  border-radius: 12rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
  margin-bottom: 16rpx;
  padding: 28rpx 24rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
}
.hotline-card--emergency {
  border-left: 6rpx solid #E74C3C;
}

/* 左侧图标 */
.hotline-icon-wrap {
  width: 80rpx; height: 80rpx;
  border-radius: 50%;
  background-color: #E8EEF5;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  margin-right: 24rpx;
}
.hotline-icon-wrap--emergency {
  background-color: #FDEDEC;
}
.hotline-icon {
  font-size: 34rpx;
}

/* 中间信息 */
.hotline-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.hotline-name {
  font-size: 28rpx;
  font-weight: 700;
  color: #263238;
  margin-bottom: 6rpx;
}
.hotline-desc {
  font-size: 24rpx;
  color: #90A4AE;
  line-height: 1.4;
}

/* 右侧号码 */
.hotline-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  flex-shrink: 0;
  margin-left: 16rpx;
}
.hotline-number {
  font-size: 36rpx;
  font-weight: 700;
  color: #1A3A5C;
  letter-spacing: 2rpx;
}
.hotline-number--emergency {
  color: #E74C3C;
}
.hotline-action {
  font-size: 20rpx;
  color: #B0BEC5;
  margin-top: 4rpx;
}

/* ===== 免责声明 ===== */
.disclaimer {
  margin: 40rpx 30rpx 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.disclaimer-text {
  font-size: 22rpx;
  color: #B0BEC5;
  text-align: center;
  line-height: 1.8;
}
</style>
