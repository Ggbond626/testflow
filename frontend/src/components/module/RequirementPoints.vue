<template>
  <div class="requirement-points">
    <!-- 操作栏 -->
    <div class="mb-6 flex justify-between items-center">
      <div>
        <h3 class="text-lg font-bold text-gray-900">需求点管理</h3>
        <p class="text-sm text-gray-500 mt-1">共 {{ total }} 个需求点</p>
      </div>
      <button
        @click="openAddDialog"
        class="bg-black hover:bg-gray-800 text-white px-4 py-2 rounded-xl font-bold shadow-lg shadow-black/20 transition-all transform hover:-translate-y-0.5 flex items-center gap-2"
      >
        <el-icon><Plus /></el-icon>
        添加需求点
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="py-12">
      <el-skeleton :rows="3" animated />
    </div>

    <!-- 空状态 -->
    <div v-else-if="points.length === 0" class="text-center py-16">
      <el-empty description="暂无需求点">
        <p class="text-sm text-gray-500 mb-4">请上传需求文档生成需求点，或手动添加</p>
        <button
          @click="openAddDialog"
          class="px-6 py-2 bg-black text-white rounded-xl text-sm font-bold hover:bg-gray-800 transition-colors"
        >
          添加第一个需求点
        </button>
      </el-empty>
    </div>

    <!-- 需求点列表 -->
    <div v-else class="space-y-4">
      <div
        v-for="(point, index) in points"
        :key="point.id"
        class="bg-white/50 border border-white/60 rounded-2xl p-6 hover:bg-white/80 hover:shadow-lg transition-all"
      >
        <div class="flex items-start gap-4">
          <div class="flex-shrink-0 w-10 h-10 bg-gray-900 text-white rounded-xl flex items-center justify-center text-sm font-bold">
            {{ (currentPage - 1) * pageSize + index + 1 }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-gray-800 text-base leading-relaxed">{{ point.content }}</div>
            <div class="flex items-center gap-3 mt-3">
              <span :class="getPriorityClass((point as any).priority)">
                {{ getPriorityLabel((point as any).priority) }}
              </span>
            </div>
          </div>
          <div class="flex-shrink-0 flex gap-2">
            <button
              @click="editPoint(point)"
              class="px-3 py-2 border border-gray-200 text-gray-700 rounded-xl text-sm font-bold hover:bg-gray-50 transition-colors"
            >
              <el-icon><Edit /></el-icon>
            </button>
            <button
              @click="deletePoint(point)"
              class="px-3 py-2 border border-red-200 text-red-600 rounded-xl text-sm font-bold hover:bg-red-50 transition-colors"
            >
              <el-icon><Delete /></el-icon>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="total > 0" class="mt-6 flex justify-end">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        background
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="showDialog"
      :title="editingPoint ? '编辑需求点' : '添加需求点'"
      width="560px"
      :close-on-click-modal="false"
      align-center
      append-to-body
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-bold text-gray-700 mb-2">需求点内容 <span class="text-red-500">*</span></label>
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="4"
            placeholder="请输入需求点内容"
            class="custom-textarea"
          />
        </div>
        <div>
          <label class="block text-sm font-bold text-gray-700 mb-2">优先级</label>
          <el-select v-model="form.priority" style="width: 100%" class="custom-select">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3 pt-4">
          <button
            @click="showDialog = false"
            class="px-6 py-2.5 rounded-xl text-gray-600 font-bold hover:bg-gray-100 transition-all border border-gray-200"
          >
            取消
          </button>
          <button
            @click="savePoint"
            :disabled="saving"
            class="px-6 py-2.5 bg-black text-white rounded-xl font-bold hover:bg-gray-800 transition-all shadow-lg shadow-black/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="saving">保存中...</span>
            <span v-else>{{ editingPoint ? '保存' : '添加' }}</span>
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { requirementApi, type RequirementPoint } from '@/api/requirement'

const props = defineProps<{
  projectId: number
  moduleId: number
}>()

const loading = ref(false)
const saving = ref(false)
const points = ref<RequirementPoint[]>([])
const allPoints = ref<RequirementPoint[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const showDialog = ref(false)
const editingPoint = ref<RequirementPoint | null>(null)
const form = ref({ content: '', priority: 'medium' })

async function loadPoints() {
  loading.value = true
  try {
    allPoints.value = await requirementApi.getModuleRequirementPoints(props.projectId, props.moduleId)
    total.value = allPoints.value.length
    updatePaginatedPoints()
  } catch (error: any) {
    if (error.response?.status !== 404) {
      ElMessage.error(error.message || '加载失败')
    }
    allPoints.value = []
    points.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function updatePaginatedPoints() {
  const start = (currentPage.value - 1) * pageSize.value
  points.value = allPoints.value.slice(start, start + pageSize.value)
}

function handlePageChange() {
  updatePaginatedPoints()
}

function handleSizeChange() {
  currentPage.value = 1
  updatePaginatedPoints()
}

function openAddDialog() {
  editingPoint.value = null
  form.value = { content: '', priority: 'medium' }
  showDialog.value = true
}

function editPoint(point: RequirementPoint) {
  editingPoint.value = point
  form.value = { content: point.content, priority: (point as any).priority || 'medium' }
  showDialog.value = true
}

async function savePoint() {
  if (!form.value.content.trim()) {
    ElMessage.warning('请输入需求点内容')
    return
  }
  saving.value = true
  try {
    if (editingPoint.value) {
      await requirementApi.updateModuleRequirementPoint(
        props.projectId, props.moduleId, editingPoint.value.id, form.value
      )
      ElMessage.success('更新成功')
    } else {
      await requirementApi.createModuleRequirementPoint(props.projectId, props.moduleId, form.value)
      ElMessage.success('添加成功')
    }
    showDialog.value = false
    loadPoints()
  } catch (error: any) {
    ElMessage.error(error.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function deletePoint(point: RequirementPoint) {
  try {
    await ElMessageBox.confirm('删除需求点将同时删除关联的测试点，确定删除？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await requirementApi.deleteModuleRequirementPoint(props.projectId, props.moduleId, point.id)
    ElMessage.success('删除成功')
    loadPoints()
  } catch (error: any) {
    if (error !== 'cancel') ElMessage.error(error.message || '删除失败')
  }
}

function getPriorityLabel(p: string | undefined | null) {
  const labels: Record<string, string> = { high: '高', medium: '中', low: '低' }
  return labels[p || 'medium'] || '中'
}

function getPriorityClass(p: string | undefined | null) {
  const classes: Record<string, string> = {
    high: 'inline-flex items-center px-2.5 py-1 bg-red-50 text-red-700 text-xs font-medium rounded-full',
    medium: 'inline-flex items-center px-2.5 py-1 bg-yellow-50 text-yellow-700 text-xs font-medium rounded-full',
    low: 'inline-flex items-center px-2.5 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded-full'
  }
  return classes[p || 'medium'] || classes.medium
}

onMounted(() => loadPoints())
defineExpose({ loadPoints })
</script>

<style scoped>


:deep(.el-pagination) {
  --el-pagination-button-bg-color: #fff;
  --el-pagination-hover-color: #000;
}

:deep(.custom-textarea .el-textarea__inner) {
  border-radius: 0.75rem;
}

:deep(.custom-select .el-input__wrapper) {
  border-radius: 0.75rem;
}
</style>
