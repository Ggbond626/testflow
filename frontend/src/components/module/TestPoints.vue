<template>
  <div class="test-points">
    <!-- 操作栏 -->
    <div class="mb-6 flex justify-between items-center">
      <div>
        <h3 class="text-lg font-bold text-gray-900">测试点管理</h3>
        <p class="text-sm text-gray-500 mt-1">
          共 {{ statistics.total_requirement_points }} 个需求点，{{ statistics.total_test_points }} 个测试点
        </p>
      </div>
      <div class="flex gap-3 items-center">
        <!-- 搜索框 -->
        <div class="relative">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索测试点..."
            class="custom-input w-64"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <button
          @click="openAddDialog"
          :disabled="!hasRequirementPoints"
          class="bg-black hover:bg-gray-800 text-white px-4 py-2 rounded-xl font-bold shadow-lg shadow-black/20 transition-all transform hover:-translate-y-0.5 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <el-icon><Plus /></el-icon>
          添加测试点
        </button>
        <button
          @click="generateTestPoints"
          :disabled="!hasRequirementPoints || generating"
          class="px-4 py-2 border border-gray-200 text-gray-700 rounded-xl font-bold hover:bg-gray-50 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <el-icon :class="{ 'is-loading': generating }"><MagicStick /></el-icon>
          {{ generating ? '生成中...' : '生成测试点' }}
        </button>
      </div>
    </div>



    <!-- 加载状态 -->
    <div v-if="loading" class="py-12">
      <el-skeleton :rows="3" animated />
    </div>

    <!-- 空状态 -->
    <div v-else-if="hierarchy.length === 0" class="text-center py-16">
      <el-empty description="暂无测试点">
        <p class="text-sm text-gray-500 mb-4">请先生成需求点，然后生成测试点</p>
      </el-empty>
    </div>

    <!-- 测试点列表 -->
    <div v-else class="space-y-4">
      <div
        v-for="reqPoint in paginatedHierarchy"
        :key="reqPoint.id"
        class="bg-white/50 border border-white/60 rounded-2xl overflow-hidden hover:shadow-lg transition-all"
      >
        <!-- 需求点标题 -->
        <div
          @click="toggleCollapse(reqPoint.id)"
          class="px-6 py-4 bg-gray-50 border-b border-gray-200 cursor-pointer hover:bg-gray-100 transition-colors"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <el-icon
                :class="['transition-transform', { 'rotate-90': activeNames.includes(reqPoint.id) }]"
              >
                <ArrowRight />
              </el-icon>
              <span class="inline-flex items-center px-2.5 py-1 bg-gray-900 text-white text-xs font-bold rounded-lg">
                需求点
              </span>
              <span class="text-gray-800 font-medium">{{ reqPoint.content }}</span>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-sm text-gray-500">
                {{ reqPoint.test_points?.length || 0 }} 个测试点
              </span>
              <button
                @click.stop="generateTestPointsForSingle(reqPoint)"
                :disabled="generatingForPoint === reqPoint.id"
                class="px-3 py-1.5 bg-black text-white rounded-lg text-xs font-bold hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                title="为此需求点生成测试点"
              >
                <el-icon :class="{ 'is-loading': generatingForPoint === reqPoint.id }"><MagicStick /></el-icon>
                <span v-if="generatingForPoint !== reqPoint.id">生成</span>
                <span v-else>生成中</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 测试点列表 -->
        <div v-show="activeNames.includes(reqPoint.id)" class="p-4 space-y-3">
          <div v-if="!reqPoint.test_points?.length" class="text-center py-6 text-gray-400 text-sm">
            暂无测试点，点击"生成测试点"自动生成
          </div>
          <div
            v-for="tp in reqPoint.test_points"
            :key="tp.id"
            class="bg-white/40 border border-white/50 rounded-xl p-4 hover:border-white/80 transition-colors"
          >
            <div class="flex items-start gap-4">
              <div class="flex-1">
                <div class="text-gray-800 text-sm leading-relaxed">{{ tp.content }}</div>
                <div class="flex items-center gap-2 mt-3">
                  <span :class="getTestTypeClass(tp.test_type)">
                    {{ getTestTypeLabel(tp.test_type) }}
                  </span>
                  <span v-if="tp.design_method" :class="getDesignMethodClass(tp.design_method)">
                    {{ getDesignMethodLabel(tp.design_method) }}
                  </span>
                  <span :class="getPriorityClass(tp.priority)">
                    {{ getPriorityLabel(tp.priority) }}
                  </span>
                </div>
              </div>
              <div class="flex-shrink-0 flex gap-2">
                <button
                  @click.stop="editTestPoint(tp)"
                  class="p-2 border border-gray-200 text-gray-600 rounded-lg text-sm hover:bg-gray-100 transition-colors"
                >
                  <el-icon><Edit /></el-icon>
                </button>
                <button
                  @click.stop="deleteTestPoint(tp)"
                  class="p-2 border border-red-200 text-red-500 rounded-lg text-sm hover:bg-red-50 transition-colors"
                >
                  <el-icon><Delete /></el-icon>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="hierarchy.length > 0" class="mt-6 flex justify-end">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="hierarchy.length"
        background
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
      />
    </div>

    <!-- 生成中对话框 -->
    <el-dialog
      v-model="showGeneratingDialog"
      title="生成测试点"
      width="450px"
      :close-on-click-modal="false"
      :show-close="!generating"
      @close="cancelGeneration"
      align-center
      append-to-body
      class="generating-dialog"
    >
      <div class="text-center py-6">
        <div class="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
          <el-icon class="is-loading text-3xl text-gray-600"><Loading /></el-icon>
        </div>
        <p class="text-gray-800 font-bold mb-2">正在生成测试点</p>
        <p class="text-gray-500 text-sm mb-4">
          {{ getProgressText() }}
        </p>
        <div class="px-8">
          <el-progress
            :percentage="generationProgress"
            :stroke-width="8"
            :show-text="false"
            color="#000"
          />
        </div>
        <p class="text-xs text-gray-400 mt-4">共 {{ hierarchy.length }} 个需求点，请耐心等待</p>
      </div>
      <template #footer>
        <div class="flex justify-center pt-2">
          <button
            @click="cancelGeneration"
            class="px-6 py-2 text-gray-500 hover:text-gray-700 text-sm"
          >
            取消任务
          </button>
        </div>
      </template>
    </el-dialog>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="showDialog"
      :title="editingTestPoint ? '编辑测试点' : '添加测试点'"
      width="560px"
      :close-on-click-modal="false"
      align-center
      append-to-body
      class="edit-dialog"
    >
      <div class="space-y-4">
        <div v-if="!editingTestPoint">
          <label class="block text-sm font-bold text-gray-700 mb-2">关联需求点 <span class="text-red-500">*</span></label>
          <el-select 
            v-model="form.requirement_point_id" 
            style="width: 100%" 
            placeholder="选择需求点" 
            class="custom-select"
            filterable
          >
            <el-option v-for="rp in hierarchy" :key="rp.id" :label="rp.content" :value="rp.id" />
          </el-select>
        </div>
        <div>
          <label class="block text-sm font-bold text-gray-700 mb-2">测试点内容 <span class="text-red-500">*</span></label>
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="4"
            placeholder="请输入测试点内容，清晰描述测试目的、策略和验证要点"
            class="custom-textarea"
          />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-bold text-gray-700 mb-2">测试类型</label>
            <el-select v-model="form.test_type" style="width: 100%" class="custom-select">
              <el-option 
                v-for="category in testCategories" 
                :key="category.code" 
                :label="category.name" 
                :value="category.code" 
              />
            </el-select>
          </div>
          <div>
            <label class="block text-sm font-bold text-gray-700 mb-2">设计方法</label>
            <el-select v-model="form.design_method" style="width: 100%" class="custom-select" clearable placeholder="选择设计方法">
              <el-option 
                v-for="method in designMethods" 
                :key="method.code" 
                :label="method.name" 
                :value="method.code" 
              />
            </el-select>
          </div>
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
            @click="saveTestPoint"
            :disabled="saving"
            class="px-6 py-2.5 bg-black text-white rounded-xl font-bold hover:bg-gray-800 transition-all shadow-lg shadow-black/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="saving">保存中...</span>
            <span v-else>{{ editingTestPoint ? '保存' : '添加' }}</span>
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, MagicStick, Loading, Edit, Delete, ArrowRight, Search } from '@element-plus/icons-vue'
import { requirementApi } from '@/api/requirement'
import { agentApi } from '@/api/agent'
import { settingsApi } from '@/api/settings'

const props = defineProps<{ projectId: number; moduleId: number }>()

const loading = ref(false)
const generating = ref(false)
const saving = ref(false)
const showGeneratingDialog = ref(false)
const showDialog = ref(false)
const activeNames = ref<number[]>([])
const hierarchy = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const editingTestPoint = ref<any>(null)
const form = ref({ 
  content: '', 
  test_type: 'functional', 
  design_method: '',
  priority: 'medium', 
  requirement_point_id: 0 
})

// 搜索
const searchKeyword = ref('')

// 测试类别和设计方法配置
const testCategories = ref<any[]>([])
const designMethods = ref<any[]>([])

// 异步任务状态
const generationProgress = ref(0)
const generationMessage = ref('')
const currentTaskId = ref<string | null>(null)
const isCancelling = ref(false)
const generatingForPoint = ref<number | null>(null)

const statistics = computed(() => ({
  total_requirement_points: hierarchy.value.length,
  total_test_points: hierarchy.value.reduce((sum, rp) => sum + (rp.test_points?.length || 0), 0)
}))
const hasRequirementPoints = computed(() => hierarchy.value.length > 0)

// 过滤后的层级数据
const filteredHierarchy = computed(() => {
  let result = hierarchy.value
  
  // 如果没有搜索关键词，直接返回原数据
  if (!searchKeyword.value) {
    return result
  }
  
  const keyword = searchKeyword.value.toLowerCase()
  
  // 对每个需求点进行筛选
  return result.map(rp => {
    // 如果需求点内容匹配，保留所有测试点
    if (rp.content?.toLowerCase().includes(keyword)) {
      return rp
    }
    
    // 否则只保留匹配的测试点
    const filteredTestPoints = (rp.test_points || []).filter((tp: any) => 
      tp.content?.toLowerCase().includes(keyword)
    )
    
    return {
      ...rp,
      test_points: filteredTestPoints
    }
  }).filter(rp => {
    // 只保留有测试点的需求点，或者需求点内容匹配搜索关键词
    if (rp.content?.toLowerCase().includes(keyword)) {
      return true
    }
    return rp.test_points && rp.test_points.length > 0
  })
})

const paginatedHierarchy = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredHierarchy.value.slice(start, start + pageSize.value)
})

// 监听搜索关键词变化，重置页码
watch(searchKeyword, () => {
  currentPage.value = 1
})

function handleSizeChange() {
  currentPage.value = 1
}

function toggleCollapse(id: number) {
  const index = activeNames.value.indexOf(id)
  if (index > -1) {
    activeNames.value.splice(index, 1)
  } else {
    activeNames.value.push(id)
  }
}

async function loadHierarchy() {
  loading.value = true
  try {
    const data = await requirementApi.getModuleTestPoints(props.projectId, props.moduleId)
    hierarchy.value = data.requirement_points || []
    activeNames.value = hierarchy.value.map(rp => rp.id)
  } catch (error: any) {
    if (error.response?.status !== 404) ElMessage.error(error.message || '加载失败')
    hierarchy.value = []
  } finally {
    loading.value = false
  }
}

async function loadTestCategories() {
  try {
    const categories = await settingsApi.getTestCategories()
    testCategories.value = categories.filter((c: any) => c.is_active)
  } catch (error: any) {
    console.error('加载测试类别失败:', error)
    // 使用默认类别
    testCategories.value = [
      { code: 'functional', name: '功能测试' },
      { code: 'performance', name: '性能测试' },
      { code: 'security', name: '安全测试' },
      { code: 'interface', name: '接口测试' },
      { code: 'stress', name: '压力测试' },
      { code: 'usability', name: '可用性测试' }
    ]
  }
}

async function loadDesignMethods() {
  try {
    const methods = await settingsApi.getDesignMethods()
    designMethods.value = methods.filter((m: any) => m.is_active)
  } catch (error: any) {
    console.error('加载测试设计方法失败:', error)
    // 使用默认设计方法（与系统设置保持一致）
    designMethods.value = [
      { code: 'equivalence_partitioning', name: '等价类划分' },
      { code: 'boundary_value', name: '边界值分析' },
      { code: 'cause_effect', name: '因果图法' },
      { code: 'decision_table', name: '判定表法' },
      { code: 'state_transition', name: '状态转换法' },
      { code: 'orthogonal_array', name: '正交试验法' },
      { code: 'scenario', name: '场景法' },
      { code: 'error_guessing', name: '错误推测法' }
    ]
  }
}

function openAddDialog() {
  editingTestPoint.value = null
  form.value = { 
    content: '', 
    test_type: 'functional', 
    design_method: '',
    priority: 'medium', 
    requirement_point_id: hierarchy.value[0]?.id || 0 
  }
  showDialog.value = true
}

function editTestPoint(tp: any) {
  editingTestPoint.value = tp
  form.value = { 
    content: tp.content, 
    test_type: tp.test_type, 
    design_method: tp.design_method || '',
    priority: tp.priority, 
    requirement_point_id: 0 
  }
  showDialog.value = true
}

async function saveTestPoint() {
  if (!form.value.content.trim()) { ElMessage.warning('请输入测试点内容'); return }
  if (!editingTestPoint.value && !form.value.requirement_point_id) { ElMessage.warning('请选择关联需求点'); return }
  
  saving.value = true
  try {
    if (editingTestPoint.value) {
      await requirementApi.updateModuleTestPoint(props.projectId, props.moduleId, editingTestPoint.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await requirementApi.createModuleTestPoint(props.projectId, props.moduleId, form.value)
      ElMessage.success('添加成功')
    }
    showDialog.value = false
    loadHierarchy()
  } catch (error: any) {
    ElMessage.error(error.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function deleteTestPoint(tp: any) {
  try {
    await ElMessageBox.confirm('确定删除该测试点？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await requirementApi.deleteModuleTestPoint(props.projectId, props.moduleId, tp.id)
    ElMessage.success('删除成功')
    loadHierarchy()
  } catch (error: any) {
    if (error !== 'cancel') ElMessage.error(error.message || '删除失败')
  }
}

async function generateTestPoints() {
  if (!hasRequirementPoints.value) { ElMessage.warning('请先生成需求点'); return }
  
  // 如果已有测试点，先确认是否清空
  if (statistics.value.total_test_points > 0) {
    try {
      await ElMessageBox.confirm(
        `当前已有 ${statistics.value.total_test_points} 个测试点，重新生成将清空现有测试点，是否继续？`,
        '确认重新生成',
        { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
      )
    } catch {
      return // 用户取消
    }
  }
  
  generating.value = true
  showGeneratingDialog.value = true
  generationProgress.value = 0
  generationMessage.value = ''
  currentTaskId.value = null
  isCancelling.value = false
  
  const requirementPoints = hierarchy.value.map(rp => ({ id: rp.id, content: rp.content }))
  
  // 记录是否需要清空现有测试点
  const shouldClearExisting = statistics.value.total_test_points > 0
  
  try {
    // 使用异步模式启动任务（测试分类和设计方法由后端从系统设置自动加载）
    const asyncResult = await agentApi.generateTestPointsAsync({
      requirement_points: requirementPoints
    })
    
    currentTaskId.value = asyncResult.task_id
    
    // 轮询任务状态
    let pollCount = 0
    let errorCount = 0
    const maxPolls = 180 // 最多轮询180次（约3分钟）
    const maxErrors = 5 // 最多允许5次连续错误
    
    while (pollCount < maxPolls && !isCancelling.value) {
      await new Promise(resolve => setTimeout(resolve, 1000))
      pollCount++
      
      try {
        const status = await agentApi.getTaskStatus(currentTaskId.value)
        errorCount = 0 // 成功后重置错误计数
        generationProgress.value = status.progress
        
        if (status.status === 'completed') {
          // 任务完成，保存测试点
          if (status.result?.test_points) {
            const pointsToCreate = status.result.test_points.map((tp: any, i: number) => ({
              content: tp.content,
              test_type: tp.test_type || 'functional',
              design_method: tp.design_method,
              priority: tp.priority || 'medium',
              requirement_point_id: tp.requirement_point_id || requirementPoints[i % requirementPoints.length]?.id,
              created_by_ai: true
            }))
            // 批量创建，如果需要则先清空现有测试点
            const saveResult = await requirementApi.batchCreateModuleTestPoints(
              props.projectId, 
              props.moduleId, 
              pointsToCreate,
              shouldClearExisting  // 传入是否清空现有测试点
            )
            if (saveResult.success) {
              const msg = shouldClearExisting && saveResult.deleted_count 
                ? `已清空 ${saveResult.deleted_count} 个旧测试点，成功生成 ${saveResult.created_count} 个新测试点`
                : `成功生成 ${saveResult.created_count} 个测试点`
              ElMessage.success(msg)
            }
          }
          break
        } else if (status.status === 'failed') {
          ElMessage.error(status.error || '生成失败')
          break
        } else if (status.status === 'cancelled') {
          ElMessage.warning('任务已取消')
          break
        }
      } catch (pollError) {
        errorCount++
        console.warn(`轮询任务状态失败 (${errorCount}/${maxErrors}):`, pollError)
        if (errorCount >= maxErrors) {
          ElMessage.error('获取任务状态失败，请刷新页面查看结果')
          break
        }
        // 继续轮询，不中断
      }
    }
    
    if (pollCount >= maxPolls && !isCancelling.value) {
      ElMessage.warning('任务超时，请稍后刷新查看结果')
    }
  } catch (error: any) {
    if (!isCancelling.value) {
      ElMessage.error(error.message || '生成失败')
    }
  } finally {
    generating.value = false
    showGeneratingDialog.value = false
    generationProgress.value = 0
    generationMessage.value = ''
    currentTaskId.value = null
    isCancelling.value = false
    loadHierarchy()
  }
}

async function cancelGeneration() {
  if (!generating.value) {
    showGeneratingDialog.value = false
    return
  }
  
  isCancelling.value = true
  
  if (currentTaskId.value) {
    try {
      await agentApi.cancelTask(currentTaskId.value)
      ElMessage.info('正在取消任务...')
    } catch (error) {
      console.error('取消任务失败:', error)
    }
  }
  
  generating.value = false
  showGeneratingDialog.value = false
}

async function generateTestPointsForSingle(reqPoint: any) {
  generatingForPoint.value = reqPoint.id
  
  try {
    // 构建需求点数据，包含已有测试点信息
    const requirementPointData: any = {
      id: reqPoint.id,
      content: reqPoint.content
    }
    
    // 如果有已有测试点，序列化传输给AI
    if (reqPoint.test_points && reqPoint.test_points.length > 0) {
      requirementPointData.existing_test_points = reqPoint.test_points.map((tp: any) => ({
        content: tp.content,
        test_type: tp.test_type,
        design_method: tp.design_method,
        priority: tp.priority
      }))
    }
    
    // 调用AI生成测试点
    const result = await agentApi.generateTestPointsAsync({
      requirement_points: [requirementPointData]
    })
    
    const taskId = result.task_id
    
    // 轮询任务状态
    let pollCount = 0
    const maxPolls = 60 // 最多轮询60次（约1分钟）
    
    while (pollCount < maxPolls) {
      await new Promise(resolve => setTimeout(resolve, 1000))
      pollCount++
      
      try {
        const status = await agentApi.getTaskStatus(taskId)
        
        if (status.status === 'completed') {
          // 任务完成，保存测试点
          if (status.result?.test_points) {
            const pointsToCreate = status.result.test_points.map((tp: any) => ({
              content: tp.content,
              test_type: tp.test_type || 'functional',
              design_method: tp.design_method,
              priority: tp.priority || 'medium',
              requirement_point_id: reqPoint.id,
              created_by_ai: true
            }))
            
            // 批量创建测试点
            const saveResult = await requirementApi.batchCreateModuleTestPoints(
              props.projectId,
              props.moduleId,
              pointsToCreate,
              false // 不清空现有测试点
            )
            
            if (saveResult.success) {
              ElMessage.success(`成功为需求点生成 ${saveResult.created_count} 个测试点`)
              // 刷新列表
              loadHierarchy()
            }
          }
          break
        } else if (status.status === 'failed') {
          ElMessage.error(status.error || '生成失败')
          break
        } else if (status.status === 'cancelled') {
          ElMessage.warning('任务已取消')
          break
        }
      } catch (pollError) {
        console.warn('轮询任务状态失败:', pollError)
        // 继续轮询
      }
    }
    
    if (pollCount >= maxPolls) {
      ElMessage.warning('任务超时，请稍后刷新查看结果')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '生成失败')
  } finally {
    generatingForPoint.value = null
  }
}

function getTestTypeLabel(t: string | undefined | null) {
  if (!t) return '功能测试'
  // 大小写不敏感匹配（兼容旧数据）
  const lowerCode = t.toLowerCase()
  const category = testCategories.value.find(c => c.code.toLowerCase() === lowerCode)
  // 如果在配置中找到，返回中文名称；否则返回code本身
  return category?.name || t
}

function getDesignMethodLabel(m: string | undefined | null) {
  if (!m) return ''
  // 大小写不敏感匹配（兼容旧数据）
  const lowerCode = m.toLowerCase()
  const method = designMethods.value.find(dm => dm.code.toLowerCase() === lowerCode)
  // 如果在配置中找到，返回中文名称；否则返回code本身
  return method?.name || m
}

function getPriorityLabel(p: string | undefined | null) {
  const labels: Record<string, string> = { high: '高', medium: '中', low: '低' }
  return labels[p || 'medium'] || '中'
}

function getTestTypeClass(t: string | undefined | null) {
  const colorMap: Record<string, string> = {
    functional: 'bg-blue-50 text-blue-700',
    performance: 'bg-yellow-50 text-yellow-700',
    security: 'bg-red-50 text-red-700',
    usability: 'bg-green-50 text-green-700',
    interface: 'bg-purple-50 text-purple-700',
    stress: 'bg-orange-50 text-orange-700',
    compatibility: 'bg-indigo-50 text-indigo-700',
    installation: 'bg-pink-50 text-pink-700',
    configuration: 'bg-cyan-50 text-cyan-700',
    exploratory: 'bg-teal-50 text-teal-700',
    automation: 'bg-lime-50 text-lime-700',
    disaster_recovery: 'bg-rose-50 text-rose-700',
    localization: 'bg-violet-50 text-violet-700',
    load: 'bg-amber-50 text-amber-700',
    capacity: 'bg-emerald-50 text-emerald-700'
  }
  const color = colorMap[t || 'functional'] || 'bg-gray-50 text-gray-700'
  return `inline-flex items-center px-2 py-0.5 ${color} text-xs font-medium rounded-full`
}

function getDesignMethodClass(m: string | undefined | null) {
  const colorMap: Record<string, string> = {
    equivalence_partitioning: 'bg-indigo-50 text-indigo-700',
    boundary_value: 'bg-purple-50 text-purple-700',
    cause_effect: 'bg-pink-50 text-pink-700',
    decision_table: 'bg-rose-50 text-rose-700',
    state_transition: 'bg-cyan-50 text-cyan-700',
    orthogonal_array: 'bg-lime-50 text-lime-700',
    scenario: 'bg-violet-50 text-violet-700',
    error_guessing: 'bg-orange-50 text-orange-700'
  }
  const color = colorMap[m || ''] || 'bg-gray-50 text-gray-700'
  return `inline-flex items-center px-2 py-0.5 ${color} text-xs font-medium rounded-full`
}

function getPriorityClass(p: string | undefined | null) {
  const classes: Record<string, string> = {
    high: 'inline-flex items-center px-2 py-0.5 bg-red-50 text-red-600 text-xs font-medium rounded-full',
    medium: 'inline-flex items-center px-2 py-0.5 bg-yellow-50 text-yellow-600 text-xs font-medium rounded-full',
    low: 'inline-flex items-center px-2 py-0.5 bg-gray-100 text-gray-500 text-xs font-medium rounded-full'
  }
  return classes[p || 'medium'] || classes.medium
}

function getProgressText() {
  if (generationProgress.value >= 100) {
    return '生成完成，正在保存...'
  } else if (generationProgress.value > 0) {
    return `已完成 ${generationProgress.value}%`
  } else if (currentTaskId.value) {
    return 'AI智能体正在分析需求点...'
  } else {
    return '正在启动任务...'
  }
}

onMounted(() => {
  loadHierarchy()
  loadTestCategories()
  loadDesignMethods()
})
defineExpose({ loadHierarchy })
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

.rotate-90 {
  transform: rotate(90deg);
}
</style>
