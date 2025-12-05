<template>
  <el-dialog
    v-model="dialogVisible"
    title="生成需求点"
    width="560px"
    :close-on-click-modal="false"
    :close-on-press-escape="!generating"
    :show-close="!generating"
    @close="handleClose"
    align-center
    class="generate-dialog"
  >
    <!-- 生成中状态 -->
    <div v-if="generating" class="py-8 text-center">
      <div class="mb-6">
        <el-icon class="is-loading text-5xl text-black"><Loading /></el-icon>
      </div>
      <h4 class="text-lg font-bold text-gray-900 mb-2">
        {{ hasImages ? '正在分析文档内容和图片...' : '正在分析文档内容...' }}
      </h4>
      <p class="text-gray-500 text-sm mb-6">{{ currentStep }}</p>
      
      <!-- 进度条 -->
      <div class="w-full bg-gray-200 rounded-full h-2 mb-4">
        <div 
          class="bg-black h-2 rounded-full transition-all duration-500"
          :style="{ width: progress + '%' }"
        ></div>
      </div>
      
      <!-- 多模态分析提示 -->
      <p v-if="hasImages" class="text-xs text-amber-500 mb-2">
        <el-icon class="mr-1"><Picture /></el-icon>
        正在分析 {{ imageCount }} 张图片，这可能需要较长时间
      </p>
      <p class="text-xs text-gray-400">请耐心等待，AI正在分析您的需求文档</p>
    </div>

    <!-- 生成成功状态 -->
    <div v-else-if="success" class="py-8 text-center">
      <div class="mb-6">
        <el-icon :size="48" class="text-green-500"><CircleCheck /></el-icon>
      </div>
      <h4 class="text-lg font-bold text-gray-900 mb-2">生成完成！</h4>
      <p class="text-gray-500 text-sm">
        成功生成 <span class="font-bold text-blue-600">{{ generatedPoints.length }}</span> 个需求点
      </p>
      
      <!-- 多模态分析结果提示 -->
      <div v-if="hasImages && multimodalUsed" class="mt-4 text-sm text-green-600">
        <el-icon class="mr-1"><Picture /></el-icon>
        已分析 {{ imageCount }} 张图片内容
      </div>
      
      <!-- 模型不支持多模态的提示 (Requirements 5.5) -->
      <div v-if="hasImages && !modelSupportsMultimodal" class="mt-4 p-3 bg-amber-50 rounded-xl text-left">
        <div class="flex items-start gap-2 text-sm text-amber-700">
          <el-icon class="mt-0.5 flex-shrink-0"><Warning /></el-icon>
          <div>
            <p class="font-medium">当前模型不支持图片分析</p>
            <p class="text-amber-600 mt-1">
              本次仅分析了文本内容。如需分析图片，请在设置中切换到支持视觉的模型（如 GPT-4V、Claude 3 Vision）。
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- 生成失败状态 -->
    <div v-else-if="error" class="py-8 text-center">
      <div class="mb-6">
        <el-icon :size="48" class="text-red-400"><CircleClose /></el-icon>
      </div>
      <h4 class="text-lg font-bold text-gray-900 mb-2">生成失败</h4>
      <p class="text-red-500 text-sm mb-4">{{ error }}</p>
      <button
        @click="startGeneration"
        class="px-4 py-2 bg-black text-white rounded-xl text-sm font-bold hover:bg-gray-800 transition-colors"
      >
        重试
      </button>
    </div>

    <!-- 初始状态 - 确认开始 -->
    <div v-else class="py-6">
      <div class="flex items-start gap-4 mb-6">
        <el-icon :size="32" class="text-blue-500 mt-1"><MagicStick /></el-icon>
        <div>
          <h4 class="text-lg font-bold text-gray-900 mb-2">AI智能分析</h4>
          <p class="text-gray-600 text-sm">
            系统将使用AI智能体分析文档 <span class="font-medium">{{ document?.filename }}</span> 的内容，
            自动提取结构化的需求点。
          </p>
        </div>
      </div>
      
      <div class="bg-gray-50 rounded-xl p-4 mb-4 space-y-3">
        <div class="flex items-center gap-2 text-sm text-gray-600">
          <el-icon class="text-blue-500"><InfoFilled /></el-icon>
          <span>文档内容长度：{{ contentLength }} 字符</span>
        </div>
        
        <!-- 图片分析提示 (Requirements 5.1) -->
        <div v-if="hasImages" class="flex items-center gap-2 text-sm text-blue-600">
          <el-icon class="text-blue-500"><Picture /></el-icon>
          <span>将分析文档中的 <span class="font-bold">{{ imageCount }}</span> 张图片</span>
        </div>
        
        <!-- 多模态分析时间提示 -->
        <div v-if="hasImages" class="flex items-center gap-2 text-sm text-amber-600">
          <el-icon class="text-amber-500"><Warning /></el-icon>
          <span>包含图片分析，处理时间可能较长，请耐心等待</span>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end gap-3 pt-4">
        <button
          v-if="!generating"
          @click="handleClose"
          class="px-6 py-2.5 rounded-xl text-gray-600 font-bold hover:bg-gray-100 transition-all border border-gray-200"
        >
          {{ success ? '关闭' : '取消' }}
        </button>
        <button
          v-if="!generating && !success && !error"
          @click="startGeneration"
          class="px-6 py-2.5 bg-black text-white rounded-xl font-bold hover:bg-gray-800 transition-all shadow-lg shadow-black/20"
        >
          开始生成
        </button>
        <button
          v-if="success"
          @click="handlePreview"
          class="px-6 py-2.5 bg-black text-white rounded-xl font-bold hover:bg-gray-800 transition-all shadow-lg shadow-black/20"
        >
          预览结果
        </button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Loading, CircleCheck, CircleClose, MagicStick, InfoFilled, Picture, Warning } from '@element-plus/icons-vue'
import { agentApi } from '@/api/agent'

interface RequirementImage {
  id: number
  image_path: string
  image_format: string
  image_size: number
  position_index: number
  width?: number
  height?: number
  alt_text?: string
}

interface RequirementDoc {
  id: number
  filename: string
  file_size: number
  file_type: string
  upload_time: string
  is_extracted: boolean
  extract_error?: string
  extracted_content?: string
  has_images?: boolean
  image_count?: number
  images?: RequirementImage[]
}

interface GeneratedPoint {
  content: string
  order_index: number
  priority?: string
  category?: string
  created_by_ai: boolean
}

const props = defineProps<{
  visible: boolean
  document: RequirementDoc | null
  documentContent: string
  projectId: number
  moduleId: number
  documentImages?: RequirementImage[]  // 文档图片列表
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'close'): void
  (e: 'success', points: GeneratedPoint[]): void
}>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// 状态
const generating = ref(false)
const success = ref(false)
const error = ref<string | null>(null)
const progress = ref(0)
const currentStep = ref('准备中...')
const generatedPoints = ref<GeneratedPoint[]>([])
const multimodalUsed = ref(false)  // 是否使用了多模态分析
const modelSupportsMultimodal = ref(true)  // 模型是否支持多模态

// 计算属性
const contentLength = computed(() => props.documentContent?.length || 0)

// 检测文档是否包含图片
const hasImages = computed(() => {
  return (props.document?.has_images && (props.document?.image_count || 0) > 0) ||
         (props.documentImages && props.documentImages.length > 0)
})

// 图片数量
const imageCount = computed(() => {
  return props.document?.image_count || props.documentImages?.length || 0
})

// 获取图片路径列表
const imagePaths = computed(() => {
  if (props.documentImages && props.documentImages.length > 0) {
    return props.documentImages.map(img => img.image_path)
  }
  return []
})

// 开始生成
const startGeneration = async () => {
  if (!props.document || !props.documentContent) {
    error.value = '文档内容未提取'
    return
  }

  generating.value = true
  success.value = false
  error.value = null
  progress.value = 10
  multimodalUsed.value = false
  modelSupportsMultimodal.value = true
  
  // 根据是否有图片设置不同的初始提示
  if (hasImages.value) {
    currentStep.value = `正在准备分析文档和${imageCount.value}张图片...`
  } else {
    currentStep.value = '正在调用AI智能体...'
  }

  try {
    // 多模态分析需要更长时间，调整进度更新间隔
    const progressUpdateInterval = hasImages.value ? 1200 : 800
    
    // 模拟进度更新
    const progressInterval = setInterval(() => {
      if (progress.value < 90) {
        // 多模态分析进度更新更慢
        const increment = hasImages.value ? Math.random() * 10 : Math.random() * 15
        progress.value += increment
        
        if (hasImages.value) {
          // 多模态分析的步骤提示
          if (progress.value > 20 && progress.value < 40) {
            currentStep.value = '正在分析文档文本内容...'
          } else if (progress.value >= 40 && progress.value < 60) {
            currentStep.value = `正在分析${imageCount.value}张图片内容...`
          } else if (progress.value >= 60 && progress.value < 80) {
            currentStep.value = '正在整合文本和图片信息...'
          } else if (progress.value >= 80) {
            currentStep.value = '正在提取需求点...'
          }
        } else {
          // 纯文本分析的步骤提示
          if (progress.value > 30 && progress.value < 60) {
            currentStep.value = '正在分析文档结构...'
          } else if (progress.value >= 60) {
            currentStep.value = '正在提取需求点...'
          }
        }
      }
    }, progressUpdateInterval)

    // 构建请求参数
    const requestParams: any = {
      requirement_content: props.documentContent,
      project_context: `项目ID: ${props.projectId}, 模块ID: ${props.moduleId}`
    }
    
    // 如果有图片，添加图片路径
    if (hasImages.value && imagePaths.value.length > 0) {
      requestParams.image_paths = imagePaths.value
    }

    // 调用需求分析API
    const response = await agentApi.analyzeRequirements(requestParams)

    clearInterval(progressInterval)

    if (response.success && response.data?.requirement_points) {
      progress.value = 100
      currentStep.value = '生成完成！'
      
      // 记录多模态分析信息
      multimodalUsed.value = response.data.multimodal_used || false
      modelSupportsMultimodal.value = response.data.model_supports_multimodal !== false
      
      // 转换为标准格式
      generatedPoints.value = response.data.requirement_points.map((point: any, index: number) => ({
        content: point.content || point.description || '',
        order_index: point.order_index ?? index,
        priority: point.priority || 'medium',
        category: point.category || 'functional',
        created_by_ai: true
      }))

      // 短暂延迟后显示成功状态
      setTimeout(() => {
        generating.value = false
        success.value = true
      }, 500)
    } else {
      throw new Error(response.error || '智能体返回结果为空')
    }
  } catch (err: any) {
    console.error('生成需求点失败:', err)
    generating.value = false
    error.value = err.response?.data?.detail || err.message || '生成失败，请重试'
  }
}

// 预览结果
const handlePreview = () => {
  emit('success', generatedPoints.value)
}

// 关闭对话框
const handleClose = () => {
  if (generating.value) return
  resetState()
  emit('update:visible', false)
  emit('close')
}

// 重置状态
const resetState = () => {
  generating.value = false
  success.value = false
  error.value = null
  progress.value = 0
  currentStep.value = '准备中...'
  generatedPoints.value = []
  multimodalUsed.value = false
  modelSupportsMultimodal.value = true
}

// 监听对话框关闭时重置状态
watch(() => props.visible, (newVal) => {
  if (!newVal) {
    resetState()
  }
})
</script>

<style scoped>
:deep(.el-dialog__header) {
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e5e7eb;
}

:deep(.el-dialog__body) {
  padding: 20px 24px;
}

:deep(.el-dialog__footer) {
  padding: 0 24px 20px;
}
</style>
