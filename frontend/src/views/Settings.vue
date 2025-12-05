<template>
  <div class="h-full flex flex-col">
    <!-- 页面描述 -->
    <div class="mb-4">
      <p class="text-gray-500">管理测试分类、设计方法和并发配置</p>
    </div>

    <!-- 设置内容区域 -->
    <div class="glass-card rounded-3xl p-6 flex-1">
      <el-tabs v-model="activeTab" class="settings-tabs">
        <!-- 测试分类标签页 -->
        <el-tab-pane label="测试分类" name="categories">
          <template #label>
            <div class="flex items-center gap-2">
              <el-icon><Collection /></el-icon>
              <span>测试分类</span>
            </div>
          </template>
          <div class="py-4">
            <TestCategories />
          </div>
        </el-tab-pane>

        <!-- 测试设计方法标签页 -->
        <el-tab-pane label="设计方法" name="methods">
          <template #label>
            <div class="flex items-center gap-2">
              <el-icon><SetUp /></el-icon>
              <span>设计方法</span>
            </div>
          </template>
          <div class="py-4">
            <TestDesignMethods />
          </div>
        </el-tab-pane>

        <!-- 并发配置标签页 -->
        <el-tab-pane label="并发配置" name="concurrency">
          <template #label>
            <div class="flex items-center gap-2">
              <el-icon><Operation /></el-icon>
              <span>并发配置</span>
            </div>
          </template>
          <div class="py-4">
            <ConcurrencySettings />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Collection, SetUp, Operation } from '@element-plus/icons-vue'
import TestCategories from '@/components/settings/TestCategories.vue'
import TestDesignMethods from '@/components/settings/TestDesignMethods.vue'
import ConcurrencySettings from '@/components/settings/ConcurrencySettings.vue'

// 当前激活的标签页
const activeTab = ref('categories')
</script>

<style scoped>
.settings-tabs {
  height: 100%;
}

:deep(.el-tabs__header) {
  margin-bottom: 0;
  border-bottom: 1px solid #e5e7eb;
}

:deep(.el-tabs__nav-wrap::after) {
  display: none;
}

:deep(.el-tabs__item) {
  font-weight: 500;
  color: #6b7280;
  padding: 0 24px;
  height: 48px;
  line-height: 48px;
}

:deep(.el-tabs__item:hover) {
  color: #374151;
}

:deep(.el-tabs__item.is-active) {
  color: #000;
  font-weight: 600;
}

:deep(.el-tabs__active-bar) {
  background-color: #000;
  height: 3px;
  border-radius: 3px 3px 0 0;
}

:deep(.el-tabs__content) {
  padding: 0;
  overflow: visible;
}

:deep(.el-tab-pane) {
  min-height: 400px;
}
</style>
