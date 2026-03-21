<template>
  <view class="page">

    <!-- ===== 顶部用户卡片 ===== -->
    <view class="user-card">
      <!-- 系统导航栏占位 -->
      <view class="status-bar-placeholder"></view>
      <view class="user-card-content">
        <!-- 头像 -->
        <view class="avatar">
          <text class="avatar-text">{{ avatarLetter }}</text>
        </view>
        <!-- 用户信息 -->
        <view class="user-info">
          <text class="user-name">{{ user.nickname || '微信用户' }}</text>
          <text class="user-meta">{{ userMeta }}</text>
        </view>
        <!-- 编辑按钮 -->
        <view class="edit-btn" @tap="toggleEdit">
          <text class="edit-btn-text">{{ showEdit ? '收起' : '编辑' }}</text>
        </view>
      </view>
    </view>

    <!-- ===== 使用情况卡片 ===== -->
    <view class="section-card">
      <text class="section-title">使用情况</text>
      <view class="usage-row">
        <view class="usage-item">
          <text class="usage-label">剩余次数</text>
          <text
            class="usage-value"
            :class="user.free_uses_remaining === 0 ? 'usage-value--red' : 'usage-value--blue'"
          >
            {{ user.free_uses_remaining === 0 ? '已用完' : user.free_uses_remaining + ' 次' }}
          </text>
        </view>
      </view>

      <!-- 看广告获取次数按钮 -->
      <view
        class="ad-btn"
        :class="user.free_uses_remaining > 5 ? 'ad-btn--disabled' : ''"
        @tap="watchAd"
      >
        <text class="ad-btn-text">
          {{ user.free_uses_remaining > 5 ? '次数充足，无需观看' : '观看广告 · 获得3次审查机会' }}
        </text>
      </view>
    </view>

    <!-- ===== 编辑资料区域 ===== -->
    <view v-if="showEdit" class="section-card edit-section">
      <text class="section-title">编辑资料</text>

      <view class="form-item">
        <text class="form-label">昵称</text>
        <input class="form-input" v-model="form.nickname" placeholder="请输入昵称" maxlength="20" />
      </view>
      <view class="form-item">
        <text class="form-label">学校</text>
        <input class="form-input" v-model="form.school" placeholder="请输入学校名称" maxlength="40" />
      </view>
      <view class="form-item">
        <text class="form-label">年级</text>
        <picker mode="selector" :range="gradeOptions" @change="onGradeChange">
          <view class="form-picker">
            <text :class="form.grade ? 'picker-text' : 'picker-placeholder'">
              {{ form.grade || '请选择年级' }}
            </text>
            <text class="picker-arrow">›</text>
          </view>
        </picker>
      </view>
      <view class="form-item">
        <text class="form-label">学号 <text class="form-label--optional">选填</text></text>
        <input class="form-input" v-model="form.student_id" placeholder="请输入学号" maxlength="20" />
      </view>

      <view class="save-btn" :class="saving ? 'save-btn--loading' : ''" @tap="saveProfile">
        <text class="save-btn-text">{{ saving ? '保存中...' : '保存资料' }}</text>
      </view>
    </view>

    <!-- ===== 退出登录 ===== -->
    <view class="logout-btn" @tap="logout">
      <text class="logout-btn-text">退出登录</text>
    </view>

  </view>
</template>

<script>
import BASE_URL from '../../config.js'

export default {
  name: 'ProfilePage',
  data() {
    return {
      user: {
        openid: '',
        nickname: '',
        school: '',
        grade: '',
        student_id: '',
        is_vip: 0,
        free_uses_remaining: 3
      },
      showEdit: false,
      saving: false,
      form: {
        nickname: '',
        school: '',
        grade: '',
        student_id: ''
      },
      gradeOptions: ['大一', '大二', '大三', '大四', '研究生']
    }
  },
  computed: {
    avatarLetter() {
      if (this.user.nickname) return this.user.nickname.charAt(0)
      return '用'
    },
    userMeta() {
      const parts = [this.user.school, this.user.grade].filter(Boolean)
      return parts.join(' · ') || '暂无学校信息'
    }
  },
  onShow() {
    this.loadProfile()
  },
  methods: {
    loadProfile() {
      // 优先从 storage 读取，再请求服务器刷新
      const cached = uni.getStorageSync('user')
      if (cached) {
        try { this.user = JSON.parse(cached) } catch (e) {}
      }
      const token = uni.getStorageSync('token')
      if (!token) return
      uni.request({
        url: BASE_URL + '/api/user/profile',
        method: 'GET',
        header: { Authorization: `Bearer ${token}` },
        success: (res) => {
          if (res.statusCode === 200 && res.data) {
            this.user = res.data
            uni.setStorageSync('user', JSON.stringify(res.data))
          }
        }
      })
    },

    watchAd() {
      if (this.user.free_uses_remaining > 5) return

      // #ifdef MP-WEIXIN
      if (wx.createRewardedVideoAd) {
        const ad = wx.createRewardedVideoAd({
          adUnitId: 'adunit-xxx' // 申请流量主后替换真实 ID
        })
        ad.onLoad(() => {})
        ad.onError((err) => {
          this.mockWatchAd()
        })
        ad.onClose((res) => {
          if (res && res.isEnded) {
            this.callRestoreApi()
          } else {
            uni.showToast({ title: '需要观看完整广告才能获得次数', icon: 'none' })
          }
        })
        ad.show().catch(() => {
          ad.load().then(() => ad.show()).catch(err => {
            this.mockWatchAd()
          })
        })
      } else {
        this.mockWatchAd()
      }
      // #endif

      // #ifndef MP-WEIXIN
      this.mockWatchAd()
      // #endif
    },

    mockWatchAd() {
      uni.showModal({
        title: '广告加载失败',
        content: '开发环境暂不支持激励视频，是否模拟观看完成（仅开发用）？',
        success: (res) => {
          if (res.confirm) {
            this.callRestoreApi()
          }
        }
      })
    },

    callRestoreApi() {
      const token = uni.getStorageSync('token')
      if (!token) {
        uni.showToast({ title: '请先登录', icon: 'none' })
        return
      }
      uni.request({
        url: BASE_URL + '/api/user/watch-ad',
        method: 'POST',
        header: { Authorization: `Bearer ${token}` },
        success: (res) => {
          if (res.statusCode === 200 && res.data) {
            uni.showToast({ title: res.data.message || '已恢复3次', icon: 'success' })
            this.user.free_uses_remaining = res.data.free_uses_remaining
            uni.setStorageSync('user', JSON.stringify(this.user))
          } else {
            uni.showToast({ title: '请求失败', icon: 'none' })
          }
        },
        fail: () => {
          uni.showToast({ title: '网络错误，请重试', icon: 'none' })
        }
      })
    },

    toggleEdit() {
      this.showEdit = !this.showEdit
      if (this.showEdit) {
        this.form.nickname = this.user.nickname
        this.form.school = this.user.school
        this.form.grade = this.user.grade
        this.form.student_id = this.user.student_id
      }
    },
    onGradeChange(e) {
      this.form.grade = this.gradeOptions[e.detail.value]
    },
    saveProfile() {
      if (this.saving) return
      const token = uni.getStorageSync('token')
      if (!token) {
        uni.showToast({ title: '请先登录', icon: 'none' })
        return
      }
      this.saving = true
      uni.request({
        url: BASE_URL + '/api/user/profile',
        method: 'POST',
        header: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        data: {
          nickname: this.form.nickname,
          school: this.form.school,
          grade: this.form.grade,
          student_id: this.form.student_id
        },
        success: (res) => {
          this.saving = false
          if (res.statusCode === 200 && res.data) {
            this.user = res.data
            uni.setStorageSync('user', JSON.stringify(res.data))
            this.showEdit = false
            uni.showToast({ title: '保存成功', icon: 'success' })
          } else {
            uni.showToast({ title: '保存失败，请重试', icon: 'none' })
          }
        },
        fail: () => {
          this.saving = false
          uni.showToast({ title: '网络错误，请重试', icon: 'none' })
        }
      })
    },
    logout() {
      uni.showModal({
        title: '退出登录',
        content: '确认退出当前账号？',
        confirmText: '退出',
        cancelText: '取消',
        success: (res) => {
          if (res.confirm) {
            uni.removeStorageSync('token')
            uni.removeStorageSync('user')
            uni.redirectTo({ url: '/pages/login/login' })
          }
        }
      })
    }
  }
}
</script>

<style scoped>
page {
  background-color: #F4F6F9;
}
.page {
  min-height: 100vh;
  background-color: #F4F6F9;
  padding-bottom: 60rpx;
}

/* ===== 顶部用户卡片 ===== */
.user-card {
  background-color: #1A3A5C;
  padding-bottom: 48rpx;
}
.status-bar-placeholder {
  height: var(--status-bar-height, 44px);
}
.user-card-content {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 30rpx 40rpx 0;
}
.avatar {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.2);
  border: 3rpx solid rgba(255, 255, 255, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.avatar-text {
  font-size: 44rpx;
  color: #FFFFFF;
  font-weight: 700;
}
.user-info {
  flex: 1;
  margin-left: 28rpx;
}
.user-name {
  font-size: 36rpx;
  font-weight: 700;
  color: #FFFFFF;
  display: block;
  margin-bottom: 8rpx;
}
.user-meta {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.7);
}
.edit-btn {
  background-color: rgba(255, 255, 255, 0.15);
  border: 1rpx solid rgba(255, 255, 255, 0.4);
  border-radius: 40rpx;
  padding: 10rpx 30rpx;
}
.edit-btn-text {
  font-size: 24rpx;
  color: #FFFFFF;
}

/* ===== Section 卡片 ===== */
.section-card {
  background-color: #FFFFFF;
  border-radius: 16rpx;
  margin: 24rpx 30rpx 0;
  padding: 36rpx;
  box-shadow: 0 2rpx 16rpx rgba(0, 0, 0, 0.06);
}
.section-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #1A3A5C;
  margin-bottom: 28rpx;
  display: block;
}

/* ===== 使用情况 ===== */
.usage-row {
  display: flex;
  flex-direction: row;
  align-items: stretch;
}
.usage-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.usage-divider {
  width: 1rpx;
  background-color: #ECEFF1;
  margin: 0 16rpx;
}
.usage-label {
  font-size: 24rpx;
  color: #90A4AE;
  margin-bottom: 12rpx;
}
.usage-value {
  font-size: 36rpx;
  font-weight: 700;
  color: #37474F;
}
.usage-value--red { color: #E74C3C; }
.usage-value--blue { color: #1A3A5C; }

/* 广告按钮 */
.ad-btn {
  margin-top: 30rpx;
  background-color: #F39C12;
  border-radius: 10rpx;
  padding: 24rpx 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ad-btn--disabled {
  background-color: #BDC3C7;
}
.ad-btn-text {
  font-size: 28rpx;
  font-weight: 600;
  color: #FFFFFF;
  letter-spacing: 2rpx;
}

/* ===== 编辑资料 ===== */
.edit-section {}
.form-item {
  margin-bottom: 28rpx;
}
.form-label {
  font-size: 26rpx;
  color: #546E7A;
  display: block;
  margin-bottom: 10rpx;
}
.form-label--optional {
  font-size: 22rpx;
  color: #B0BEC5;
  margin-left: 8rpx;
}
.form-input {
  width: 100%;
  height: 80rpx;
  background-color: #F4F6F9;
  border-radius: 10rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  color: #37474F;
  box-sizing: border-box;
}
.form-picker {
  height: 80rpx;
  background-color: #F4F6F9;
  border-radius: 10rpx;
  padding: 0 24rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
}
.picker-text { font-size: 28rpx; color: #37474F; }
.picker-placeholder { font-size: 28rpx; color: #B0BEC5; }
.picker-arrow { font-size: 36rpx; color: #90A4AE; }
.save-btn {
  background-color: #1A3A5C;
  border-radius: 10rpx;
  padding: 28rpx 0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 10rpx;
}
.save-btn--loading { opacity: 0.65; }
.save-btn-text { font-size: 30rpx; font-weight: 600; color: #FFFFFF; letter-spacing: 2rpx; }

/* ===== 退出登录 ===== */
.logout-btn {
  margin: 40rpx 30rpx 0;
  background-color: #FFFFFF;
  border-radius: 16rpx;
  padding: 32rpx 0;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}
.logout-btn-text {
  font-size: 30rpx;
  color: #90A4AE;
}
</style>
