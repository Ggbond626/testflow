<template>
  <div class="dashboard">

    
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="glass-card p-5 rounded-2xl flex flex-col justify-between h-32 hover:scale-[1.02] transition-transform cursor-pointer">
        <div class="flex justify-between items-start">
          <div class="w-10 h-10 rounded-xl bg-gray-100 text-gray-600 flex items-center justify-center text-lg">
            <el-icon><Folder /></el-icon>
          </div>
          <span class="text-xs font-bold text-gray-400 uppercase tracking-wider">Total</span>
        </div>
        <div>
          <p class="text-3xl font-bold text-gray-900">{{ projectStats.total_projects }}</p>
          <p class="text-xs text-gray-500 font-medium mt-1">总项目数</p>
        </div>
      </div>
      
      <div class="glass-card p-5 rounded-2xl flex flex-col justify-between h-32 hover:scale-[1.02] transition-transform cursor-pointer">
        <div class="flex justify-between items-start">
          <div class="w-10 h-10 rounded-xl bg-gray-100 text-gray-600 flex items-center justify-center text-lg">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <span class="text-xs font-bold text-gray-400 uppercase tracking-wider">New</span>
        </div>
        <div>
          <p class="text-3xl font-bold text-gray-900">+{{ systemStats.weekly_new }}</p>
          <p class="text-xs text-gray-500 font-medium mt-1">本周新增</p>
        </div>
      </div>
      
      <div class="glass-card p-5 rounded-2xl flex flex-col justify-between h-32 hover:scale-[1.02] transition-transform cursor-pointer">
        <div class="flex justify-between items-start">
          <div class="w-10 h-10 rounded-xl bg-gray-100 text-gray-600 flex items-center justify-center text-lg">
            <el-icon><Document /></el-icon>
          </div>
          <span class="text-xs font-bold text-gray-400 uppercase tracking-wider">Cases</span>
        </div>
        <div>
          <p class="text-3xl font-bold text-gray-900">{{ systemStats.test_cases }}</p>
          <p class="text-xs text-gray-500 font-medium mt-1">测试用例</p>
        </div>
      </div>
      
      <div class="glass-card p-5 rounded-2xl flex flex-col justify-between h-32 hover:scale-[1.02] transition-transform cursor-pointer">
        <div class="flex justify-between items-start">
          <div class="w-10 h-10 rounded-xl bg-gray-100 text-gray-600 flex items-center justify-center text-lg">
            <el-icon><Setting /></el-icon>
          </div>
          <span class="text-xs font-bold text-gray-400 uppercase tracking-wider">Agents</span>
        </div>
        <div>
          <p class="text-3xl font-bold text-gray-900">{{ systemStats.agents }}</p>
          <p class="text-xs text-gray-500 font-medium mt-1">AI智能体</p>
        </div>
      </div>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <div class="glass-card rounded-3xl p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-bold text-gray-900">最近项目</h3>
          <button @click="$router.push('/projects')" class="text-xs font-bold text-black hover:text-gray-600 transition-colors">
            查看全部 <i class="fa-solid fa-arrow-right ml-1"></i>
          </button>
        </div>
        
        <div v-if="recentProjects.length === 0" class="text-center py-10">
          <el-empty description="暂无项目" :image-size="100" />
          <button @click="$router.push('/projects')" class="mt-4 px-6 py-2 bg-black text-white rounded-xl text-sm font-bold hover:bg-gray-800 transition-colors">
            创建第一个项目
          </button>
        </div>
        
        <div v-else class="space-y-4">
          <div
            v-for="project in recentProjects"
            :key="project.id"
            class="group p-4 rounded-2xl bg-white/40 hover:bg-white/80 transition-all cursor-pointer border border-transparent hover:border-gray-200"
            @click="$router.push(`/projects/${project.id}`)"
          >
            <div class="flex justify-between items-start">
              <div>
                <div class="font-bold text-gray-900 group-hover:text-black mb-1">{{ project.name }}</div>
                <div class="text-xs text-gray-500 line-clamp-1">{{ project.description || '暂无描述' }}</div>
              </div>
              <div class="text-xs font-mono text-gray-400 group-hover:text-gray-600">
                {{ formatTime(project.updated_at) }}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="glass-card rounded-3xl p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-bold text-gray-900">系统状态</h3>
        </div>
        
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 rounded-2xl bg-white/40">
            <span class="text-sm font-bold text-gray-600">系统状态</span>
            <span class="px-3 py-1 rounded-full text-xs font-bold border" 
              :class="systemHealth.status === 'healthy' ? 'bg-green-100 text-green-700 border-green-200' : 'bg-red-100 text-red-700 border-red-200'">
              {{ systemHealth.status === 'healthy' ? '正常' : '异常' }}
            </span>
          </div>
          
          <div class="flex items-center justify-between p-4 rounded-2xl bg-white/40">
            <span class="text-sm font-bold text-gray-600">数据库</span>
            <span class="px-3 py-1 rounded-full text-xs font-bold border"
              :class="systemHealth.database === 'healthy' ? 'bg-green-100 text-green-700 border-green-200' : 'bg-red-100 text-red-700 border-red-200'">
              {{ systemHealth.database === 'healthy' ? '正常' : '异常' }}
            </span>
          </div>
          
          <div class="flex items-center justify-between p-4 rounded-2xl bg-white/40">
            <span class="text-sm font-bold text-gray-600">版本</span>
            <span class="font-mono text-sm font-bold text-gray-800">{{ systemHealth.version || 'v1.0.0' }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import api from '@/api'
import dayjs from 'dayjs'
import { Folder, User, Document, Setting, TrendCharts } from '@element-plus/icons-vue'

const authStore = useAuthStore()
const projectStore = useProjectStore()

// 统计数据
const projectStats = ref({ total_projects: 0 })
const systemStats = ref({
  test_cases: 0,
  agents: 0,
  weekly_new: 0
})
const recentProjects = ref<Array<{
  id: number
  name: string
  description?: string
  owner_id: number
  created_at: string
  updated_at: string
}>>([])
const systemHealth = ref<{ 
  status: string
  database: string
  version: string
}>({ status: 'healthy', database: 'healthy', version: 'v1.0.0' })

// 格式化时间
const formatTime = (time: string) => {
  return dayjs(time).format('MM-DD HH:mm')
}

// 加载数据
const loadData = async () => {
  try {
    // 加载项目列表
    await projectStore.getProjectList({ limit: 5 })
    recentProjects.value = projectStore.projects
    projectStats.value.total_projects = projectStore.total
    
    // 加载系统健康状态
    const healthData = await api.get('/api/system/health')
    systemHealth.value = healthData as any
    
    // 加载测试数据统计
    try {
      const statsData = await api.get('/api/test-data/stats') as any
      if (statsData) {
        systemStats.value.test_cases = statsData.total_test_cases || 0
        systemStats.value.weekly_new = statsData.weekly_new || 0
        systemStats.value.agents = statsData.total_agents || 0
      }
    } catch (e) {
      console.log('加载统计数据失败:', e)
    }
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
/* No extra styles needed, using Tailwind utility classes */
</style>
