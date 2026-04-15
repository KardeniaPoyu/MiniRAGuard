<template>
  <el-container class="app-container">
    <el-aside width="240px">
      <div style="height: 60px; line-height: 60px; text-align: center; color: white; font-size: 18px; font-weight: bold; background: #2b3643;">
        基层法检协同预警平台
      </div>
      <el-menu router :default-active="$route.path" background-color="#304156" text-color="#bfcbd9" active-text-color="#409eff" style="height: calc(100vh - 60px);">
        <el-menu-item index="/">
          <el-icon><DataBoard /></el-icon>
          <span>多维治理大屏</span>
        </el-menu-item>
        <el-menu-item index="/warnings">
          <el-icon><Warning /></el-icon>
          <span>风险预警中心</span>
        </el-menu-item>
        <el-menu-item index="/cases">
          <el-icon><Tickets /></el-icon>
          <span>协同跟进台账</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { DataBoard, Tickets, Warning } from '@element-plus/icons-vue'
</script>

<style>
body { margin: 0; font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "微软雅黑", Arial, sans-serif; }
.app-container { height: 100vh; }
.el-main { background-color: #f0f2f5; padding: 20px; }
</style>
