<template>
  <div class="test-cases">
    <!-- 操作栏 -->
    <div class="mb-6 flex justify-between items-center">
      <div>
        <h3 class="text-lg font-bold text-gray-900">用例生成</h3>
        <p class="text-sm text-gray-500 mt-1">
          共 {{ statistics.total_test_points }} 个测试点，{{ statistics.total_test_cases }} 个测试用例
        </p>
      </div>
      <div class="flex gap-3 items-center">
        <!-- 搜索框 -->
        <div class="relative">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索测试用例..."
            class="custom-input w-64"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <button
          @click="openAddDialog"
          :disabled="!hasTestPoints"
          class="bg-black hover:bg-gray-800 text-white px-4 py-2 rounded-xl font-bold shadow-lg shadow-black/20 transition-all transform hover:-translate-y-0.5 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <el-icon><Plus /></el-icon>
          添加测试用例
        </button>
        <button
          @click="generateTestCases"
          :disabled="!hasTestPoints || generating || generatingTestPointIds.length > 0"
          class="px-4 py-2 border border-gray-200 text-gray-700 rounded-xl font-bold hover:bg-gray-50 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <el-icon :class="{ 'is-loading': generating }"><MagicStick /></el-icon>
          {{ generating ? '生成中...' : '生成测试用例' }}
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="py-12">
      <el-skeleton :rows="3" animated />
    </div>

    <!-- 空状态 -->
    <div v-else-if="hierarchy.length === 0" class="text-center py-16">
      <el-empty description="暂无测试用例">
        <p class="text-sm text-gray-500 mb-4">请先生成测试点，然后生成测试用例</p>
      </el-empty>
    </div>

    <!-- 测试用例列表（按测试点分组） -->
    <div v-else class="space-y-4">
      <div
        v-for="testPoint in paginatedHierarchy"
        :key="testPoint.id"
        class="bg-white/50 border border-white/60 rounded-2xl overflow-hidden hover:shadow-lg transition-all"
      >
        <!-- 测试点标题 -->
        <div
          @click="toggleCollapse(testPoint.id)"
          class="px-6 py-4 bg-gray-50 border-b border-gray-200 cursor-pointer hover:bg-gray-100 transition-colors"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex items-start gap-3 flex-1 min-w-0">
              <el-icon :class="['transition-transform flex-shrink-0 mt-0.5', { 'rotate-90': activeNames.includes(testPoint.id) }]">
                <ArrowRight />
              </el-icon>
              <span class="inline-flex items-center px-2.5 py-1 bg-blue-600 text-white text-xs font-bold rounded-lg flex-shrink-0">
                测试点
              </span>
              <span class="text-gray-800 font-medium break-words flex-1">{{ testPoint.content }}</span>
            </div>
            <div class="flex items-center gap-3 flex-shrink-0">
              <span class="text-sm text-gray-500 whitespace-nowrap">
                {{ testPoint.test_cases?.length || 0 }} 个用例
              </span>
              <button
                @click.stop="generateForTestPoint(testPoint)"
                :disabled="generating || generatingTestPointIds.includes(testPoint.id)"
                class="px-3 py-1.5 text-xs border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 whitespace-nowrap"
              >
                <el-icon class="mr-1" :class="{ 'is-loading': generatingTestPointIds.includes(testPoint.id) }">
                  <Loading v-if="generatingTestPointIds.includes(testPoint.id)" />
                  <MagicStick v-else />
                </el-icon>
                {{ generatingTestPointIds.includes(testPoint.id) ? '生成中...' : '生成用例' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 测试用例列表 -->
        <div v-show="activeNames.includes(testPoint.id)" class="p-4 space-y-3">
          <div v-if="!testPoint.test_cases?.length" class="text-center py-6 text-gray-400 text-sm">
            暂无测试用例，点击"生成用例"自动生成
          </div>
          <div
            v-for="tc in testPoint.test_cases"
            :key="tc.id"
            class="bg-white/40 border border-white/50 rounded-xl p-4 hover:border-white/80 transition-colors"
          >
            <div class="flex items-start gap-4">
              <div class="flex-1">
                <!-- 用例标题 -->
                <div class="flex items-center gap-2 mb-2">
                  <span class="text-gray-900 font-medium">{{ tc.title }}</span>
                  <span v-if="tc.edited_by_user" class="inline-flex items-center px-1.5 py-0.5 bg-green-50 text-green-600 text-xs rounded">
                    已编辑
                  </span>
                </div>
                <!-- 用例描述 -->
                <div v-if="tc.description" class="text-gray-600 text-sm mb-2">{{ tc.description }}</div>
                <!-- 前置条件 -->
                <div v-if="tc.preconditions" class="text-gray-500 text-xs mb-2">
                  <span class="font-medium">前置条件：</span>{{ tc.preconditions }}
                </div>
                <!-- 测试步骤预览 -->
                <div v-if="tc.test_steps?.length" class="text-gray-500 text-xs">
                  <span class="font-medium">测试步骤：</span>{{ tc.test_steps.length }} 步
                </div>
                <!-- 标签 -->
                <div class="flex items-center gap-2 mt-3">
                  <span :class="getStatusClass(tc.status)">{{ getStatusLabel(tc.status) }}</span>
                  <span v-if="tc.test_category" :class="getTestCategoryClass(tc.test_category)">
                    {{ getTestCategoryLabel(tc.test_category) }}
                  </span>
                  <span v-if="tc.design_method" :class="getDesignMethodClass(tc.design_method)">
                    {{ getDesignMethodLabel(tc.design_method) }}
                  </span>
                  <span v-if="tc.priority" :class="getPriorityClass(tc.priority)">
                    {{ getPriorityLabel(tc.priority) }}
                  </span>
                </div>
              </div>
              <div class="flex-shrink-0 flex gap-2">
                <button
                  @click.stop="viewTestCase(tc)"
                  class="p-2 border border-gray-200 text-gray-600 rounded-lg text-sm hover:bg-gray-100 transition-colors"
                  title="查看详情"
                >
                  <el-icon><View /></el-icon>
                </button>
                <button
                  @click.stop="editTestCase(tc)"
                  class="p-2 border border-gray-200 text-gray-600 rounded-lg text-sm hover:bg-gray-100 transition-colors"
                  title="编辑"
                >
                  <el-icon><Edit /></el-icon>
                </button>
                <button
                  @click.stop="deleteTestCase(tc)"
                  class="p-2 border border-red-200 text-red-500 rounded-lg text-sm hover:bg-red-50 transition-colors"
                  title="删除"
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
      title="生成测试用例"
      width="450px"
      :close-on-click-modal="false"
      :show-close="!generating"
      @close="cancelGeneration"
      align-center
      append-to-body
    >
      <div class="text-center py-6">
        <div class="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
          <el-icon class="is-loading text-3xl text-gray-600"><Loading /></el-icon>
        </div>
        <p class="text-gray-800 font-bold mb-2">{{ getProgressTitle() }}</p>
        <p class="text-gray-500 text-sm mb-4">{{ getProgressText() }}</p>
        <div class="px-8">
          <el-progress :percentage="generationProgress" :stroke-width="8" :show-text="false" color="#000" />
        </div>
        <p class="text-xs text-gray-400 mt-4">{{ getProgressHint() }}</p>
      </div>
      <template #footer>
        <div class="flex justify-center pt-2">
          <button @click="cancelGeneration" class="px-6 py-2 text-gray-500 hover:text-gray-700 text-sm">
            取消任务
          </button>
        </div>
      </template>
    </el-dialog>


    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="showDialog"
      :title="editingTestCase ? '编辑测试用例' : '添加测试用例'"
      width="700px"
      :close-on-click-modal="false"
      align-center
      append-to-body
      @close="clearFormErrors"
    >
      <div class="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
        <div v-if="!editingTestCase">
          <label class="block text-sm font-bold text-gray-700 mb-2">关联测试点 <span class="text-red-500">*</span></label>
          <el-select 
            v-model="form.test_point_id" 
            style="width: 100%" 
            placeholder="选择测试点" 
            class="custom-select"
            :class="{ 'is-error': formErrors.test_point_id }" 
            @change="clearFieldError('test_point_id')"
            :teleported="true"
            popper-class="test-point-select-popper"
            filterable
          >
            <el-option 
              v-for="tp in hierarchy" 
              :key="tp.id" 
              :label="tp.content" 
              :value="tp.id"
            >
              <span class="block truncate" :title="tp.content">{{ tp.content }}</span>
            </el-option>
          </el-select>
          <p v-if="formErrors.test_point_id" class="text-red-500 text-xs mt-1">{{ formErrors.test_point_id }}</p>
        </div>
        <div>
          <label class="block text-sm font-bold text-gray-700 mb-2">用例标题 <span class="text-red-500">*</span></label>
          <el-input v-model="form.title" placeholder="请输入测试用例标题" class="custom-input"
            :class="{ 'is-error': formErrors.title }" @input="clearFieldError('title')" />
          <p v-if="formErrors.title" class="text-red-500 text-xs mt-1">{{ formErrors.title }}</p>
        </div>
        <div>
          <label class="block text-sm font-bold text-gray-700 mb-2">用例描述</label>
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="请输入用例描述" class="custom-textarea" />
        </div>
        <div>
          <label class="block text-sm font-bold text-gray-700 mb-2">前置条件</label>
          <el-input v-model="form.preconditions" type="textarea" :rows="2" placeholder="请输入前置条件" class="custom-textarea" />
        </div>
        <div>
          <label class="block text-sm font-bold text-gray-700 mb-2">测试步骤</label>
          <div class="space-y-2">
            <div v-for="(step, index) in form.test_steps" :key="index" class="flex gap-2 items-start">
              <span class="text-gray-500 text-sm mt-2 w-6">{{ index + 1 }}.</span>
              <div class="flex-1 space-y-1">
                <el-input v-model="step.action" placeholder="操作步骤" size="small" />
                <el-input v-model="step.expected" placeholder="预期结果" size="small" />
              </div>
              <button @click="removeStep(index)" class="p-1.5 text-red-500 hover:bg-red-50 rounded mt-1">
                <el-icon><Delete /></el-icon>
              </button>
            </div>
            <button @click="addStep" class="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1">
              <el-icon><Plus /></el-icon>
              添加步骤
            </button>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-bold text-gray-700 mb-2">测试类别</label>
            <el-select v-model="form.test_category" style="width: 100%" placeholder="选择测试类别" class="custom-select">
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
            <el-select v-model="form.design_method" style="width: 100%" placeholder="选择设计方法" class="custom-select" clearable>
              <el-option 
                v-for="method in designMethods" 
                :key="method.code" 
                :label="method.name" 
                :value="method.code" 
              />
            </el-select>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-bold text-gray-700 mb-2">优先级</label>
            <el-select v-model="form.priority" style="width: 100%" class="custom-select">
              <el-option label="高" value="high" />
              <el-option label="中" value="medium" />
              <el-option label="低" value="low" />
            </el-select>
          </div>
          <div>
            <label class="block text-sm font-bold text-gray-700 mb-2">状态</label>
            <el-select v-model="form.status" style="width: 100%" class="custom-select">
              <el-option label="草稿" value="draft" />
              <el-option label="待评审" value="under_review" />
              <el-option label="已通过" value="approved" />
              <el-option label="已拒绝" value="rejected" />
            </el-select>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3 pt-4">
          <button @click="showDialog = false"
            class="px-6 py-2.5 rounded-xl text-gray-600 font-bold hover:bg-gray-100 transition-all border border-gray-200">
            取消
          </button>
          <button @click="saveTestCase" :disabled="saving"
            class="px-6 py-2.5 bg-black text-white rounded-xl font-bold hover:bg-gray-800 transition-all shadow-lg shadow-black/20 disabled:opacity-50 disabled:cursor-not-allowed">
            <span v-if="saving">保存中...</span>
            <span v-else>{{ editingTestCase ? '保存' : '添加' }}</span>
          </button>
        </div>
      </template>
    </el-dialog>

    <!-- 查看详情对话框 -->
    <el-dialog v-model="showViewDialog" title="测试用例详情" width="700px" align-center append-to-body>
      <div v-if="viewingTestCase" class="space-y-4">
        <div>
          <label class="block text-sm font-bold text-gray-700 mb-1">用例标题</label>
          <p class="text-gray-900">{{ viewingTestCase.title }}</p>
        </div>
        <div v-if="viewingTestCase.description">
          <label class="block text-sm font-bold text-gray-700 mb-1">用例描述</label>
          <p class="text-gray-700">{{ viewingTestCase.description }}</p>
        </div>
        <div v-if="viewingTestCase.preconditions">
          <label class="block text-sm font-bold text-gray-700 mb-1">前置条件</label>
          <p class="text-gray-700">{{ viewingTestCase.preconditions }}</p>
        </div>
        <div v-if="viewingTestCase.test_steps?.length">
          <label class="block text-sm font-bold text-gray-700 mb-2">测试步骤</label>
          <div class="space-y-2">
            <div v-for="(step, index) in viewingTestCase.test_steps" :key="index" class="bg-gray-50 rounded-lg p-3">
              <div class="flex gap-2">
                <span class="text-gray-500 font-medium">{{ step.step || index + 1 }}.</span>
                <div>
                  <p class="text-gray-800">{{ step.action }}</p>
                  <p v-if="step.expected" class="text-gray-500 text-sm mt-1">预期：{{ step.expected }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="flex gap-4 flex-wrap">
          <div>
            <label class="block text-sm font-bold text-gray-700 mb-1">状态</label>
            <span :class="getStatusClass(viewingTestCase.status)">{{ getStatusLabel(viewingTestCase.status) }}</span>
          </div>
          <div v-if="viewingTestCase.test_category">
            <label class="block text-sm font-bold text-gray-700 mb-1">测试类别</label>
            <span :class="getTestCategoryClass(viewingTestCase.test_category)">{{ getTestCategoryLabel(viewingTestCase.test_category) }}</span>
          </div>
          <div v-if="viewingTestCase.design_method">
            <label class="block text-sm font-bold text-gray-700 mb-1">设计方法</label>
            <span :class="getDesignMethodClass(viewingTestCase.design_method)">{{ getDesignMethodLabel(viewingTestCase.design_method) }}</span>
          </div>
          <div v-if="viewingTestCase.priority">
            <label class="block text-sm font-bold text-gray-700 mb-1">优先级</label>
            <span :class="getPriorityClass(viewingTestCase.priority)">{{ getPriorityLabel(viewingTestCase.priority) }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <button @click="showViewDialog = false"
            class="px-6 py-2.5 rounded-xl text-gray-600 font-bold hover:bg-gray-100 transition-all border border-gray-200">
            关闭
          </button>
          <button @click="editFromView"
            class="px-6 py-2.5 bg-black text-white rounded-xl font-bold hover:bg-gray-800 transition-all">
            编辑
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>


<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, MagicStick, Loading, Edit, Delete, ArrowRight, View, Search } from '@element-plus/icons-vue'
import { requirementApi } from '@/api/requirement'
import { agentApi } from '@/api/agent'
import { settingsApi } from '@/api/settings'

const props = defineProps<{ projectId: number; moduleId: number }>()

// 状态
const loading = ref(false)
const generating = ref(false)
const saving = ref(false)
const showGeneratingDialog = ref(false)
const showDialog = ref(false)
const showViewDialog = ref(false)
const activeNames = ref<number[]>([])
const hierarchy = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(10)

// 搜索
const searchKeyword = ref('')

// 编辑相关
const editingTestCase = ref<any>(null)
const viewingTestCase = ref<any>(null)

// 表单
const form = ref({
  title: '',
  description: '',
  preconditions: '',
  test_steps: [] as Array<{ step: number; action: string; expected: string }>,
  expected_result: '',
  design_method: '',
  test_category: 'functional',
  priority: 'medium',
  status: 'draft',
  test_point_id: 0
})

// 设计方法列表
const designMethods = ref<Array<{ code: string; name: string }>>([])

// 测试类别列表
const testCategories = ref<Array<{ code: string; name: string }>>([])

// 表单验证错误
const formErrors = ref<{ title?: string; test_point_id?: string }>({})

// 异步任务状态
const generationProgress = ref(0)
const currentTaskId = ref<string | null>(null)
const isCancelling = ref(false)
const generatingTestPointCount = ref(0)
const progressMessage = ref('')
const generatingTestPointIds = ref<number[]>([])

// 计算属性
const statistics = computed(() => ({
  total_test_points: hierarchy.value.length,
  total_test_cases: hierarchy.value.reduce((sum, tp) => sum + (tp.test_cases?.length || 0), 0)
}))

const hasTestPoints = computed(() => hierarchy.value.length > 0)

// 过滤后的层级数据
const filteredHierarchy = computed(() => {
  let result = hierarchy.value
  
  // 如果没有搜索关键词，直接返回原数据
  if (!searchKeyword.value) {
    return result
  }
  
  const keyword = searchKeyword.value.toLowerCase()
  
  // 对每个测试点进行筛选
  return result.map(tp => {
    // 如果测试点内容匹配，保留所有测试用例
    if (tp.content?.toLowerCase().includes(keyword)) {
      return tp
    }
    
    // 否则只保留匹配的测试用例
    const filteredTestCases = (tp.test_cases || []).filter((tc: any) => 
      tc.title?.toLowerCase().includes(keyword) ||
      tc.description?.toLowerCase().includes(keyword)
    )
    
    return {
      ...tp,
      test_cases: filteredTestCases
    }
  }).filter(tp => {
    // 只保留有测试用例的测试点，或者测试点内容匹配搜索关键词
    if (tp.content?.toLowerCase().includes(keyword)) {
      return true
    }
    return tp.test_cases && tp.test_cases.length > 0
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

// 方法
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
    const data = await requirementApi.getModuleTestCases(props.projectId, props.moduleId)
    hierarchy.value = data.test_points || []
    activeNames.value = hierarchy.value.map(tp => tp.id)
  } catch (error: any) {
    if (error.response?.status !== 404) ElMessage.error(error.message || '加载失败')
    hierarchy.value = []
  } finally {
    loading.value = false
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

async function loadTestCategories() {
  try {
    const categories = await settingsApi.getTestCategories()
    testCategories.value = categories.filter((c: any) => c.is_active)
  } catch (error: any) {
    console.error('加载测试类别失败:', error)
    // 使用默认测试类别
    testCategories.value = [
      { code: 'functional', name: '功能测试' },
      { code: 'performance', name: '性能测试' },
      { code: 'security', name: '安全测试' },
      { code: 'usability', name: '易用性测试' }
    ]
  }
}

function openAddDialog() {
  editingTestCase.value = null
  clearFormErrors()
  form.value = {
    title: '',
    description: '',
    preconditions: '',
    test_steps: [{ step: 1, action: '', expected: '' }],
    expected_result: '',
    design_method: designMethods.value[0]?.code || '',
    test_category: testCategories.value[0]?.code || 'functional',
    priority: 'medium',
    status: 'draft',
    test_point_id: hierarchy.value[0]?.id || 0
  }
  showDialog.value = true
}

function clearFormErrors() {
  formErrors.value = {}
}

function clearFieldError(field: 'title' | 'test_point_id') {
  if (formErrors.value[field]) delete formErrors.value[field]
}

function validateForm(): boolean {
  clearFormErrors()
  let isValid = true
  if (!form.value.title.trim()) {
    formErrors.value.title = '请输入用例标题'
    isValid = false
  }
  if (!editingTestCase.value && !form.value.test_point_id) {
    formErrors.value.test_point_id = '请选择关联测试点'
    isValid = false
  }
  return isValid
}

function viewTestCase(tc: any) {
  viewingTestCase.value = tc
  showViewDialog.value = true
}

function editFromView() {
  showViewDialog.value = false
  editTestCase(viewingTestCase.value)
}

function editTestCase(tc: any) {
  editingTestCase.value = tc
  clearFormErrors()
  form.value = {
    title: tc.title || '',
    description: tc.description || '',
    preconditions: tc.preconditions || '',
    test_steps: tc.test_steps?.length ? [...tc.test_steps] : [{ step: 1, action: '', expected: '' }],
    expected_result: tc.expected_result || '',
    design_method: tc.design_method || '',
    test_category: tc.test_category || 'functional',
    priority: tc.priority || 'medium',
    status: tc.status || 'draft',
    test_point_id: tc.test_point_id || 0
  }
  showDialog.value = true
}

function addStep() {
  form.value.test_steps.push({ step: form.value.test_steps.length + 1, action: '', expected: '' })
}

function removeStep(index: number) {
  form.value.test_steps.splice(index, 1)
  form.value.test_steps.forEach((step, i) => { step.step = i + 1 })
}

async function saveTestCase() {
  if (!validateForm()) return

  saving.value = true
  try {
    const validSteps = form.value.test_steps.filter(s => s.action.trim())
    const data = {
      title: form.value.title,
      description: form.value.description || undefined,
      preconditions: form.value.preconditions || undefined,
      test_steps: validSteps.length > 0 ? validSteps : undefined,
      expected_result: form.value.expected_result || undefined,
      design_method: form.value.design_method || undefined,
      test_category: form.value.test_category || undefined,
      priority: form.value.priority || undefined,
      status: form.value.status,
      test_point_id: form.value.test_point_id
    }

    if (editingTestCase.value) {
      await requirementApi.updateModuleTestCase(props.projectId, props.moduleId, editingTestCase.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await requirementApi.createModuleTestCase(props.projectId, props.moduleId, data)
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

async function deleteTestCase(tc: any) {
  await ElMessageBox.confirm('确定要删除这个测试用例吗？', '确认删除', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
  await requirementApi.deleteModuleTestCase(props.projectId, props.moduleId, tc.id)
  ElMessage.success('删除成功')
  loadHierarchy()
}


// ==================== 生成测试用例 ====================

async function generateTestCases() {
  // 防止重复点击
  if (generating.value) {
    return
  }
  
  if (!hasTestPoints.value) {
    ElMessage.warning('请先生成测试点')
    return
  }

  if (statistics.value.total_test_cases > 0) {
    try {
      await ElMessageBox.confirm(
        `当前已有 ${statistics.value.total_test_cases} 个测试用例，重新生成将清空现有用例，是否继续？`,
        '确认重新生成',
        { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
      )
    } catch {
      return
    }
  }

  generating.value = true
  showGeneratingDialog.value = true
  generationProgress.value = 0
  currentTaskId.value = null
  isCancelling.value = false
  progressMessage.value = ''

  // 传递完整的测试点数据（包含所有必要字段）
  const testPoints = hierarchy.value.map(tp => ({
    id: tp.id,
    content: tp.content,
    test_type: tp.test_type,
    design_method: tp.design_method,
    priority: tp.priority,
    requirement_point_id: tp.requirement_point_id
  }))
  const shouldClearExisting = statistics.value.total_test_cases > 0
  generatingTestPointCount.value = testPoints.length

  try {
    const asyncResult = await agentApi.designTestCasesAsync({
      test_points: testPoints,
      module_id: props.moduleId,
      clear_existing: shouldClearExisting
    })

    currentTaskId.value = asyncResult.task_id

    let pollCount = 0
    let errorCount = 0
    const maxPolls = 600 // 10分钟（生成+优化需要更长时间）
    const maxErrors = 5

    while (pollCount < maxPolls && !isCancelling.value) {
      await new Promise(resolve => setTimeout(resolve, 1000))
      pollCount++

      try {
        const status = await agentApi.getTaskStatus(currentTaskId.value)
        errorCount = 0
        generationProgress.value = status.progress
        if ((status as any).message) progressMessage.value = (status as any).message

        if (status.status === 'completed') {
          const savedCount = status.result?.saved_count || 0
          const optimizedCount = status.result?.optimized_count || 0
          ElMessage.success(`成功生成 ${savedCount} 个测试用例${optimizedCount > 0 ? `，优化 ${optimizedCount} 个` : ''}`)
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
        if (errorCount >= maxErrors) {
          ElMessage.error('获取任务状态失败，请刷新页面查看结果')
          break
        }
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
    currentTaskId.value = null
    isCancelling.value = false
    progressMessage.value = ''
    loadHierarchy()
  }
}

async function generateForTestPoint(testPoint: any) {
  if (testPoint.test_cases?.length > 0) {
    try {
      const action = await ElMessageBox.confirm(
        `该测试点已有 ${testPoint.test_cases.length} 个用例，请选择操作方式`,
        '生成用例',
        { confirmButtonText: '追加', cancelButtonText: '替换', distinguishCancelAndClose: true, type: 'info' }
      )
      await doGenerateForTestPoint(testPoint, false, false)
    } catch (action) {
      if (action === 'cancel') {
        await doGenerateForTestPoint(testPoint, true, false)
      }
    }
  } else {
    await doGenerateForTestPoint(testPoint, false, false)
  }
}

async function doGenerateForTestPoint(testPoint: any, clearExisting: boolean, showDialog: boolean = true) {
  if (showDialog) {
    generating.value = true
    showGeneratingDialog.value = true
    generatingTestPointCount.value = 1
    generationProgress.value = 0
    progressMessage.value = ''
  } else {
    generatingTestPointIds.value.push(testPoint.id)
  }

  // 本地任务ID，避免冲突
  let localTaskId: string | null = null

  try {
    // 传递完整的测试点数据
    const asyncResult = await agentApi.designTestCasesAsync({
      test_points: [{
        id: testPoint.id,
        content: testPoint.content,
        test_type: testPoint.test_type,
        design_method: testPoint.design_method,
        priority: testPoint.priority,
        requirement_point_id: testPoint.requirement_point_id
      }],
      module_id: props.moduleId,
      clear_existing: false // 单个测试点不清空整个模块
    })

    localTaskId = asyncResult.task_id
    if (showDialog) {
      currentTaskId.value = localTaskId
    }

    // 如果需要替换，先删除现有用例
    if (clearExisting && testPoint.test_cases?.length > 0) {
      for (const tc of testPoint.test_cases) {
        await requirementApi.deleteModuleTestCase(props.projectId, props.moduleId, tc.id)
      }
    }

    let pollCount = 0
    let errorCount = 0
    const maxPolls = 300

    while (pollCount < maxPolls) {
      // 如果是弹窗模式，检查全局取消状态
      if (showDialog && isCancelling.value) break
      
      await new Promise(resolve => setTimeout(resolve, 1000))
      pollCount++

      try {
        const status = await agentApi.getTaskStatus(localTaskId)
        errorCount = 0
        
        // 只有弹窗模式才更新全局进度
        if (showDialog) {
          generationProgress.value = status.progress
          if ((status as any).message) progressMessage.value = (status as any).message
        }

        if (status.status === 'completed') {
          ElMessage.success('测试用例生成并优化完成')
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
        if (errorCount >= 5) {
          ElMessage.error('获取任务状态失败')
          break
        }
      }
    }
  } catch (error: any) {
    ElMessage.error(error.message || '生成失败')
  } finally {
    if (showDialog) {
      generating.value = false
      showGeneratingDialog.value = false
      generationProgress.value = 0
      currentTaskId.value = null
      progressMessage.value = ''
    } else {
      const index = generatingTestPointIds.value.indexOf(testPoint.id)
      if (index > -1) {
        generatingTestPointIds.value.splice(index, 1)
      }
    }
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

// ==================== 辅助函数 ====================

function getProgressTitle() {
  if (generationProgress.value < 50) {
    return '正在生成测试用例'
  } else {
    return '正在优化测试用例'
  }
}

function getProgressText() {
  if (progressMessage.value) return progressMessage.value
  if (generationProgress.value >= 100) return '处理完成，正在保存...'
  if (generationProgress.value >= 50) return `优化中 ${generationProgress.value}%`
  if (generationProgress.value > 0) return `生成中 ${generationProgress.value}%`
  if (currentTaskId.value) return 'AI智能体正在设计测试用例...'
  return '正在启动任务...'
}

function getProgressHint() {
  if (generatingTestPointCount.value > 1) {
    return `共 ${generatingTestPointCount.value} 个测试点，生成后自动优化`
  }
  return '生成后自动优化，请耐心等待'
}

function getStatusLabel(s: string | undefined | null) {
  const labels: Record<string, string> = { draft: '草稿', under_review: '待评审', approved: '已通过', rejected: '已拒绝' }
  return labels[s || 'draft'] || '草稿'
}

function getStatusClass(s: string | undefined | null) {
  const classes: Record<string, string> = {
    draft: 'inline-flex items-center px-2 py-0.5 bg-gray-100 text-gray-600 text-xs font-medium rounded-full',
    under_review: 'inline-flex items-center px-2 py-0.5 bg-yellow-50 text-yellow-700 text-xs font-medium rounded-full',
    approved: 'inline-flex items-center px-2 py-0.5 bg-green-50 text-green-700 text-xs font-medium rounded-full',
    rejected: 'inline-flex items-center px-2 py-0.5 bg-red-50 text-red-700 text-xs font-medium rounded-full'
  }
  return classes[s || 'draft'] || classes.draft
}

function getDesignMethodLabel(code: string | undefined | null) {
  if (!code) return ''
  // 大小写不敏感匹配（兼容旧数据）
  const lowerCode = code.toLowerCase()
  const method = designMethods.value.find(m => m.code.toLowerCase() === lowerCode)
  // 如果在配置中找到，返回中文名称；否则返回code本身
  return method?.name || code
}

function getDesignMethodClass(code: string | undefined | null) {
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
  // 大小写不敏感匹配
  const lowerCode = (code || '').toLowerCase()
  const color = colorMap[lowerCode] || 'bg-gray-50 text-gray-700'
  return `inline-flex items-center px-2 py-0.5 ${color} text-xs font-medium rounded-full`
}

function getTestCategoryLabel(code: string | undefined | null) {
  if (!code) return ''
  // 大小写不敏感匹配（兼容旧数据）
  const lowerCode = code.toLowerCase()
  const category = testCategories.value.find(c => c.code.toLowerCase() === lowerCode)
  return category?.name || code
}

function getTestCategoryClass(code: string | undefined | null) {
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
  // 大小写不敏感匹配
  const lowerCode = (code || 'functional').toLowerCase()
  const color = colorMap[lowerCode] || 'bg-gray-50 text-gray-700'
  return `inline-flex items-center px-2 py-0.5 ${color} text-xs font-medium rounded-full`
}

function getPriorityLabel(priority: string | undefined | null) {
  const labels: Record<string, string> = { high: '高优先级', medium: '中优先级', low: '低优先级' }
  return labels[priority || 'medium'] || '中优先级'
}

function getPriorityClass(priority: string | undefined | null) {
  const classes: Record<string, string> = {
    high: 'inline-flex items-center px-2 py-0.5 bg-red-50 text-red-700 text-xs font-medium rounded-full',
    medium: 'inline-flex items-center px-2 py-0.5 bg-orange-50 text-orange-700 text-xs font-medium rounded-full',
    low: 'inline-flex items-center px-2 py-0.5 bg-gray-50 text-gray-600 text-xs font-medium rounded-full'
  }
  return classes[priority || 'medium'] || classes.medium
}

onMounted(() => {
  loadHierarchy()
  loadDesignMethods()
  loadTestCategories()
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

:deep(.custom-input .el-input__wrapper) {
  border-radius: 0.75rem;
}

:deep(.is-error .el-input__wrapper),
:deep(.is-error .el-textarea__inner) {
  border-color: #ef4444 !important;
  box-shadow: 0 0 0 1px #ef4444 !important;
}

:deep(.is-error .el-select .el-input__wrapper) {
  border-color: #ef4444 !important;
  box-shadow: 0 0 0 1px #ef4444 !important;
}

.rotate-90 {
  transform: rotate(90deg);
}
</style>

<style>
/* 全局样式：确保下拉框弹出层有正确的 z-index 和宽度 */
.test-point-select-popper {
  z-index: 3000 !important;
}

.test-point-select-popper .el-select-dropdown__item {
  max-width: 600px;
  white-space: normal;
  line-height: 1.5;
  padding: 8px 12px;
  height: auto;
  min-height: 34px;
}

.test-point-select-popper .el-select-dropdown__item span {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.test-point-select-popper .el-select-dropdown__item:hover span {
  white-space: normal;
  word-break: break-all;
}
</style>
