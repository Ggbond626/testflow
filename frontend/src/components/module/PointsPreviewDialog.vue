<template>
  <el-dialog
    v-model="dialogVisible"
    title="生成结果预览"
    width="720px"
    :close-on-click-modal="false"
    @close="handleClose"
    align-center
    class="preview-dialog"
  >
    <!-- 统计信息 -->
    <div class="mb-4 pb-4 border-b border-gray-200">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <el-icon :size="24" class="text-green-500"><CircleCheck /></el-icon>
          <span class="text-lg font-bold text-gray-900">
            共生成 <span class="text-blue-600">{{ points.length }}</span> 个需求点
          </span>
        </div>
        <div class="flex items-center gap-2 text-sm text-gray-500">
          <el-icon><MagicStick /></el-icon>
          <span>AI智能生成</span>
        </div>
      </div>
    </div>

    <!-- 需求点列表 -->
    <div class="points-list">
      <div
        v-for="(point, index) in points"
        :key="index"
        class="point-item bg-gray-50 rounded-xl p-4 mb-3 border border-gray-200 hover:border-gray-300 transition-colors"
      >
        <div class="flex items-start gap-3">
          <span class="flex-shrink-0 w-7 h-7 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center text-sm font-bold">
            {{ index + 1 }}
          </span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-2">
              <span 
                class="px-2 py-0.5 rounded text-xs font-medium"
                :class="getPriorityClass(point.priority)"
              >
                {{ getPriorityLabel(point.priority) }}
              </span>
              <span v-if="point.category" class="text-xs text-gray-400">
                {{ getCategoryLabel(point.category) }}
              </span>
            </div>
            <p class="text-gray-700 text-sm leading-relaxed">{{ point.content }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="points.length === 0" class="py-12 text-center">
      <el-icon :size="48" class="text-gray-300 mb-4"><Document /></el-icon>
      <p class="text-gray-500">暂无生成的需求点</p>
    </div>

    <!-- 保存中状态 -->
    <div v-if="saving" class="absolute inset-0 bg-white/80 flex items-center justify-center z-10">
      <div class="text-center">
        <el-icon class="is-loading text-4xl text-blue-500 mb-4"><Loading /></el-icon>
        <p class="text-gray-600">正在保存需求点...</p>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-between items-center pt-4">
        <p class="text-sm text-gray-500">
          <el-icon class="text-yellow-500"><Warning /></el-icon>
          确认保存后，需求点将添加到当前文档
        </p>
        <div class="flex gap-3">
          <button
            @click="handleCancel"
            :disabled="saving"
            class="px-6 py-2.5 rounded-xl text-gray-600 font-bold hover:bg-gray-100 transition-all border border-gray-200 disabled:opacity-50"
          >
            取消
          </button>
          <button
            @click="handleSave"
            :disabled="saving || points.length === 0"
            class="px-6 py-2.5 bg-black text-white rounded-xl font-bold hover:bg-gray-800 transition-all shadow-lg shadow-black/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ saving ? '保存中...' : '确认保存' }}
          </button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheck, MagicStick, Document, Loading, Warning } from '@element-plus/icons-vue'
import api from '@/api'

interface GeneratedPoint {
  content: string
  order_index: number
  priority?: string
  category?: string
  created_by_ai: boolean
}

const props = defineProps<{
  visible: boolean
  points: GeneratedPoint[]
  projectId: number
  moduleId: number
  fileId: number
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'close'): void
  (e: 'saved'): void
  (e: 'cancel'): void
}>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const saving = ref(false)

// 获取优先级样式
const getPriorityClass = (priority?: string) => {
  switch (priority?.toLowerCase()) {
    case 'high':
      return 'bg-red-100 text-red-600'
    case 'medium':
      return 'bg-yellow-100 text-yellow-600'
    case 'low':
      return 'bg-green-100 text-green-600'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

// 获取优先级标签
const getPriorityLabel = (priority?: string) => {
  switch (priority?.toLowerCase()) {
    case 'high':
      return '高优先级'
    case 'medium':
      return '中优先级'
    case 'low':
      return '低优先级'
    default:
      return '普通'
  }
}

// 获取分类标签
const getCategoryLabel = (category?: string) => {
  switch (category?.toLowerCase()) {
    case 'functional':
      return '功能需求'
    case 'non-functional':
      return '非功能需求'
    case 'business':
      return '业务需求'
    case 'technical':
      return '技术需求'
    default:
      return category || ''
  }
}

// 保存需求点
const handleSave = async () => {
  if (props.points.length === 0) return

  saving.value = true

  try {
    // 调用批量创建API
    const response = await api.post(
      `/api/projects/${props.projectId}/modules/${props.moduleId}/requirements/files/${props.fileId}/points/batch`,
      {
        points: props.points.map((point, index) => ({
          content: point.content,
          order_index: point.order_index ?? index,
          priority: point.priority || 'medium',
          created_by_ai: true
        }))
      }
    )

    ElMessage.success(`成功保存 ${props.points.length} 个需求点`)
    emit('saved')
    emit('update:visible', false)
  } catch (err: any) {
    console.error('保存需求点失败:', err)
    ElMessage.error(err.response?.data?.detail || '保存失败，请重试')
  } finally {
    saving.value = false
  }
}

// 取消
const handleCancel = () => {
  emit('cancel')
  emit('update:visible', false)
}

// 关闭
const handleClose = () => {
  if (saving.value) return
  emit('close')
}
</script>

<style scoped>
.points-list {
  max-height: 400px;
  overflow-y: auto;
}

.points-list::-webkit-scrollbar {
  width: 6px;
}

.points-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.points-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.points-list::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}

:deep(.el-dialog__header) {
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e5e7eb;
}

:deep(.el-dialog__body) {
  padding: 20px 24px;
  position: relative;
}

:deep(.el-dialog__footer) {
  padding: 0 24px 20px;
}
</style>
