<template>
  <el-container class="app-container">
    <el-aside width="200px">
      <el-menu router :default-active="$route.path" background-color="#304156" text-color="#bfcbd9" active-text-color="#409eff" style="height: 100vh;">
        <el-menu-item index="/">
          <el-icon><DataBoard /></el-icon>
          <span>数据看板</span>
        </el-menu-item>
        <el-menu-item index="/clues">
          <el-icon><Tickets /></el-icon>
          <span>线索列表</span>
        </el-menu-item>
        <el-menu-item index="/clues/new">
          <el-icon><Edit /></el-icon>
          <span>录入线索</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { DataBoard, Tickets, Edit } from '@element-plus/icons-vue'
</script>

<style>
body { margin: 0; font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "微软雅黑", Arial, sans-serif; }
.app-container { height: 100vh; }
.el-main { background-color: #f0f2f5; padding: 20px; }
</style>
