<!-- pages/find/find.vue -->
<template>
  <view class="container">
    <view class="header">
      <text class="title">操作日志</text>
    </view>
    <scroll-view scroll-y="true" class="logs-list">
      <view v-for="(log, index) in logs" :key="index" class="log-item">
        <text>{{ `${log.timestamp} - ${log.action}: ${log.description}` }}</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed } from 'vue';
import { useStore } from 'vuex';

const store = useStore();
const logs = computed(() => store.state.logs);
</script>

<style scoped>
.container {
  padding: 20rpx;
}

.header {
  font-size: 36rpx;
  font-weight: bold;
  margin-bottom: 20rpx;
}

.logs-list {
  height: calc(100vh - 80rpx); /* 调整高度以适应屏幕 */
}

.log-item {
  background-color: #f9f9f9;
  padding: 20rpx;
  margin-bottom: 10rpx;
  border-radius: 10rpx;
}
</style>