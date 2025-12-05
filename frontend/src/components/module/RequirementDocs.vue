<template>
  <div class="requirement-docs">
    <!-- 操作栏 -->
    <div class="mb-6 flex justify-between items-center">
      <div>
        <h3 class="text-lg font-bold text-gray-900">需求文档管理</h3>
        <p class="text-sm text-gray-500 mt-1">上传需求文档，系统将自动提取内容并生成需求点</p>
      </div>
      <button
        @click="showUploadDialog = true"
        class="bg-black hover:bg-gray-800 text-white px-4 py-2 rounded-xl font-bold shadow-lg shadow-black/20 transition-all transform hover:-translate-y-0.5 flex items-center gap-2"
      >
        <el-icon><Upload /></el-icon>
        上传文档
      </button>
    </div>

    <!-- 文档列表 -->
    <div v-if="loading" class="py-12">
      <el-skeleton :rows="3" animated />
    </div>

    <div v-else-if="documents.length === 0" class="text-center py-16">
      <el-empty description="暂无需求文档">
        <button
          @click="showUploadDialog = true"
          class="mt-4 px-6 py-2 bg-black text-white rounded-xl text-sm font-bold hover:bg-gray-800 transition-colors"
        >
          上传第一个文档
        </button>
      </el-empty>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="doc in documents"
        :key="doc.id"
        class="bg-white/50 border border-white/60 rounded-2xl p-6 hover:bg-white/80 hover:shadow-lg transition-all"
      >
        <div class="flex justify-between items-start">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <el-icon :size="24" class="text-blue-500"><Document /></el-icon>
              <h4 class="text-lg font-bold text-gray-900">{{ doc.filename }}</h4>
              <!-- 图片数量标识 -->
              <span
                v-if="doc.has_images && (doc.image_count || 0) > 0"
                class="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium rounded-full"
              >
                <el-icon :size="12"><Picture /></el-icon>
                {{ doc.image_count }} 张图片
              </span>
            </div>
            <div class="flex flex-wrap gap-x-6 gap-y-2 text-sm text-gray-600 mt-4">
              <div class="flex items-center gap-1">
                <span class="text-gray-400">文件大小：</span>
                <span class="font-medium">{{ formatFileSize(doc.file_size) }}</span>
              </div>
              <div class="flex items-center gap-1">
                <span class="text-gray-400">文件类型：</span>
                <span class="font-medium uppercase">{{ doc.file_type }}</span>
              </div>
              <div class="flex items-center gap-1">
                <span class="text-gray-400 whitespace-nowrap">上传时间：</span>
                <span class="font-medium whitespace-nowrap">{{ formatDate(doc.upload_time) }}</span>
              </div>
            </div>
          </div>
          <div class="flex gap-2 flex-wrap">
            <button
              @click="viewDocument(doc)"
              class="px-4 py-2 border border-gray-200 text-gray-700 rounded-xl text-sm font-bold hover:bg-gray-50 transition-colors flex items-center gap-2"
            >
              <el-icon><View /></el-icon>
              查看
            </button>
            <button
              @click="generateRequirementPoints(doc)"
              :disabled="!doc.is_extracted"
              :title="!doc.is_extracted ? '文档内容尚未提取，无法生成需求点' : '使用AI智能体分析文档并生成需求点'"
              class="px-4 py-2 bg-black text-white rounded-xl text-sm font-bold hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <el-icon><MagicStick /></el-icon>
              生成需求点
            </button>
            <button
              @click="generateAllTestArtifacts(doc)"
              :disabled="!doc.is_extracted || generatingAll"
              :title="!doc.is_extracted ? '文档内容尚未提取，无法生成' : '一键生成：需求点 → 测试点 → 测试用例'"
              class="px-4 py-2 bg-black text-white rounded-xl text-sm font-bold hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <el-icon :class="{ 'is-loading': generatingAll }"><Lightning /></el-icon>
              {{ generatingAll ? '生成中...' : '生成测试用例' }}
            </button>
            <button
              @click="deleteDocument(doc.id)"
              class="px-4 py-2 border border-red-200 text-red-600 rounded-xl text-sm font-bold hover:bg-red-50 transition-colors flex items-center gap-2"
            >
              <el-icon><Delete /></el-icon>
              删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 文档内容查看对话框 -->
    <DocumentViewerDialog
      v-model:visible="showViewerDialog"
      :document="selectedDocument"
      :project-id="projectId"
      @close="handleViewerClose"
    />

    <!-- 生成需求点对话框 -->
    <GeneratePointsDialog
      v-model:visible="showGenerateDialog"
      :document="selectedDocument"
      :document-content="selectedDocumentContent"
      :document-images="selectedDocumentImages"
      :project-id="projectId"
      :module-id="moduleId"
      @close="handleGenerateClose"
      @success="handleGenerateSuccess"
    />

    <!-- 一键生成进度对话框 -->
    <GenerationProgressDialog
      v-model="showProgressDialog"
      :task-id="currentTaskId"
      @completed="handleGenerationCompleted"
    />

    <!-- 需求点预览对话框 -->
    <PointsPreviewDialog
      v-model:visible="showPreviewDialog"
      :points="generatedPoints"
      :project-id="projectId"
      :module-id="moduleId"
      :file-id="selectedDocument?.id || 0"
      @close="handlePreviewClose"
      @saved="handlePointsSaved"
      @cancel="handlePreviewCancel"
    />

    <!-- 上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传需求文档"
      width="560px"
      :close-on-click-modal="false"
      align-center
      class="upload-dialog"
    >
      <div class="space-y-4">
        <el-upload
          ref="uploadRef"
          drag
          :auto-upload="false"
          :limit="1"
          :on-change="handleFileChange"
          :on-exceed="handleExceed"
          accept=".txt,.docx,.md"
          class="w-full"
        >
          <el-icon class="text-5xl text-gray-400 mb-4"><UploadFilled /></el-icon>
          <div class="text-base text-gray-600 mb-2">
            拖拽文件到此处，或<span class="text-black font-bold">点击上传</span>
          </div>
          <div class="text-sm text-gray-400">
            支持格式：TXT、DOCX、MD（最大 10MB）
          </div>
        </el-upload>
      </div>

      <template #footer>
        <div class="flex justify-end gap-3 pt-4">
          <button 
            @click="showUploadDialog = false" 
            class="px-6 py-2.5 rounded-xl text-gray-600 font-bold hover:bg-gray-100 transition-all border border-gray-200"
          >
            取消
          </button>
          <button 
            @click="handleUpload" 
            :disabled="!selectedFile || uploading" 
            class="px-6 py-2.5 bg-black text-white rounded-xl font-bold hover:bg-gray-800 transition-all shadow-lg shadow-black/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="uploading">上传中...</span>
            <span v-else>确认上传</span>
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type UploadInstance } from 'element-plus'
import { Document, Upload, UploadFilled, Delete, MagicStick, View, Picture, Lightning } from '@element-plus/icons-vue'
import api from '@/api'
import DocumentViewerDialog from './DocumentViewerDialog.vue'
import GeneratePointsDialog from './GeneratePointsDialog.vue'
import PointsPreviewDialog from './PointsPreviewDialog.vue'
import GenerationProgressDialog from './GenerationProgressDialog.vue'

const props = defineProps<{
  projectId: number
  moduleId: number
}>()

const emit = defineEmits<{
  (e: 'switchTab', tab: string): void
}>()

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

const documents = ref<RequirementDoc[]>([])
const loading = ref(false)
const showUploadDialog = ref(false)
const uploading = ref(false)
const selectedFile = ref<File | null>(null)
const uploadRef = ref<UploadInstance>()

// 文档查看对话框状态
const showViewerDialog = ref(false)
const selectedDocument = ref<RequirementDoc | null>(null)

// 生成需求点对话框状态
const showGenerateDialog = ref(false)
const selectedDocumentContent = ref('')

// 需求点预览对话框状态
const showPreviewDialog = ref(false)
const generatedPoints = ref<any[]>([])

// 一键生成测试用例状态
const generatingAll = ref(false)
const showProgressDialog = ref(false)
const currentTaskId = ref<string | null>(null)

// 加载文档列表
const loadDocuments = async () => {
  loading.value = true
  try {
    // 使用模块级API路径，api实例会自动添加baseURL和认证token
    const response = await api.get(`/api/projects/${props.projectId}/modules/${props.moduleId}/requirements/files`)
    documents.value = response as any
  } catch (error: any) {
    console.error('加载文档列表失败:', error)
    ElMessage.error('加载文档列表失败')
  } finally {
    loading.value = false
  }
}

// 文件选择
const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
}

const handleExceed = () => {
  ElMessage.warning('一次只能上传一个文件')
}

// 上传文件
const handleUpload = async () => {
  if (!selectedFile.value) return

  uploading.value = true
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  // module_id现在在路径中，不需要单独传递
  // formData.append('module_id', props.moduleId.toString())

  try {
    // 使用模块级API路径，api实例会自动添加baseURL和认证token
    await api.post(`/api/projects/${props.projectId}/modules/${props.moduleId}/requirements/files`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success('文档上传成功')
    showUploadDialog.value = false
    selectedFile.value = null
    uploadRef.value?.clearFiles()
    loadDocuments()
  } catch (error: any) {
    console.error('上传失败:', error)
    ElMessage.error(error.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

// 删除文档
const deleteDocument = async (docId: number) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除此文档吗？删除后将无法恢复！',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 使用模块级API路径，api实例会自动添加baseURL和认证token
    await api.delete(`/api/projects/${props.projectId}/modules/${props.moduleId}/requirements/files/${docId}`)
    ElMessage.success('文档删除成功')
    loadDocuments()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 查看文档内容
const viewDocument = (doc: RequirementDoc) => {
  selectedDocument.value = doc
  showViewerDialog.value = true
}

// 关闭文档查看对话框
const handleViewerClose = () => {
  showViewerDialog.value = false
  selectedDocument.value = null
}

// 文档图片列表
const selectedDocumentImages = ref<any[]>([])

// 生成需求点
const generateRequirementPoints = async (doc: RequirementDoc) => {
  if (!doc.is_extracted) {
    ElMessage.warning('文档内容尚未提取，无法生成需求点')
    return
  }

  // 先获取文档内容（包含图片信息）
  try {
    const response = await api.get(`/api/projects/${props.projectId}/requirements/files/${doc.id}/content`) as any
    if (response.is_extracted && response.extracted_content) {
      selectedDocument.value = {
        ...doc,
        has_images: response.has_images,
        image_count: response.image_count
      }
      selectedDocumentContent.value = response.extracted_content
      // 保存图片信息用于多模态分析
      selectedDocumentImages.value = response.images || []
      showGenerateDialog.value = true
    } else {
      ElMessage.error(response.extract_error || '文档内容尚未提取')
    }
  } catch (error: any) {
    console.error('获取文档内容失败:', error)
    ElMessage.error(error.response?.data?.detail || '获取文档内容失败')
  }
}

// 关闭生成对话框
const handleGenerateClose = () => {
  showGenerateDialog.value = false
}

// 生成成功，显示预览
const handleGenerateSuccess = (points: any[]) => {
  generatedPoints.value = points
  showGenerateDialog.value = false
  showPreviewDialog.value = true
}

// 关闭预览对话框
const handlePreviewClose = () => {
  showPreviewDialog.value = false
}

// 一键生成测试用例（需求点 → 测试点 → 测试用例 → 优化）
const generateAllTestArtifacts = async (doc: RequirementDoc) => {
  if (!doc.is_extracted) {
    ElMessage.warning('文档内容尚未提取，无法生成测试用例')
    return
  }

  try {
    await ElMessageBox.confirm(
      '整个过程可能持续数分钟，期间请耐心等待任务完成，是否继续？',
      '确认一键生成',
      {
        confirmButtonText: '开始生成',
        cancelButtonText: '取消',
        type: 'info',
        distinguishCancelAndClose: true
      }
    )

    generatingAll.value = true

    // 调用后端 API 执行完整流程
    const response = await api.post(
      `/api/projects/${props.projectId}/modules/${props.moduleId}/requirements/files/${doc.id}/generate-all`
    ) as any

    currentTaskId.value = response.task_id
    showProgressDialog.value = true

  } catch (error: any) {
    if (error !== 'cancel' && error !== 'close') {
      console.error('一键生成失败:', error)
      ElMessage.error(error.response?.data?.detail || '生成失败，请重试')
    }
    generatingAll.value = false
  }
}

// 生成完成的回调
const handleGenerationCompleted = async () => {
  generatingAll.value = false
  ElMessage.success('测试用例生成完成！')
  // 刷新页面数据
  await loadDocuments()
  // 通知父组件切换到测试用例标签页
  emit('switchTab', 'testcases')
}

// 取消预览
const handlePreviewCancel = () => {
  showPreviewDialog.value = false
  generatedPoints.value = []
}

// 需求点保存成功
const handlePointsSaved = () => {
  showPreviewDialog.value = false
  generatedPoints.value = []
  selectedDocument.value = null
  selectedDocumentContent.value = ''
  selectedDocumentImages.value = []
  // 刷新文档列表
  loadDocuments()
  ElMessage.success('需求点已保存，正在跳转到需求点列表')
  // 跳转到需求点列表页面 (Requirements 2.8)
  emit('switchTab', 'points')
}

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / 1024 / 1024).toFixed(2) + ' MB'
}

// 格式化日期
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
:deep(.el-upload-dragger) {
  border-radius: 1rem;
  border: 2px dashed #d1d5db;
  background-color: #f9fafb;
  transition: all 0.3s;
}

:deep(.el-upload-dragger:hover) {
  border-color: #9ca3af;
  background-color: #f3f4f6;
}
</style>

