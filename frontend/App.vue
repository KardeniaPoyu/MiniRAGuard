<script>
	export default {
		onLaunch: function() {
			console.log('App Launch')
			const token = uni.getStorageSync('token')
			if (!token) {
				// 延迟跳转，等小程序初始化完成
				setTimeout(() => {
					uni.redirectTo({ url: '/pages/login/login' })
				}, 100)
			}
		},
		onShow: function() {
			console.log('App Show')
		},
		onHide: function() {
			console.log('App Hide')
		}
	}
</script>

<style>
	/*每个页面公共css */
</style>
