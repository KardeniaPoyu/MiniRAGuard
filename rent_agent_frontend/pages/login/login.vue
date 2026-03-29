<template>
  <view class="page">
    
    <!-- Top Text Group -->
    <view class="top-text-group">
      <view class="text-welcome">Welcome to</view>
      <view class="text-youthhome">YouthHome</view>
      <view class="text-ai">AI</view>
    </view>

    <!-- Center Logo & Name -->
    <view class="center-content">
      <image class="main-logo" src="/static/logo.png" mode="aspectFit"></image>
      <view class="brand-name">青居智选</view>
    </view>

    <!-- Login Button -->
    <view class="login-action">
      <button class="wx-login-btn" :class="{'btn-loading': loading}" @tap="handleLogin">
        {{ loading ? '登录中...' : '微信登录' }}
      </button>
    </view>

    <!-- Bottom Agreement -->
    <view class="agreement-section">
      <view class="checkbox-circle" @tap="toggleAgreement">
        <view v-if="agreed" class="checked-dot"></view>
      </view>
      <view class="agreement-text">
        <text class="text-black" @tap="toggleAgreement">我同意青居智选 </text>
        <text class="text-blue">《用户服务协议》</text>
        <text class="text-black"> 和 </text>
        <text class="text-blue">《隐私条款》</text>
      </view>
    </view>

  </view>
</template>

<script>
import BASE_URL from '../../config.js'

export default {
  name: 'LoginPage',
  data() {
    return {
      loading: false,
      agreed: false
    }
  },
  methods: {
    toggleAgreement() {
      this.agreed = !this.agreed;
    },
    handleLogin() {
      if (!this.agreed) {
        uni.showToast({ title: '请先阅读并同意用户协议和隐私条款', icon: 'none' });
        return;
      }
      if (this.loading) return;
      this.loading = true;

      // #ifdef MP-WEIXIN
      // 1. 微信小程序环境：走正常授权流程
      uni.login({
        provider: 'weixin',
        success: (loginRes) => {
          this.loginWithCode(loginRes.code);
        },
        fail: () => {
          this.loading = false;
          uni.showToast({ title: '微信授权失败', icon: 'none' });
        }
      });
      // #endif

      // #ifndef MP-WEIXIN
      // 2. 非微信环境（如 HBuilderX H5 预览）：使用测试通道 bypass
      uni.showToast({ title: 'H5 预览：使用测试账号', icon: 'none' });
      this.loginWithCode("test_code");
      // #endif
    },

    loginWithCode(code) {
      uni.request({
        url: BASE_URL + '/api/login',
        method: 'POST',
        header: { 'Content-Type': 'application/json' },
        data: { code },
        success: (res) => {
          this.loading = false;
          if (res.statusCode === 200 && res.data && res.data.token) {
            uni.setStorageSync('token', res.data.token);
            uni.setStorageSync('user', JSON.stringify(res.data.user));
            uni.redirectTo({ url: '/pages/index/index' });
          } else {
            uni.showToast({ title: '登录失败，请重试', icon: 'none' });
          }
        },
        fail: () => {
          this.loading = false;
          uni.showToast({ title: '登录请求失败', icon: 'none' });
        }
      });
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background-color: #FFFFFF;
  display: flex;
  flex-direction: column;
  position: relative;
  padding: 0 80rpx;
  box-sizing: border-box;
}

/* ===== Top Text Group ===== */
.top-text-group {
  margin-top: 150rpx;
  display: flex;
  flex-direction: column;
}

.text-welcome {
  font-size: 40rpx;
  font-weight: 900;
  color: #B5D0E6;
  letter-spacing: 2rpx;
  margin-bottom: 5rpx;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
}

.text-youthhome {
  font-size: 72rpx;
  font-weight: 900;
  color: #B5D0E6;
  letter-spacing: 2rpx;
  line-height: 1.1;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
}

.text-ai {
  font-size: 72rpx;
  font-weight: 900;
  color: #B5D0E6;
  letter-spacing: 2rpx;
  line-height: 1.1;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
}

/* ===== Center Logo & Name ===== */
.center-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-top: -80rpx;
}

.main-logo {
  width: 500rpx;
  height: 380rpx;
}

.brand-name {
  margin-top: 10rpx;
  font-size: 80rpx;
  color: #3B5373;
  font-family: 'Songti SC', 'STSong', 'SimSun', serif; 
  font-weight: 600;
  letter-spacing: 10rpx;
}

/* ===== Login Button ===== */
.login-action {
  margin-bottom: 220rpx;
  width: 100%;
}

.wx-login-btn {
  background-color: #8CBAED;
  color: #FFFFFF;
  font-size: 34rpx;
  font-weight: 400;
  height: 96rpx;
  line-height: 96rpx;
  border-radius: 12rpx;
  box-shadow: 0 6rpx 20rpx rgba(140, 186, 237, 0.4);
  margin: 0;
  border: none;
}
.wx-login-btn::after {
  border: none;
}
.btn-loading {
  opacity: 0.7;
}

/* ===== Bottom Agreement ===== */
.agreement-section {
  position: absolute;
  bottom: 80rpx;
  left: 0;
  width: 100%;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
}

.checkbox-circle {
  width: 30rpx;
  height: 30rpx;
  border-radius: 50%;
  border: 2rpx solid #888888;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12rpx;
}

.checked-dot {
  width: 18rpx;
  height: 18rpx;
  border-radius: 50%;
  background-color: #8CBAED;
}

.agreement-text {
  font-size: 24rpx;
}

.text-black {
  color: #333333;
}

.text-blue {
  color: #559DF3;
}
</style>
