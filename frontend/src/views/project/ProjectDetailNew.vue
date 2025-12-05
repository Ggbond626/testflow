<template>
  <div class="project-detail">
    <!-- 页面头部 -->
    <div class="page-header mb-8 flex justify-between items-center">
      <div class="flex items-center gap-4">
        <button @click="$router.back()" class="p-2 hover:bg-gray-100 rounded-xl transition-colors text-gray-600">
          <el-icon :size="20"><ArrowLeft /></el-icon>
        </button>
        <div>
          <h1 class="text-2xl font-bold text-gray-900 tracking-tight">{{ projectName || '项目详情' }}</h1>
          <p v-if="projectDescription" class="text-sm text-gray-500 mt-1">{{ projectDescription }}</p>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="glass-card rounded-3xl p-6">
      <!-- Tab导航 -->
      <div class="mb-6 border-b border-gray-200">
        <div class="flex gap-1">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            @click="activeTab = tab.key"
            class="px-6 py-3 font-bold transition-all relative"
            :class="activeTab === tab.key 
              ? 'text-black' 
              : 'text-gray-400 hover:text-gray-600'"
          >
            <span class="flex items-center gap-2">
              <el-icon><component :is="tab.icon" /></el-icon>
              {{ tab.label }}
            </span>
            <div
              v-if="activeTab === tab.key"
              class="absolute bottom-0 left-0 right-0 h-0.5 bg-black rounded-t-full"
            ></div>
          </button>
        </div>
      </div>

      <!-- Tab内容 -->
      <div v-if="loading" class="py-12">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="error" class="text-center py-16">
        <el-empty description="加载失败">
          <button @click="loadProjectData" class="mt-4 px-6 py-2 bg-black text-white rounded-xl text-sm font-bold hover:bg-gray-800 transition-colors">
            重试
          </button>
        </el-empty>
      </div>

      <div v-else class="tab-content">
        <!-- 概览 -->
        <ProjectOverview
          v-if="activeTab === 'overview'"
          :project-id="projectId"
        />

        <!-- 功能模块 -->
        <ModuleList
          v-if="activeTab === 'modules'"
          :project-id="projectId"
          :can-edit="canEdit"
        />

        <!-- 成员管理 -->
        <MemberList
          v-if="activeTab === 'members'"
          :project-id="projectId"
          :can-edit="canEdit"
        />

        <!-- 测试用例 -->
        <ProjectTestCases
          v-if="activeTab === 'test-cases'"
          :project-id="projectId"
          :can-edit="canEdit"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, TrendCharts, Grid, User, List } from '@element-plus/icons-vue'
import ProjectOverview from '@/components/project/ProjectOverview.vue'
import ModuleList from '@/components/project/ModuleList.vue'
import MemberList from '@/components/project/MemberList.vue'
import ProjectTestCases from '@/components/project/ProjectTestCases.vue'
import { useAuthStore } from '@/stores/auth'
import { projectApi } from '@/api/project'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 项目ID
const projectId = computed(() => Number(route.params.id))

// 项目信息
const projectName = ref('')
const projectDescription = ref('')
const projectOwnerId = ref(0)

// 状态
const loading = ref(false)
const error = ref(false)

// 当前Tab
const activeTab = ref('overview')

// Tab配置
const tabs = computed(() => {
  const baseTabs = [
    { key: 'overview', label: '概览', icon: TrendCharts },
    { key: 'modules', label: '功能模块', icon: Grid }
  ]
  // 只有管理员或项目所有者才能看到成员管理
  if (canEdit.value) {
    baseTabs.push({ key: 'members', label: '成员管理', icon: User })
  }
  // 所有成员可见测试用例
  baseTabs.push({ key: 'test-cases', label: '测试用例', icon: List })
  
  return baseTabs
})

// 权限检查
const canEdit = computed(() => {
  return authStore.isAdmin || projectOwnerId.value === authStore.user?.id
})

// 加载项目数据
const loadProjectData = async () => {
  loading.value = true
  error.value = false
  try {
    const project = await projectApi.getProject(projectId.value)
    projectName.value = project.name
    projectDescription.value = project.description || ''
    projectOwnerId.value = project.owner_id
  } catch (err: any) {
    console.error('加载项目失败:', err)
    error.value = true
    ElMessage.error(err.response?.data?.detail || '加载项目失败')
  } finally {
    loading.value = false
  }
}

// 初始化
onMounted(() => {
  loadProjectData()
})
</script>

<style scoped>
.project-detail {
  padding: 24px;
  min-height: 100vh;
}

.tab-content {
  min-height: 400px;
}

/* 覆盖Element Plus的样式 */
:deep(.el-skeleton) {
  padding: 20px;
}
</style>
