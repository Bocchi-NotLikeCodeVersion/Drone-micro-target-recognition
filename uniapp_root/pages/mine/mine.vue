<template>
  <view class="container">
    <!-- 用户信息 -->
    <view class="user-info">
      <image :src="user.avatar" class="avatar"></image>
      <text class="username">{{ user.name }}</text>
    </view>

    <!-- 个人信息列表 -->
    <view class="info-list">
      <navigator  hover-class="navigator-hover" class="info-item">
        
		<text class="label">编辑资料</text>
        <uni-icons type="arrowright" size="18"></uni-icons>
      </navigator>
      <view class="info-item">
		  
        <text class="label">VIP权益</text>
        <uni-icons type="arrowright" size="18"></uni-icons>
      </view>
      <!-- 更多选项... -->
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      user: {
        name: '张三',
        avatar: '../../static/chat/zhangsan.jpg' // 用户头像URL
      }
    };
  },
  onLoad() {
    // 页面加载时可以获取用户数据
  }
};
</script>

<style>
/* 样式 */
.container {
  padding: 20px;
}

.user-info {
  text-align: center;
  margin-bottom: 20px;
}

.avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: block;
  margin: 0 auto;
}

.username {
  font-size: 24px;
  margin-top: 10px;
}

.info-list .info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #eee;
}

.label {
  font-size: 16px;
}
</style>