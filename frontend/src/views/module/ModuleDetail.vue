<template>
  <div class="module-detail">
    <!-- 页面头部 -->
    <div class="page-header mb-8">
      <div class="flex items-center gap-4 mb-4">
        <button @click="goBack" class="p-2 hover:bg-gray-100 rounded-xl transition-colors text-gray-600">
          <el-icon :size="20"><ArrowLeft /></el-icon>
        </button>
        <div class="flex-1">
          <h1 class="text-2xl font-bold text-gray-900 tracking-tight">{{ moduleName || '模块详情' }}</h1>
          <p v-if="moduleDescription" class="text-sm text-gray-500 mt-1">{{ moduleDescription }}</p>
        </div>
        <div class="flex items-center gap-3">
          <span class="px-3 py-1 rounded-lg text-xs font-bold" :class="getPriorityClass(modulePriority)">
            {{ getPriorityLabel(modulePriority) }}
          </span>
          <span class="px-3 py-1 rounded-lg text-xs font-bold" :class="getStatusClass(moduleStatus)">
            {{ getStatusLabel(moduleStatus) }}
          </span>
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

      <div v-else class="tab-content">
        <!-- 需求文档 -->
        <RequirementDocs
          v-if="activeTab === 'requirements'"
          :project-id="projectId"
          :module-id="moduleId"
          @switch-tab="handleSwitchTab"
        />

        <!-- 需求点 -->
        <RequirementPoints
          v-if="activeTab === 'points'"
          :project-id="projectId"
          :module-id="moduleId"
        />

        <!-- 测试点 -->
        <TestPoints
          v-if="activeTab === 'testpoints'"
          :project-id="projectId"
          :module-id="moduleId"
        />

        <!-- 测试用例 -->
        <TestCases
          v-if="activeTab === 'testcases'"
          :project-id="projectId"
          :module-id="moduleId"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Document, List, Checked, DocumentChecked } from '@element-plus/icons-vue'
import RequirementDocs from '@/components/module/RequirementDocs.vue'
import RequirementPoints from '@/components/module/RequirementPoints.vue'
import TestPoints from '@/components/module/TestPoints.vue'
import TestCases from '@/components/module/TestCases.vue'
import { moduleApi, type ModuleDetail } from '@/api/module'
import { projectApi } from '@/api/project'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const projectId = computed(() => parseInt(route.params.projectId as string))
const moduleId = computed(() => parseInt(route.params.moduleId as string))

// 模块数据
const moduleName = ref('')
const moduleDescription = ref('')
const modulePriority = ref('medium')
const moduleStatus = ref('planning')
const moduleAssignees = ref<any[]>([])
const projectOwnerId = ref(0)

// 状态
const loading = ref(false)
const activeTab = ref('requirements')

// 检查是否有权限访问该模块
const hasModuleAccess = computed(() => {
  // 管理员有所有权限
  if (authStore.isAdmin) return true
  // 项目所有者有所有权限
  if (projectOwnerId.value === authStore.user?.id) return true
  // 检查是否被分配到该模块
  const currentUserId = authStore.user?.id
  if (!currentUserId) return false
  return moduleAssignees.value.some(a => a.user_id === currentUserId)
})

// Tab配置
const tabs = [
  { key: 'requirements', label: '需求文档', icon: Document },
  { key: 'points', label: '需求点', icon: List },
  { key: 'testpoints', label: '测试点', icon: Checked },
  { key: 'testcases', label: '用例生成', icon: DocumentChecked }
]

// 返回
const goBack = () => {
  router.push(`/projects/${projectId.value}`)
}

// 切换Tab (用于子组件触发)
const handleSwitchTab = (tab: string) => {
  activeTab.value = tab
}

// 加载项目信息
const loadProjectData = async () => {
  try {
    const project = await projectApi.getProject(projectId.value)
    projectOwnerId.value = project.owner_id
  } catch (error: any) {
    console.error('加载项目失败:', error)
  }
}

// 加载模块数据
const loadModuleData = async () => {
  loading.value = true
  try {
    // 先加载项目信息获取所有者ID
    await loadProjectData()
    
    const modules = await moduleApi.getModules(projectId.value)
    const module = modules.modules.find(m => m.id === moduleId.value)
    
    if (module) {
      moduleName.value = module.name
      moduleDescription.value = module.description || ''
      modulePriority.value = module.priority
      moduleStatus.value = module.status
      moduleAssignees.value = module.assignees || []
      
      // 检查权限
      if (!hasModuleAccess.value) {
        ElMessage.warning('您没有权限访问此模块')
        goBack()
        return
      }
    } else {
      ElMessage.error('模块不存在')
      goBack()
    }
  } catch (error: any) {
    console.error('加载模块失败:', error)
    ElMessage.error('加载模块失败')
    goBack()
  } finally {
    loading.value = false
  }
}

// 优先级标签
const getPriorityLabel = (priority: string) => {
  const labels: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    critical: '紧急'
  }
  return labels[priority] || priority
}

const getPriorityClass = (priority: string) => {
  const classes: Record<string, string> = {
    low: 'bg-gray-100 text-gray-600',
    medium: 'bg-yellow-100 text-yellow-700',
    high: 'bg-orange-100 text-orange-700',
    critical: 'bg-red-100 text-red-700'
  }
  return classes[priority] || 'bg-gray-100 text-gray-600'
}

// 状态标签
const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    planning: '规划中',
    in_progress: '进行中',
    completed: '已完成',
    on_hold: '暂停'
  }
  return labels[status] || status
}

const getStatusClass = (status: string) => {
  const classes: Record<string, string> = {
    planning: 'bg-blue-100 text-blue-700',
    in_progress: 'bg-green-100 text-green-700',
    completed: 'bg-gray-100 text-gray-600',
    on_hold: 'bg-yellow-100 text-yellow-700'
  }
  return classes[status] || 'bg-gray-100 text-gray-600'
}

// 初始化
onMounted(() => {
  loadModuleData()
})
</script>

<style scoped>
.module-detail {
  padding: 24px;
  min-height: 100vh;
}

.tab-content {
  min-height: 400px;
}
</style>

