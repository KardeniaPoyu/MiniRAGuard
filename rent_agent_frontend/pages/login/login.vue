<template>
  <view class="page">

    <!-- ===== 顶部 Logo 区 ===== -->
    <view class="hero">
      <view class="hero-inner">
        <view class="logo-circle">
          <text class="logo-icon">🏠</text>
        </view>
        <text class="brand-title">青居智选</text>
        <text class="brand-sub">租房合同智能审查</text>
      </view>
      <!-- 底部圆弧 -->
      <view class="hero-arc"></view>
    </view>

    <!-- ===== 下半白色卡片 ===== -->
    <view class="card">
      <text class="welcome-title">你好，欢迎使用青居智选</text>
      <text class="welcome-desc">使用微信账号一键登录，保存您的审查记录</text>

      <!-- 微信登录按钮 -->
      <view class="wx-btn" :class="loading ? 'wx-btn--loading' : ''" @tap="handleLogin">
        <view class="wx-btn-inner">
          <text class="wx-logo">
            <!-- 微信 logo SVG 近似 -->
            💬
          </text>
          <text class="wx-btn-text">{{ loading ? '登录中...' : '微信一键登录' }}</text>
        </view>
      </view>

      <text class="privacy-tip">登录即表示同意用户协议和隐私政策</text>
    </view>

  </view>
</template>

<script>
import BASE_URL from '../../config.js'

export default {
  name: 'LoginPage',
  data() {
    return {
      loading: false
    }
  },
  methods: {
    handleLogin() {
      if (this.loading) return
      this.loading = true

      // #ifdef MP-WEIXIN
      // 1. 微信小程序环境：走正常授权流程
      uni.login({
        provider: 'weixin',
        success: (loginRes) => {
          this.loginWithCode(loginRes.code)
        },
        fail: () => {
          this.loading = false
          uni.showToast({ title: '微信授权失败', icon: 'none' })
        }
      })
      // #endif

      // #ifndef MP-WEIXIN
      // 2. 非微信环境（如 HBuilderX H5 预览）：使用测试通道 bypass
      uni.showToast({ title: 'H5 预览：使用测试账号', icon: 'none' })
      this.loginWithCode("test_code")
      // #endif
    },

    loginWithCode(code) {
      uni.request({
        url: BASE_URL + '/api/login',
        method: 'POST',
        header: { 'Content-Type': 'application/json' },
        data: { code },
        success: (res) => {
          this.loading = false
          if (res.statusCode === 200 && res.data && res.data.token) {
            uni.setStorageSync('token', res.data.token)
            uni.setStorageSync('user', JSON.stringify(res.data.user))
            uni.redirectTo({ url: '/pages/index/index' })
          } else {
            uni.showToast({ title: '登录失败，请重试', icon: 'none' })
          }
        },
        fail: () => {
          this.loading = false
          uni.showToast({ title: '登录请求失败', icon: 'none' })
        }
      })
    }

  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background-color: #F4F6F9;
  display: flex;
  flex-direction: column;
}

/* ===== Hero 区 ===== */
.hero {
  background-color: #1A3A5C;
  height: 52vh;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.hero-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-bottom: 60rpx;
}
.logo-circle {
  width: 140rpx;
  height: 140rpx;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 28rpx;
  border: 3rpx solid rgba(255, 255, 255, 0.3);
}
.logo-icon {
  font-size: 70rpx;
  line-height: 1;
}
.brand-title {
  font-size: 56rpx;
  font-weight: 700;
  color: #FFFFFF;
  letter-spacing: 6rpx;
}
.brand-sub {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.75);
  margin-top: 14rpx;
  letter-spacing: 2rpx;
}
/* 底部圆弧 */
.hero-arc {
  position: absolute;
  bottom: -2rpx;
  left: 0;
  right: 0;
  height: 80rpx;
  background-color: #F4F6F9;
  border-radius: 80rpx 80rpx 0 0;
}

/* ===== 卡片 ===== */
.card {
  flex: 1;
  background-color: #F4F6F9;
  padding: 60rpx 48rpx 80rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.welcome-title {
  font-size: 38rpx;
  font-weight: 700;
  color: #1A3A5C;
  margin-bottom: 20rpx;
  text-align: center;
}
.welcome-desc {
  font-size: 28rpx;
  color: #78909C;
  text-align: center;
  line-height: 1.6;
  margin-bottom: 72rpx;
}

/* ===== 微信登录按钮 ===== */
.wx-btn {
  width: 100%;
  background-color: #07C160;
  border-radius: 100rpx;
  padding: 36rpx 0;
  box-shadow: 0 8rpx 24rpx rgba(7, 193, 96, 0.35);
  transition: opacity 0.2s;
}
.wx-btn--loading {
  opacity: 0.7;
}
.wx-btn-inner {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
}
.wx-logo {
  font-size: 40rpx;
  margin-right: 16rpx;
  line-height: 1;
}
.wx-btn-text {
  font-size: 34rpx;
  font-weight: 600;
  color: #FFFFFF;
  letter-spacing: 2rpx;
}

/* ===== 隐私提示 ===== */
.privacy-tip {
  font-size: 22rpx;
  color: #B0BEC5;
  margin-top: 40rpx;
  text-align: center;
}
</style>
