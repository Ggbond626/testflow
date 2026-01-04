<template>
  <el-dialog
    v-model="dialogVisible"
    title="文档内容"
    width="800px"
    :close-on-click-modal="false"
    @close="handleClose"
    align-center
    class="document-viewer-dialog"
  >
    <!-- 文档基本信息 -->
    <div class="mb-4 pb-4 border-b border-gray-200">
      <div class="flex items-center gap-3 mb-3">
        <el-icon :size="24" class="text-blue-500"><Document /></el-icon>
        <h4 class="text-lg font-bold text-gray-900">{{ document?.filename }}</h4>
      </div>
      <div class="flex flex-wrap gap-x-6 gap-y-2 text-sm text-gray-600">
        <div class="flex items-center gap-1">
          <span class="text-gray-400">文件类型：</span>
          <span class="font-medium uppercase">{{ document?.file_type }}</span>
        </div>
        <div class="flex items-center gap-1">
          <span class="text-gray-400">文件大小：</span>
          <span class="font-medium">{{ formatFileSize(document?.file_size || 0) }}</span>
        </div>
        <div class="flex items-center gap-1">
          <span class="text-gray-400 whitespace-nowrap">上传时间：</span>
          <span class="font-medium whitespace-nowrap">{{ formatDate(document?.upload_time || '') }}</span>
        </div>
        <div v-if="imageCount > 0" class="flex items-center gap-1">
          <span class="text-gray-400">图片数量：</span>
          <span class="font-medium text-blue-600">{{ imageCount }} 张</span>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="py-12 text-center">
      <el-icon class="is-loading text-4xl text-blue-500 mb-4"><Loading /></el-icon>
      <p class="text-gray-500">正在加载文档内容...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="py-12 text-center">
      <el-icon :size="48" class="text-red-400 mb-4"><CircleClose /></el-icon>
      <p class="text-red-600 font-medium mb-2">内容提取失败</p>
      <p class="text-gray-500 text-sm mb-4">{{ error }}</p>
      <button
        @click="loadContent"
        class="px-4 py-2 bg-black text-white rounded-xl text-sm font-bold hover:bg-gray-800 transition-colors"
      >
        重试
      </button>
    </div>

    <!-- 文档内容 -->
    <div v-else class="content-area">
      <!-- 文本内容区域 -->
      <div class="mb-6">
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-medium text-gray-700">📝 提取内容</span>
          <span class="text-xs text-gray-400">{{ contentLength }} 字符</span>
        </div>
        <div class="content-scroll bg-gray-50 rounded-xl p-4 border border-gray-200">
          <pre class="whitespace-pre-wrap text-sm text-gray-700 font-mono leading-relaxed">{{ content }}</pre>
        </div>
      </div>

      <!-- 图片列表区域 -->
      <div v-if="images.length > 0" class="image-section">
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-medium text-gray-700">🖼️ 文档图片 ({{ images.length }}张)</span>
        </div>
        <div class="image-grid">
          <div
            v-for="(image, index) in images"
            :key="image.id"
            class="image-item"
            @click="openImagePreview(index)"
          >
            <div class="image-thumbnail">
              <img
                :src="getImageUrl(image)"
                :alt="image.alt_text || `图片 ${index + 1}`"
                @error="handleImageError($event, index)"
              />
              <div class="image-overlay">
                <el-icon :size="24"><ZoomIn /></el-icon>
              </div>
            </div>
            <div class="image-info">
              <span class="image-name">图片 {{ index + 1 }}</span>
              <span class="image-size">{{ formatFileSize(image.image_size) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end pt-4">
        <button
          @click="handleClose"
          class="px-6 py-2.5 rounded-xl text-gray-600 font-bold hover:bg-gray-100 transition-all border border-gray-200"
        >
          关闭
        </button>
      </div>
    </template>
  </el-dialog>

  <!-- 图片预览对话框 -->
  <el-dialog
    v-model="previewVisible"
    :title="`图片预览 - ${currentPreviewIndex + 1}/${images.length}`"
    width="90%"
    :close-on-click-modal="true"
    align-center
    class="image-preview-dialog"
  >
    <div class="preview-container">
      <button
        v-if="images.length > 1"
        class="preview-nav prev"
        @click="prevImage"
        :disabled="currentPreviewIndex === 0"
      >
        <el-icon :size="32"><ArrowLeft /></el-icon>
      </button>
      
      <div class="preview-image-wrapper">
        <img
          v-if="currentPreviewImage"
          :src="getImageUrl(currentPreviewImage)"
          :alt="currentPreviewImage.alt_text || `图片 ${currentPreviewIndex + 1}`"
          class="preview-image"
        />
      </div>
      
      <button
        v-if="images.length > 1"
        class="preview-nav next"
        @click="nextImage"
        :disabled="currentPreviewIndex === images.length - 1"
      >
        <el-icon :size="32"><ArrowRight /></el-icon>
      </button>
    </div>
    
    <div v-if="currentPreviewImage" class="preview-info">
      <span>尺寸: {{ currentPreviewImage.width || '未知' }} × {{ currentPreviewImage.height || '未知' }}</span>
      <span>格式: {{ currentPreviewImage.image_format?.toUpperCase() }}</span>
      <span>大小: {{ formatFileSize(currentPreviewImage.image_size) }}</span>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Document, Loading, CircleClose, ZoomIn, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import api from '@/api'

interface RequirementDoc {
  id: number
  filename: string
  file_size: number
  file_type: string
  upload_time: string
  is_extracted: boolean
  extract_error?: string
  has_images?: boolean
  image_count?: number
}

interface RequirementImage {
  id: number
  requirement_file_id: number
  image_path: string
  image_format: string
  image_size: number
  position_index: number
  width?: number
  height?: number
  alt_text?: string
  created_at: string
}

interface FileContentResponse {
  id: number
  filename: string
  file_type: string
  extracted_content?: string | null
  is_extracted: boolean
  extract_error?: string | null
  has_images?: boolean
  image_count?: number
  requirement_points?: any[]
  images?: RequirementImage[]
}

const props = defineProps<{
  visible: boolean
  document: RequirementDoc | null
  projectId: number
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'close'): void
}>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const loading = ref(false)
const content = ref<string>('')
const error = ref<string | null>(null)
const images = ref<RequirementImage[]>([])
const imageCount = ref(0)

// 图片预览状态
const previewVisible = ref(false)
const currentPreviewIndex = ref(0)

const contentLength = computed(() => content.value?.length || 0)
const currentPreviewImage = computed(() => images.value[currentPreviewIndex.value] || null)

// 获取图片URL
const getImageUrl = (image: RequirementImage) => {
  // 使用后端API获取图片
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  return `${baseUrl}/projects/${props.projectId}/requirements/files/${image.requirement_file_id}/images/${image.id}`
}

// 处理图片加载错误
const handleImageError = (event: Event, index: number) => {
  const target = event.target as HTMLImageElement
  target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiB2aWV3Qm94PSIwIDAgMTAwIDEwMCI+PHJlY3Qgd2lkdGg9IjEwMCIgaGVpZ2h0PSIxMDAiIGZpbGw9IiNlZWUiLz48dGV4dCB4PSI1MCIgeT0iNTAiIGZvbnQtc2l6ZT0iMTIiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIiBmaWxsPSIjOTk5Ij7lm77niYfliqDovb3lpLHotKU8L3RleHQ+PC9zdmc+'
}

// 打开图片预览
const openImagePreview = (index: number) => {
  currentPreviewIndex.value = index
  previewVisible.value = true
}

// 上一张图片
const prevImage = () => {
  if (currentPreviewIndex.value > 0) {
    currentPreviewIndex.value--
  }
}

// 下一张图片
const nextImage = () => {
  if (currentPreviewIndex.value < images.value.length - 1) {
    currentPreviewIndex.value++
  }
}

// 加载文档内容
const loadContent = async () => {
  if (!props.document) return

  loading.value = true
  error.value = null
  content.value = ''
  images.value = []
  imageCount.value = 0

  try {
    const response = await api.get<FileContentResponse>(
      `/projects/${props.projectId}/requirements/files/${props.document.id}/content`
    )
    
    const data = response as unknown as FileContentResponse
    
    if (data.is_extracted && data.extracted_content) {
      content.value = data.extracted_content
    } else if (data.extract_error) {
      error.value = data.extract_error
    } else {
      error.value = '文档内容尚未提取'
    }
    
    // 加载图片信息
    if (data.images && data.images.length > 0) {
      images.value = data.images
      imageCount.value = data.images.length
    } else if (data.has_images && data.image_count) {
      imageCount.value = data.image_count
    }
  } catch (err: any) {
    console.error('加载文档内容失败:', err)
    error.value = err.response?.data?.detail || '加载文档内容失败'
  } finally {
    loading.value = false
  }
}

// 关闭对话框
const handleClose = () => {
  emit('update:visible', false)
  emit('close')
  // 重置状态
  previewVisible.value = false
  currentPreviewIndex.value = 0
}

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / 1024 / 1024).toFixed(2) + ' MB'
}

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 监听对话框打开
watch(() => props.visible, (newVal) => {
  if (newVal && props.document) {
    loadContent()
  }
})
</script>

<style scoped>
.content-scroll {
  max-height: 300px;
  overflow-y: auto;
}

.content-scroll::-webkit-scrollbar {
  width: 6px;
}

.content-scroll::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.content-scroll::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.content-scroll::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}

/* 图片网格布局 */
.image-section {
  border-top: 1px solid #e5e7eb;
  padding-top: 16px;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}

.image-item {
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
}

.image-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
  transform: translateY(-2px);
}

.image-thumbnail {
  position: relative;
  width: 100%;
  height: 100px;
  background-color: #f9fafb;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.image-thumbnail img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.image-overlay {
  position: absolute;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
  color: white;
}

.image-item:hover .image-overlay {
  opacity: 1;
}

.image-info {
  padding: 8px;
  background-color: #f9fafb;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.image-name {
  font-size: 12px;
  font-weight: 500;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.image-size {
  font-size: 11px;
  color: #9ca3af;
}

/* 图片预览对话框 */
.preview-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  position: relative;
}

.preview-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.5);
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  z-index: 10;
}

.preview-nav:hover:not(:disabled) {
  background-color: rgba(0, 0, 0, 0.7);
}

.preview-nav:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.preview-nav.prev {
  left: 16px;
}

.preview-nav.next {
  right: 16px;
}

.preview-image-wrapper {
  max-width: 100%;
  max-height: 70vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
  border-radius: 8px;
}

.preview-info {
  display: flex;
  justify-content: center;
  gap: 24px;
  padding: 16px;
  color: #6b7280;
  font-size: 14px;
  border-top: 1px solid #e5e7eb;
  margin-top: 16px;
}

:deep(.el-dialog__header) {
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e5e7eb;
}

:deep(.el-dialog__body) {
  padding: 20px 24px;
  max-height: 70vh;
  overflow-y: auto;
}

:deep(.el-dialog__footer) {
  padding: 0 24px 20px;
}

/* 图片预览对话框特殊样式 */
:deep(.image-preview-dialog .el-dialog__body) {
  padding: 0;
  max-height: none;
}
</style>
