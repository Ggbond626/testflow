<template>
  <div class="project-overview">
    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div
        v-for="stat in stats"
        :key="stat.key"
        class="bg-white/50 hover:bg-white/80 border border-gray-100 rounded-2xl p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg"
      >
        <div class="flex items-center justify-between mb-4">
          <div class="p-3 bg-gray-100 rounded-xl">
            <el-icon :size="24" class="text-gray-700">
              <component :is="stat.icon" />
            </el-icon>
          </div>
          <span class="text-3xl font-bold text-gray-900">{{ stat.value }}</span>
        </div>
        <h3 class="text-sm font-medium text-gray-500">{{ stat.label }}</h3>
      </div>
    </div>

    <!-- 模块进度概览 -->
    <div class="bg-white/50 border border-gray-100 rounded-2xl p-6 mb-6">
      <h3 class="text-lg font-bold text-gray-900 mb-4">模块进度概览</h3>
      
      <div v-if="loadingModules" class="py-8">
        <el-skeleton :rows="3" animated />
      </div>

      <div v-else-if="modules.length === 0" class="text-center py-12">
        <el-empty description="暂无模块数据" :image-size="100" />
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="module in modules"
          :key="module.id"
          class="bg-white rounded-xl p-4 border border-gray-100 hover:border-gray-200 transition-colors"
        >
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-3">
              <h4 class="font-bold text-gray-900">{{ module.name }}</h4>
              <span
                class="px-2 py-1 rounded-md text-xs font-bold"
                :class="getPriorityClass(module.priority)"
              >
                {{ getPriorityLabel(module.priority) }}
              </span>
              <span
                class="px-2 py-1 rounded-md text-xs font-bold"
                :class="getStatusClass(module.status)"
              >
                {{ getStatusLabel(module.status) }}
              </span>
            </div>
            <span class="text-sm font-bold text-gray-600">
              {{ module.stats.completion_rate.toFixed(0) }}%
            </span>
          </div>

          <div class="mb-3">
            <div class="bg-gray-100 rounded-full h-2 overflow-hidden">
              <div
                class="bg-black h-full rounded-full transition-all duration-500"
                :style="{ width: module.stats.completion_rate + '%' }"
              ></div>
            </div>
          </div>

          <div class="flex items-center gap-6 text-xs text-gray-500">
            <span>需求点: {{ module.stats.requirement_points_count }}</span>
            <span>测试点: {{ module.stats.test_points_count }}</span>
            <span>测试用例: {{ module.stats.test_cases_count }}</span>
            <div v-if="module.assignees.length > 0" class="flex items-center gap-1 ml-auto">
              <el-icon :size="14"><User /></el-icon>
              <span>{{ module.assignees.map(a => a.username).join(', ') }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 模块状态分布 -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- 按状态分布 -->
      <div class="bg-white/50 border border-gray-100 rounded-2xl p-6">
        <h3 class="text-lg font-bold text-gray-900 mb-4">模块状态分布</h3>
        <div v-if="projectStats" class="space-y-3">
          <div
            v-for="(count, status) in projectStats.modules_by_status"
            :key="status"
            class="flex items-center justify-between"
          >
            <div class="flex items-center gap-2">
              <div class="w-3 h-3 rounded-full" :class="getStatusColor(status)"></div>
              <span class="text-sm font-medium text-gray-600">{{ getStatusLabel(status) }}</span>
            </div>
            <span class="text-sm font-bold text-gray-900">{{ count }}</span>
          </div>
        </div>
      </div>

      <!-- 按优先级分布 -->
      <div class="bg-white/50 border border-gray-100 rounded-2xl p-6">
        <h3 class="text-lg font-bold text-gray-900 mb-4">模块优先级分布</h3>
        <div v-if="projectStats" class="space-y-3">
          <div
            v-for="(count, priority) in projectStats.modules_by_priority"
            :key="priority"
            class="flex items-center justify-between"
          >
            <div class="flex items-center gap-2">
              <div class="w-3 h-3 rounded-full" :class="getPriorityColor(priority)"></div>
              <span class="text-sm font-medium text-gray-600">{{ getPriorityLabel(priority) }}</span>
            </div>
            <span class="text-sm font-bold text-gray-900">{{ count }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Grid, User, Document, Checked } from '@element-plus/icons-vue'
import { moduleApi, type ModuleDetail, type ProjectStatsResponse } from '@/api/module'

const props = defineProps<{
  projectId: number
}>()

// 数据状态
const projectStats = ref<ProjectStatsResponse | null>(null)
const modules = ref<ModuleDetail[]>([])
const loadingStats = ref(false)
const loadingModules = ref(false)

// 统计卡片
const stats = computed(() => [
  {
    key: 'modules',
    label: '功能模块',
    value: projectStats.value?.module_count || 0,
    icon: Grid
  },
  {
    key: 'members',
    label: '项目成员',
    value: projectStats.value?.member_count || 0,
    icon: User
  },
  {
    key: 'requirements',
    label: '需求点',
    value: projectStats.value?.requirement_points_count || 0,
    icon: Document
  },
  {
    key: 'testcases',
    label: '测试用例',
    value: projectStats.value?.test_cases_count || 0,
    icon: Checked
  }
])

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

// 优先级样式
const getPriorityClass = (priority: string) => {
  const classes: Record<string, string> = {
    low: 'bg-gray-100 text-gray-600',
    medium: 'bg-yellow-100 text-yellow-700',
    high: 'bg-orange-100 text-orange-700',
    critical: 'bg-red-100 text-red-700'
  }
  return classes[priority] || 'bg-gray-100 text-gray-600'
}

// 优先级颜色
const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = {
    low: 'bg-gray-400',
    medium: 'bg-yellow-400',
    high: 'bg-orange-400',
    critical: 'bg-red-400'
  }
  return colors[priority] || 'bg-gray-400'
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

// 状态样式
const getStatusClass = (status: string) => {
  const classes: Record<string, string> = {
    planning: 'bg-blue-100 text-blue-700',
    in_progress: 'bg-green-100 text-green-700',
    completed: 'bg-gray-100 text-gray-600',
    on_hold: 'bg-yellow-100 text-yellow-700'
  }
  return classes[status] || 'bg-gray-100 text-gray-600'
}

// 状态颜色
const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    planning: 'bg-blue-400',
    in_progress: 'bg-green-400',
    completed: 'bg-gray-400',
    on_hold: 'bg-yellow-400'
  }
  return colors[status] || 'bg-gray-400'
}

// 加载统计数据
const loadStats = async () => {
  loadingStats.value = true
  try {
    projectStats.value = await moduleApi.getProjectStats(props.projectId)
  } catch (error: any) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
  } finally {
    loadingStats.value = false
  }
}

// 加载模块列表
const loadModules = async () => {
  loadingModules.value = true
  try {
    const response = await moduleApi.getModules(props.projectId)
    modules.value = response.modules
  } catch (error: any) {
    console.error('加载模块列表失败:', error)
    ElMessage.error('加载模块列表失败')
  } finally {
    loadingModules.value = false
  }
}

// 初始化
onMounted(() => {
  loadStats()
  loadModules()
})
</script>

<style scoped>
.project-overview {
  padding: 4px;
}
</style>

