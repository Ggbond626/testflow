<template>
  <el-dialog
    v-model="visible"
    title="一键生成进度"
    width="600px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    class="generation-dialog"
    align-center
  >
    <div class="py-8 px-6">
      <!-- 成功状态展示 -->
      <div v-if="isCompleted && !errorMessage" class="text-center mb-10 animate-fade-in-up">
        <div class="w-24 h-24 mx-auto bg-black text-white rounded-full flex items-center justify-center mb-6 shadow-xl shadow-black/20 transform hover:scale-105 transition-transform duration-300">
          <el-icon class="text-5xl"><Check /></el-icon>
        </div>
        <h3 class="text-2xl font-extrabold text-gray-900 mb-2 tracking-tight">生成完成</h3>
        <p class="text-gray-500 font-medium">所有测试用例已成功生成并优化</p>
      </div>

      <!-- 失败状态展示 -->
      <div v-else-if="errorMessage" class="text-center mb-10 animate-fade-in-up">
        <div class="w-24 h-24 mx-auto bg-red-50 text-red-500 rounded-full flex items-center justify-center mb-6 shadow-xl shadow-red-500/10">
          <el-icon class="text-5xl"><CloseBold /></el-icon>
        </div>
        <h3 class="text-2xl font-extrabold text-gray-900 mb-2 tracking-tight">生成失败</h3>
        <p class="text-red-500 font-medium">{{ errorMessage }}</p>
      </div>

      <!-- 进度步骤条 -->
      <div class="relative mb-12 px-2">
        <!-- 背景连接线 -->
        <div class="absolute top-[26px] left-12 right-12 h-[2px] bg-gray-100 -z-10 rounded-full"></div>
        
        <div class="flex justify-between items-start">
          <div
            v-for="(stage, index) in stages"
            :key="stage.name"
            class="flex flex-col items-center relative group flex-1"
          >
            <!-- 动态连接线 (连接到下一个) -->
            <div 
              v-if="index < stages.length - 1"
              class="absolute top-[26px] left-[50%] w-full h-[2px] bg-black transition-all duration-1000 ease-in-out origin-left -z-0"
              :class="stage.status === 'completed' ? 'scale-x-100' : 'scale-x-0'"
            ></div>

            <!-- 步骤圆点容器 -->
            <div class="relative mb-4 flex justify-center items-center">
              <!-- 呼吸光晕 (仅进行中显示) -->
              <div 
                v-if="stage.status === 'running'"
                class="absolute inset-0 -m-2 rounded-full bg-black/5 animate-ripple"
              ></div>
              
              <!-- 圆点主体容器 -->
              <div class="relative w-14 h-14 flex items-center justify-center z-10">
                <!-- 1. 背景层 -->
                <div 
                  class="absolute inset-0 rounded-full transition-colors duration-300"
                  :class="[
                    stage.status === 'completed' ? 'bg-black shadow-lg shadow-black/20' : 'bg-white'
                  ]"
                ></div>

                <!-- 2. 边框层 -->
                <!-- Pending: 灰色边框 -->
                <div 
                  v-if="stage.status === 'pending'"
                  class="absolute inset-0 rounded-full border-2 border-gray-100"
                ></div>
                
                <!-- Running: 旋转的黑色边框环 -->
                <div 
                  v-else-if="stage.status === 'running'"
                  class="absolute inset-0 rounded-full border-[2.5px] border-gray-100 border-t-black animate-spin"
                ></div>

                <!-- 3. 图标层 (居中，不旋转) -->
                <div class="relative z-10 flex items-center justify-center w-full h-full">
                  <!-- 完成状态：对勾 (自定义超粗SVG) -->
                  <div v-if="stage.status === 'completed'" class="animate-scale-in drop-shadow-sm flex items-center justify-center">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M5 13L9 17L19 7" stroke="white" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  
                  <!-- 进行中/等待状态：显示阶段图标 -->
                  <el-icon 
                    v-else 
                    class="text-2xl transition-all duration-300" 
                    :class="[
                      stage.status === 'running' ? 'text-black scale-110' : 'text-gray-300'
                    ]"
                  >
                    <component :is="stage.icon" />
                  </el-icon>
                </div>
              </div>
            </div>
            
            <!-- 步骤信息 -->
            <div class="flex flex-col items-center gap-1.5 transition-all duration-300"
                 :class="{'opacity-40 grayscale': stage.status === 'pending', 'opacity-100': stage.status !== 'pending'}">
              <span 
                class="text-xs font-bold tracking-wide uppercase"
                :class="stage.status === 'running' ? 'text-black' : 'text-gray-500'"
              >
                {{ stage.label }}
              </span>
              
              <!-- 数量显示 -->
              <div 
                class="h-5 flex items-center justify-center overflow-hidden transition-all duration-300"
                :class="{'opacity-0 translate-y-1': stage.status === 'pending' || (stage.status === 'completed' && stage.name !== 'test_case')}"
              >
                <span 
                  v-if="stage.count !== null" 
                  class="px-2 py-0.5 bg-gray-50 text-gray-900 text-[10px] rounded-md font-bold border border-gray-100 shadow-sm"
                >
                  {{ stage.count }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 底部状态栏 (仅进行中显示) -->
      <div v-if="!isCompleted && !errorMessage" class="bg-gray-50/80 backdrop-blur-sm rounded-2xl p-5 border border-gray-100/50">
        <div class="flex justify-between items-end mb-3">
          <div class="flex flex-col gap-1">
            <span class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Status</span>
            <span class="text-sm font-bold text-gray-900 animate-pulse">{{ currentMessage }}</span>
          </div>
          <span class="text-2xl font-black text-gray-900 font-mono">{{ Math.round(progress) }}%</span>
        </div>
        <div class="h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div 
            class="h-full bg-black transition-all duration-300 ease-out rounded-full relative overflow-hidden"
            :style="{ width: `${progress}%` }"
          >
            <!-- 进度条流光效果 -->
            <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent w-full -translate-x-full animate-shimmer"></div>
          </div>
        </div>
      </div>
    </div>
    
    <template #footer>
      <div class="flex justify-center pb-6">
        <button 
          v-if="isCompleted || errorMessage" 
          @click="handleClose"
          class="group px-12 py-3.5 bg-black text-white rounded-2xl font-bold hover:bg-gray-900 transition-all shadow-xl shadow-black/10 hover:shadow-black/25 transform hover:-translate-y-0.5 active:translate-y-0 text-sm flex items-center gap-3"
        >
          <span>{{ errorMessage ? '关闭窗口' : '完成任务' }}</span>
          <el-icon class="group-hover:translate-x-1 transition-transform"><ArrowRight /></el-icon>
        </button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, markRaw } from 'vue'
import { 
  Check, 
  Loading, 
  CloseBold, 
  ArrowRight,
  Document,
  Aim,
  Collection,
  MagicStick
} from '@element-plus/icons-vue'
import api from '@/api'

interface Stage {
  name: string
  label: string
  status: 'pending' | 'running' | 'completed'
  count: number | null
  icon: any
}

const props = defineProps<{
  modelValue: boolean
  taskId: string | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'completed'): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const progress = ref(0)
const currentMessage = ref('正在初始化...')
const errorMessage = ref('')
const isCompleted = ref(false)

// 使用 markRaw 避免图标组件被响应式代理，提高性能
const stages = ref<Stage[]>([
  { name: 'requirement', label: '需求分析', status: 'pending', count: null, icon: markRaw(Document) },
  { name: 'test_point', label: '测试拆解', status: 'pending', count: null, icon: markRaw(Aim) },
  { name: 'test_case', label: '用例生成', status: 'pending', count: null, icon: markRaw(Collection) },
  { name: 'optimize', label: '智能优化', status: 'pending', count: null, icon: markRaw(MagicStick) }
])

let pollInterval: number | null = null

const updateStageStatus = (progressValue: number, message: string) => {
  // 根据进度更新阶段状态（每个阶段25%）
  if (progressValue >= 0 && progressValue < 25) {
    stages.value[0].status = 'running'
  } else if (progressValue >= 25 && progressValue < 50) {
    stages.value[0].status = 'completed'
    stages.value[1].status = 'running'
    
    // 从消息中提取需求点数量
    const reqMatch = message.match(/(\d+)\s*个/)
    if (reqMatch) {
      stages.value[0].count = parseInt(reqMatch[1])
    }
  } else if (progressValue >= 50 && progressValue < 75) {
    stages.value[0].status = 'completed'
    stages.value[1].status = 'completed'
    stages.value[2].status = 'running'
    
    // 从消息中提取测试点数量
    const tpMatch = message.match(/(\d+)\s*个/)
    if (tpMatch) {
      stages.value[1].count = parseInt(tpMatch[1])
    }
  } else if (progressValue >= 75 && progressValue < 100) {
    stages.value[0].status = 'completed'
    stages.value[1].status = 'completed'
    stages.value[2].status = 'completed'
    stages.value[3].status = 'running'
    
    // 从消息中提取测试用例数量
    const tcMatch = message.match(/(\d+)\s*个/)
    if (tcMatch) {
      stages.value[2].count = parseInt(tcMatch[1])
    }
  } else if (progressValue === 100) {
    stages.value.forEach(stage => stage.status = 'completed')
  }
}

const startPolling = () => {
  if (!props.taskId) return
  
  // 防止重复轮询
  if (pollInterval) {
    return
  }
  
  pollInterval = window.setInterval(async () => {
    try {
      const response = await api.get(`/api/agents/tasks/${props.taskId}/status`) as any
      const { status, progress: prog, message, error } = response
      
      progress.value = prog || 0
      currentMessage.value = message || '处理中...'
      
      updateStageStatus(progress.value, currentMessage.value)
      
      // 检查多种完成条件
      const isTaskCompleted = status === 'completed' || status === 'COMPLETED'
      const isProgressComplete = prog >= 100
      
      if (isTaskCompleted) {
        isCompleted.value = true
        progress.value = 100
        if (pollInterval) {
          clearInterval(pollInterval)
          pollInterval = null
        }
        emit('completed')
      } else if (status === 'failed' || status === 'FAILED') {
        errorMessage.value = error || '生成失败'
        if (pollInterval) {
          clearInterval(pollInterval)
          pollInterval = null
        }
      }
    } catch (error: any) {
      console.error('查询任务状态失败:', error)
      errorMessage.value = '查询任务状态失败'
      if (pollInterval) {
        clearInterval(pollInterval)
        pollInterval = null
      }
    }
  }, 2000)
  
  // 20分钟超时
  setTimeout(() => {
    if (pollInterval && !isCompleted.value) {
      clearInterval(pollInterval)
      pollInterval = null
      errorMessage.value = '任务执行超时（超过40分钟），请检查后台任务状态'
    }
  }, 2400000)
}

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

const handleClose = () => {
  stopPolling()
  visible.value = false
  
  // 重置状态
  setTimeout(() => {
    progress.value = 0
    currentMessage.value = '正在初始化...'
    errorMessage.value = ''
    isCompleted.value = false
    stages.value.forEach(stage => {
      stage.status = 'pending'
      stage.count = null
    })
  }, 300)
}

watch(() => props.taskId, (newTaskId) => {
  if (newTaskId && visible.value) {
    startPolling()
  }
})

watch(visible, (newVisible) => {
  if (newVisible && props.taskId) {
    startPolling()
  } else if (!newVisible) {
    stopPolling()
  }
})
</script>

<style scoped>
/* 移除所有自定义样式，完全使用 Tailwind CSS */
:deep(.el-dialog) {
  border-radius: 2rem;
  overflow: hidden;
  box-shadow: 0 40px 80px -20px rgba(0, 0, 0, 0.3);
}

:deep(.el-dialog__header) {
  margin: 0;
  padding: 2rem 2rem 0.5rem;
  text-align: center;
}

:deep(.el-dialog__title) {
  font-weight: 900;
  font-size: 1.25rem;
  color: #111827;
  letter-spacing: -0.025em;
}

:deep(.el-dialog__body) {
  padding: 0;
}

:deep(.el-dialog__footer) {
  padding: 0 2rem 2.5rem;
}

.animate-fade-in-up {
  animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.animate-scale-in {
  animation: scaleIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.animate-ripple {
  animation: ripple 2s infinite cubic-bezier(0, 0, 0.2, 1);
}

.animate-shimmer {
  animation: shimmer 2s infinite linear;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.5);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes ripple {
  0% {
    transform: scale(1);
    opacity: 0.5;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}

@keyframes shimmer {
  from {
    transform: translateX(-100%);
  }
  to {
    transform: translateX(100%);
  }
}
</style>
