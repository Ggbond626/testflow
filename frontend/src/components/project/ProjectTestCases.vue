<template>
  <div class="project-test-cases">
    <!-- 工具栏 -->
    <div class="mb-6 flex justify-between items-center">
      <div class="flex items-center gap-3">
        <!-- 视图切换 -->
        <div class="bg-gray-100 p-1 rounded-lg flex text-sm font-medium">
          <button
            @click="viewMode = 'hierarchy'"
            class="px-3 py-1.5 rounded-md transition-all flex items-center gap-1.5"
            :class="viewMode === 'hierarchy' ? 'bg-white text-black shadow-sm' : 'text-gray-500 hover:text-gray-900'"
          >
            <el-icon><Operation /></el-icon>
            层级视图
          </button>
          <button
            @click="viewMode = 'flat'"
            class="px-3 py-1.5 rounded-md transition-all flex items-center gap-1.5"
            :class="viewMode === 'flat' ? 'bg-white text-black shadow-sm' : 'text-gray-500 hover:text-gray-900'"
          >
            <el-icon><List /></el-icon>
            列表视图
          </button>
        </div>

        <div class="h-6 w-px bg-gray-200 mx-1"></div>

        <!-- 操作按钮 -->
        <template v-if="canEdit">
          <button
            @click="showImportDialog = true"
            class="px-3 py-1.5 border border-gray-200 text-gray-700 rounded-lg text-sm font-bold hover:bg-gray-50 transition-all flex items-center gap-2"
          >
            <el-icon><Upload /></el-icon>
            导入
          </button>
          
          <el-dropdown trigger="click" @command="handleExport" :disabled="exporting">
            <button :disabled="exporting" class="px-3 py-1.5 border border-gray-200 text-gray-700 rounded-lg text-sm font-bold hover:bg-gray-50 transition-all flex items-center gap-2 disabled:opacity-50">
              <el-icon :class="{ 'animate-spin': exporting }"><Download /></el-icon>
              {{ exporting ? '导出中...' : '导出' }}
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="excel">
                  导出 Excel {{ selectedIds.length > 0 ? `(已选${selectedIds.length}条)` : '(全部)' }}
                </el-dropdown-item>
                <el-dropdown-item command="xmind">
                  导出思维导图 {{ selectedIds.length > 0 ? `(已选${selectedIds.length}条)` : '(全部)' }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <button
            @click="handleBatchOptimize"
            :disabled="selectedIds.length === 0 || optimizing"
            class="px-3 py-1.5 border border-gray-200 text-gray-700 rounded-lg text-sm font-bold hover:bg-gray-50 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <el-icon :class="{ 'animate-spin': optimizing }"><MagicStick /></el-icon>
            {{ optimizing ? '优化中...' : '批量优化' }}
          </button>

          <button
            @click="handleBatchDelete"
            :disabled="selectedIds.length === 0"
            class="px-3 py-1.5 border border-red-200 text-red-500 rounded-lg text-sm font-bold hover:bg-red-50 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <el-icon><Delete /></el-icon>
            批量删除
          </button>
        </template>
      </div>

      <!-- 筛选区 -->
      <div class="flex items-center gap-3">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用例标题/内容..."
          class="custom-input w-64"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 内容区 -->
    <div v-loading="loading" class="min-h-[400px]">
      <!-- 层级视图 -->
      <div v-if="viewMode === 'hierarchy'" class="space-y-6">
        <div v-for="module in filteredModules" :key="module.id" class="border border-gray-100 rounded-2xl overflow-hidden bg-white">
          <!-- 模块头部 -->
          <div class="px-6 py-4 bg-gray-50 border-b border-gray-100 flex items-center justify-between cursor-pointer" @click="toggleModule(module.id)">
            <div class="flex items-center gap-3">
              <el-icon :class="['transition-transform text-gray-400', { 'rotate-90': !collapsedModules.includes(module.id) }]">
                <ArrowRight />
              </el-icon>
              <el-checkbox
                v-if="canEdit"
                v-model="module.selected"
                :indeterminate="module.indeterminate"
                @change="(val) => handleModuleSelect(val, module)"
                @click.stop
                class="mr-2"
              />
              <span class="font-bold text-gray-800">{{ module.name }}</span>
              <span class="px-2 py-0.5 bg-gray-200 text-gray-600 text-xs rounded-full">{{ module.test_cases.length }}</span>
            </div>
          </div>

          <!-- 模块内容 -->
          <div v-show="!collapsedModules.includes(module.id)" class="p-4">
            <el-table
              :data="module.test_cases"
              :style="{ width: '100%' }"
              @selection-change="(selection) => handleSelectionChange(selection, module)"
              ref="moduleTables"
            >
              <el-table-column v-if="canEdit" type="selection" width="55" />
              <el-table-column label="标题" min-width="200">
                <template #default="{ row }">
                  <div class="font-medium text-gray-900">{{ row.title }}</div>
                </template>
              </el-table-column>
              <el-table-column label="测试分类" width="100">
                <template #default="{ row }">
                  <span v-if="row.test_category" :class="getTestCategoryClass(row.test_category)">
                    {{ getTestCategoryLabel(row.test_category) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="设计方法" width="120">
                <template #default="{ row }">
                  <span v-if="row.design_method" :class="getDesignMethodClass(row.design_method)">
                    {{ getDesignMethodLabel(row.design_method) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column min-width="500">
                <!-- 自定义表头模拟两列 -->
                <template #header>
                  <div class="flex items-center w-full">
                    <div class="flex-1 px-2 border-r border-gray-200 text-center">测试步骤</div>
                    <div class="flex-1 px-2 text-center">预期结果</div>
                  </div>
                </template>
                
                <template #default="{ row }">
                  <div class="flex flex-col w-full">
                    <!-- 内容区域：左右分栏 -->
                    <div class="flex border-b border-gray-100 pb-2 mb-2">
                      <!-- 测试步骤 -->
                      <div class="flex-1 pr-4 border-r border-gray-100">
                        <div v-for="(step, idx) in (expandedRows.has(row.id) ? row.test_steps : row.test_steps.slice(0, 2))" :key="idx" class="text-xs text-gray-600 flex gap-2 mb-1">
                          <span class="text-gray-400 select-none">{{ idx + 1 }}.</span>
                          <div class="flex-1 break-words">{{ step.action }}</div>
                        </div>
                      </div>
                      <!-- 预期结果 -->
                      <div class="flex-1 pl-4">
                        <div v-for="(step, idx) in (expandedRows.has(row.id) ? row.test_steps : row.test_steps.slice(0, 2))" :key="idx" class="text-xs text-gray-600 flex gap-2 mb-1">
                          <span class="text-gray-400 select-none">{{ idx + 1 }}.</span>
                          <div class="flex-1 break-words">{{ step.expected }}</div>
                        </div>
                      </div>
                    </div>
                    
                    <!-- 居中的展开/收起按钮 -->
                    <div v-if="row.test_steps.length > 2" 
                         class="text-xs text-blue-500 cursor-pointer hover:underline text-center bg-gray-50 py-1 rounded-md mx-auto w-1/3 transition-colors hover:bg-gray-100"
                         @click="toggleExpand(row.id)">
                      {{ expandedRows.has(row.id) ? '收起' : `展开剩余 ${row.test_steps.length - 2} 步...` }}
                    </div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="优先级" width="100">
                <template #default="{ row }">
                  <span :class="getPriorityClass(row.priority)">{{ getPriorityLabel(row.priority) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <span :class="getStatusClass(row.status)">{{ getStatusLabel(row.status) }}</span>
                </template>
              </el-table-column>
              <el-table-column v-if="canEdit" label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <div class="flex gap-2">
                    <button @click="editTestCase(row)" class="p-1.5 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors">
                      <el-icon><Edit /></el-icon>
                    </button>
                    <button @click="deleteTestCase(row)" class="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                      <el-icon><Delete /></el-icon>
                    </button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>

      <!-- 列表视图 -->
      <div v-else class="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        <el-table
          :data="flatTestCases"
          :style="{ width: '100%' }"
          @selection-change="handleGlobalSelectionChange"
        >
          <el-table-column v-if="canEdit" type="selection" width="55" />
          <el-table-column label="标题" min-width="200" prop="title" />
          <el-table-column label="所属模块" width="150" prop="module_name">
            <template #default="{ row }">
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                {{ row.module_name || '未分类' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="测试分类" width="100">
            <template #default="{ row }">
              <span v-if="row.test_category" :class="getTestCategoryClass(row.test_category)">
                {{ getTestCategoryLabel(row.test_category) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="设计方法" width="120">
            <template #default="{ row }">
              <span v-if="row.design_method" :class="getDesignMethodClass(row.design_method)">
                {{ getDesignMethodLabel(row.design_method) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="优先级" width="100">
            <template #default="{ row }">
              <span :class="getPriorityClass(row.priority)">{{ getPriorityLabel(row.priority) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <span :class="getStatusClass(row.status)">{{ getStatusLabel(row.status) }}</span>
            </template>
          </el-table-column>
          <el-table-column v-if="canEdit" label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <div class="flex gap-2">
                <button @click="editTestCase(row)" class="p-1.5 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors">
                  <el-icon><Edit /></el-icon>
                </button>
                <button @click="deleteTestCase(row)" class="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                  <el-icon><Delete /></el-icon>
                </button>
              </div>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 分页 -->
        <div class="p-4 flex justify-end border-t border-gray-100">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            layout="total, prev, pager, next"
            background
          />
        </div>
      </div>
    </div>

    <!-- 导入对话框 -->
    <el-dialog
      v-model="showImportDialog"
      title="导入测试用例"
      width="500px"
      align-center
      append-to-body
      @close="resetImport"
    >
      <div class="space-y-6">
        <div 
          class="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-black transition-colors cursor-pointer bg-gray-50 relative"
          @click="triggerFileInput"
          @dragover.prevent
          @drop.prevent="handleDrop"
        >
          <input 
            type="file" 
            ref="fileInput" 
            class="hidden" 
            accept=".xlsx,.xls" 
            @change="handleFileChange"
          >
          <el-icon class="text-4xl text-gray-400 mb-2"><UploadFilled /></el-icon>
          <p v-if="!selectedFile" class="text-sm text-gray-600 font-medium">点击或拖拽 Excel 文件到此处</p>
          <div v-else class="text-center">
            <p class="text-sm text-black font-bold mb-1">{{ selectedFile.name }}</p>
            <p class="text-xs text-green-600">{{ (selectedFile.size / 1024).toFixed(1) }} KB</p>
          </div>
          <p class="text-xs text-gray-400 mt-2">支持 .xlsx, .xls 格式</p>
        </div>

        <div class="bg-blue-50 p-4 rounded-xl flex items-start gap-3">
          <el-icon class="text-blue-600 mt-0.5"><InfoFilled /></el-icon>
          <div class="text-xs text-blue-700">
            <p class="font-bold mb-1">导入说明：</p>
            <p>1. 系统将根据“所属模块”自动匹配现有模块。</p>
            <p>2. 匹配失败的用例将归入“未分类”模块。</p>
          </div>
        </div>

        <div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
          <div>
            <p class="text-sm font-bold text-gray-900">自动优化</p>
            <p class="text-xs text-gray-500">导入后自动调用 AI 优化用例步骤</p>
          </div>
          <el-switch v-model="autoOptimize" />
        </div>
      </div>
      <template #footer>
        <div class="flex justify-between items-center">
          <button 
            @click="handleDownloadTemplate" 
            class="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center gap-1"
          >
            <el-icon><Download /></el-icon>
            下载模板
          </button>
          <div class="flex gap-3">
            <button @click="showImportDialog = false" class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors text-sm font-bold">取消</button>
            <button 
              @click="handleStartImport" 
              :disabled="!selectedFile || importing"
              class="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors text-sm font-bold disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <el-icon v-if="importing" class="animate-spin"><Loading /></el-icon>
              {{ importing ? '导入中...' : '开始导入' }}
            </button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="showEditDialog"
      :title="editingTestCase ? '编辑测试用例' : '新增测试用例'"
      width="700px"
      align-center
      append-to-body
      destroy-on-close
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-bold text-gray-700 mb-1">标题 <span class="text-red-500">*</span></label>
          <el-input v-model="editForm.title" placeholder="请输入测试用例标题" />
        </div>

        <div>
          <label class="block text-sm font-bold text-gray-700 mb-1">所属模块</label>
          <el-select 
            v-model="editForm.module_id" 
            placeholder="选择所属模块" 
            class="w-full"
            :disabled="!isUnclassifiedCase"
          >
            <el-option 
              v-for="module in moduleList" 
              :key="module.id" 
              :label="module.name" 
              :value="module.id" 
            />
          </el-select>
          <p v-if="!isUnclassifiedCase" class="text-xs text-gray-400 mt-1">已归属模块的用例不可更改所属模块</p>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-bold text-gray-700 mb-1">测试分类</label>
            <el-select v-model="editForm.test_category" placeholder="选择测试分类" class="w-full">
              <el-option v-for="cat in testCategories" :key="cat.code" :label="cat.name" :value="cat.code" />
            </el-select>
          </div>
          <div>
            <label class="block text-sm font-bold text-gray-700 mb-1">设计方法</label>
            <el-select v-model="editForm.design_method" placeholder="选择设计方法" class="w-full" clearable>
              <el-option v-for="method in designMethods" :key="method.code" :label="method.name" :value="method.code" />
            </el-select>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-bold text-gray-700 mb-1">优先级</label>
            <el-select v-model="editForm.priority" placeholder="选择优先级" class="w-full">
              <el-option label="高" value="high" />
              <el-option label="中" value="medium" />
              <el-option label="低" value="low" />
            </el-select>
          </div>
          <div>
            <label class="block text-sm font-bold text-gray-700 mb-1">状态</label>
            <el-select v-model="editForm.status" placeholder="选择状态" class="w-full">
              <el-option label="草稿" value="draft" />
              <el-option label="评审中" value="under_review" />
              <el-option label="已通过" value="approved" />
            </el-select>
          </div>
        </div>

        <div>
          <label class="block text-sm font-bold text-gray-700 mb-1">前置条件</label>
          <el-input v-model="editForm.preconditions" type="textarea" :rows="2" placeholder="请输入前置条件" />
        </div>

        <div>
          <label class="block text-sm font-bold text-gray-700 mb-1">测试步骤</label>
          <div class="space-y-2">
            <div v-for="(step, index) in editForm.test_steps" :key="index" class="flex gap-2 items-start">
              <span class="text-gray-400 text-sm mt-2">{{ index + 1 }}.</span>
              <div class="flex-1 grid grid-cols-2 gap-2">
                <el-input v-model="step.action" placeholder="操作步骤" size="small" />
                <el-input v-model="step.expected" placeholder="预期结果" size="small" />
              </div>
              <button @click="removeEditStep(index)" class="p-1 text-red-400 hover:text-red-600" :disabled="editForm.test_steps.length <= 1">
                <el-icon><Delete /></el-icon>
              </button>
            </div>
            <button @click="addEditStep" class="text-blue-500 text-sm hover:text-blue-700">+ 添加步骤</button>
          </div>
        </div>

        <div>
          <label class="block text-sm font-bold text-gray-700 mb-1">预期结果</label>
          <el-input v-model="editForm.expected_result" type="textarea" :rows="2" placeholder="请输入预期结果" />
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <button @click="showEditDialog = false" class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors text-sm font-bold">取消</button>
          <button @click="saveTestCase" :disabled="saving" class="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors text-sm font-bold disabled:opacity-50">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Operation, List, Upload, Download, MagicStick, Delete, Search, ArrowRight, ArrowDown, UploadFilled, InfoFilled, Edit, Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { projectApi } from '@/api/project'
import { settingsApi } from '@/api/settings'
import { agentApi } from '@/api/agent'

const props = defineProps<{ projectId: number; canEdit: boolean }>()

// 状态
const loading = ref(false)
const viewMode = ref<'hierarchy' | 'flat'>('hierarchy')
const searchKeyword = ref('')
const showImportDialog = ref(false)
const autoOptimize = ref(false)
const collapsedModules = ref<number[]>([])
const selectedIds = ref<number[]>([])
const expandedRows = ref(new Set<number>())
const moduleTables = ref<any[]>([])

function toggleExpand(id: number) {
  if (expandedRows.value.has(id)) {
    expandedRows.value.delete(id)
  } else {
    expandedRows.value.add(id)
  }
}

// 导入相关
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const importing = ref(false)

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    const file = input.files[0]
    if (!file.name.match(/\.(xlsx|xls)$/)) {
      ElMessage.warning('请选择 Excel 文件 (.xlsx, .xls)')
      return
    }
    selectedFile.value = file
  }
}

function handleDrop(event: DragEvent) {
  const file = event.dataTransfer?.files[0]
  if (file) {
    if (!file.name.match(/\.(xlsx|xls)$/)) {
      ElMessage.warning('请选择 Excel 文件 (.xlsx, .xls)')
      return
    }
    selectedFile.value = file
  }
}

function resetImport() {
  selectedFile.value = null
  if (fileInput.value) fileInput.value.value = ''
  showImportDialog.value = false
}

async function handleDownloadTemplate() {
  try {
    const blob = await projectApi.downloadImportTemplate(props.projectId)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '测试用例导入模板.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('模板下载成功')
  } catch (error: any) {
    ElMessage.error('下载模板失败')
  }
}

async function handleStartImport() {
  if (!selectedFile.value) return
  
  importing.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('auto_optimize', String(autoOptimize.value))
    
    const res = await projectApi.importTestCases(props.projectId, formData)
    
    ElMessage.success(res.message || `成功导入 ${res.imported_count} 条用例`)
    showImportDialog.value = false
    loadData() // 刷新列表
  } catch (error: any) {
    ElMessage.error(error.message || '导入失败')
  } finally {
    importing.value = false
  }
}

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 数据
const modules = ref<any[]>([])
const flatData = ref<any[]>([])

// 设计方法和测试分类配置
const designMethods = ref<Array<{ code: string; name: string }>>([])
const testCategories = ref<Array<{ code: string; name: string }>>([])

// 加载设计方法
async function loadDesignMethods() {
  try {
    const methods = await settingsApi.getDesignMethods()
    designMethods.value = methods.filter((m: any) => m.is_active)
  } catch (error: any) {
    console.error('加载测试设计方法失败:', error)
    // 使用默认设计方法
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

// 加载测试分类
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

// 加载数据
async function loadData() {
  loading.value = true
  try {
    const data = await projectApi.getProjectTestCases(props.projectId, {
      view_mode: viewMode.value,
      keyword: searchKeyword.value || undefined
    })
    
    if (viewMode.value === 'hierarchy') {
      // 层级视图：为每个模块添加选择状态
      modules.value = data.map((m: any) => ({
        ...m,
        selected: false,
        indeterminate: false,
        test_cases: m.test_cases || []
      }))
      // 过滤空模块（未分类除外）
      modules.value = modules.value.filter((m: any) => m.test_cases.length > 0 || m.id === 0)
    } else {
      // 扁平视图
      flatData.value = data
      total.value = data.length
    }
  } catch (error: any) {
    ElMessage.error(error.message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

// 视图切换时重新加载
watch(viewMode, () => {
  loadData()
})

// 搜索防抖
let searchTimer: any = null
watch(searchKeyword, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadData()
  }, 300)
})

// 计算属性
const filteredModules = computed(() => modules.value)
const flatTestCases = computed(() => flatData.value)

// 方法
function toggleModule(id: number) {
  const index = collapsedModules.value.indexOf(id)
  if (index > -1) {
    collapsedModules.value.splice(index, 1)
  } else {
    collapsedModules.value.push(id)
  }
}

function handleModuleSelect(val: string | number | boolean, module: any) {
  module.indeterminate = false
  // Find the index of the module in the filteredModules list
  const index = filteredModules.value.findIndex(m => m.id === module.id)
  if (index > -1 && moduleTables.value && moduleTables.value[index]) {
    moduleTables.value[index].toggleAllSelection()
  }
}

// 存储每个模块的选中用例
const moduleSelections = ref<Map<number, any[]>>(new Map())

function handleSelectionChange(selection: any[], module: any) {
  const count = selection.length
  const totalCount = module.test_cases.length
  module.selected = count === totalCount && totalCount > 0
  module.indeterminate = count > 0 && count < totalCount
  
  // 保存该模块的选中项
  moduleSelections.value.set(module.id, selection)
  
  // 更新全局选中ID
  updateSelectedIds()
}

function handleGlobalSelectionChange(selection: any[]) {
  selectedIds.value = selection.map(item => item.id)
}

function updateSelectedIds() {
  // 从所有模块的选中项中收集ID
  const ids: number[] = []
  moduleSelections.value.forEach((selection) => {
    selection.forEach((tc: any) => ids.push(tc.id))
  })
  selectedIds.value = ids
}

const exporting = ref(false)

async function handleExport(command: string) {
  exporting.value = true
  try {
    // 如果有选中的用例，只导出选中的；否则导出全部
    const idsToExport = selectedIds.value.length > 0 ? selectedIds.value : undefined
    
    const blob = await projectApi.exportTestCases(props.projectId, idsToExport, command)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 生成文件名
    const now = new Date()
    const timestamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`
    const ext = command === 'xmind' ? 'xmind' : 'xlsx'
    const filename = `测试用例_${timestamp}.${ext}`
    link.download = filename
    
    // 触发下载
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    const count = idsToExport ? idsToExport.length : '全部'
    const formatName = command === 'xmind' ? '思维导图' : 'Excel'
    ElMessage.success(`导出${formatName}成功，共 ${count} 条用例`)
  } catch (error: any) {
    ElMessage.error(error.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

// 优化中状态
const optimizing = ref(false)

async function handleBatchOptimize() {
  if (selectedIds.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(
      `确定优化选中的 ${selectedIds.value.length} 条测试用例吗？\n优化将使用AI提升测试步骤和预期结果的质量。`,
      '批量优化确认',
      { type: 'info', confirmButtonText: '开始优化', cancelButtonText: '取消' }
    )
    
    optimizing.value = true
    
    // 收集选中的测试用例完整数据
    const selectedTestCases: any[] = []
    let moduleId = 0
    
    moduleSelections.value.forEach((selection, mId) => {
      if (selection.length > 0) {
        moduleId = mId  // 使用第一个有选中项的模块ID
        selection.forEach(tc => {
          selectedTestCases.push({
            id: tc.id,
            title: tc.title,
            description: tc.description,
            preconditions: tc.preconditions,
            test_steps: tc.test_steps,
            expected_result: tc.expected_result
          })
        })
      }
    })
    
    if (selectedTestCases.length === 0) {
      ElMessage.warning('请选择要优化的测试用例')
      return
    }
    
    // 使用现有的 agentApi 启动异步优化任务
    const result = await agentApi.optimizeTestCasesBatch({
      test_cases: selectedTestCases,
      module_id: moduleId,
      auto_save: true,
      optimization_requirements: '全面优化测试用例质量，确保测试步骤清晰、预期结果明确'
    })
    const taskId = result.task_id
    
    ElMessage.info(`优化任务已启动，共 ${selectedTestCases.length} 个用例`)
    
    // 轮询任务状态
    const pollInterval = setInterval(async () => {
      try {
        const status = await agentApi.getTaskStatus(taskId)
        
        if (status.status === 'completed') {
          clearInterval(pollInterval)
          optimizing.value = false
          ElMessage.success(`优化完成！成功优化 ${status.result?.updated_count || 0} 个用例`)
          selectedIds.value = []
          moduleSelections.value.clear()
          loadData()
        } else if (status.status === 'failed') {
          clearInterval(pollInterval)
          optimizing.value = false
          ElMessage.error(`优化失败：${status.error || '未知错误'}`)
        }
        // running 状态继续等待
      } catch (e) {
        clearInterval(pollInterval)
        optimizing.value = false
        console.error('轮询任务状态失败:', e)
      }
    }, 2000)
    
  } catch (error: any) {
    optimizing.value = false
    if (error !== 'cancel') {
      ElMessage.error(error.message || '优化失败')
    }
  }
}

async function handleBatchDelete() {
  if (selectedIds.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedIds.value.length} 条测试用例吗？`,
      '批量删除确认',
      { type: 'warning' }
    )
    
    const result = await projectApi.batchDeleteTestCases(props.projectId, selectedIds.value)
    ElMessage.success(result.message)
    selectedIds.value = []
    loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

// ==================== 编辑/删除单个用例 ====================
const showEditDialog = ref(false)
const editingTestCase = ref<any>(null)
const saving = ref(false)

const editForm = ref({
  title: '',
  description: '',
  preconditions: '',
  test_steps: [] as Array<{ step: number; action: string; expected: string }>,
  expected_result: '',
  design_method: '',
  test_category: 'functional',
  priority: 'medium',
  status: 'draft',
  module_id: null as number | null
})

// 模块列表（从 modules 中提取）
const moduleList = computed(() => modules.value.map(m => ({ id: m.id, name: m.name })))

// 是否为未分类用例（只有未分类用例可以编辑所属模块）
const isUnclassifiedCase = computed(() => {
  if (!editingTestCase.value) return false
  // check if it's from unclassified (module_id is null/0/undefined)
  const tc = editingTestCase.value
  return !tc.module_id
})

function editTestCase(tc: any) {
  editingTestCase.value = tc
  editForm.value = {
    title: tc.title || '',
    description: tc.description || '',
    preconditions: tc.preconditions || '',
    test_steps: tc.test_steps?.length ? [...tc.test_steps] : [{ step: 1, action: '', expected: '' }],
    expected_result: tc.expected_result || '',
    design_method: tc.design_method || '',
    test_category: tc.test_category || 'functional',
    priority: tc.priority || 'medium',
    status: tc.status || 'draft',
    module_id: tc.module_id || null
  }
  showEditDialog.value = true
}

function addEditStep() {
  editForm.value.test_steps.push({ step: editForm.value.test_steps.length + 1, action: '', expected: '' })
}

function removeEditStep(index: number) {
  editForm.value.test_steps.splice(index, 1)
  editForm.value.test_steps.forEach((step, i) => { step.step = i + 1 })
}

async function saveTestCase() {
  if (!editForm.value.title.trim()) {
    ElMessage.warning('请输入测试用例标题')
    return
  }

  saving.value = true
  try {
    const validSteps = editForm.value.test_steps.filter(s => s.action.trim())
    const data: any = {
      title: editForm.value.title,
      description: editForm.value.description || undefined,
      preconditions: editForm.value.preconditions || undefined,
      test_steps: validSteps.length > 0 ? validSteps : undefined,
      expected_result: editForm.value.expected_result || undefined,
      design_method: editForm.value.design_method || undefined,
      test_category: editForm.value.test_category || undefined,
      priority: editForm.value.priority || undefined,
      status: editForm.value.status,
      module_id: isUnclassifiedCase.value ? editForm.value.module_id : undefined
    }

    if (editingTestCase.value) {
      await projectApi.updateTestCase(props.projectId, editingTestCase.value.id, data)
      ElMessage.success('更新成功')
    }
    showEditDialog.value = false
    loadData()
  } catch (error: any) {
    ElMessage.error(error.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function deleteTestCase(tc: any) {
  try {
    await ElMessageBox.confirm('确定要删除这个测试用例吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await projectApi.deleteTestCase(props.projectId, tc.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

// 辅助函数
function getPriorityLabel(val: string) {
  const map: any = { high: '高', medium: '中', low: '低' }
  return map[val] || val
}

function getPriorityClass(val: string) {
  const map: any = {
    high: 'text-red-600 bg-red-50 px-2 py-0.5 rounded text-xs',
    medium: 'text-orange-600 bg-orange-50 px-2 py-0.5 rounded text-xs',
    low: 'text-gray-600 bg-gray-50 px-2 py-0.5 rounded text-xs'
  }
  return map[val] || ''
}

function getStatusLabel(val: string) {
  const map: any = { draft: '草稿', approved: '已通过', under_review: '评审中' }
  return map[val] || val
}

function getStatusClass(val: string) {
  const map: any = {
    draft: 'text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full text-xs',
    approved: 'text-green-600 bg-green-50 px-2 py-0.5 rounded-full text-xs',
    under_review: 'text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full text-xs'
  }
  return map[val] || ''
}

function getDesignMethodLabel(code: string | undefined | null) {
  if (!code) return ''
  // 大小写不敏感匹配（兼容旧数据）
  const lowerCode = code.toLowerCase()
  const method = designMethods.value.find(m => m.code.toLowerCase() === lowerCode)
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
  const baseClass = 'inline-flex items-center px-2 py-0.5 text-xs font-medium rounded'
  const lowerCode = (code || '').toLowerCase()
  return `${baseClass} ${colorMap[lowerCode] || 'bg-blue-50 text-blue-700'}`
}

function getTestCategoryLabel(code: string | undefined | null) {
  if (!code) return ''
  const lowerCode = code.toLowerCase()
  const category = testCategories.value.find(c => c.code.toLowerCase() === lowerCode)
  return category?.name || code
}

function getTestCategoryClass(code: string | undefined | null) {
  const colorMap: Record<string, string> = {
    functional: 'bg-blue-50 text-blue-700',
    performance: 'bg-green-50 text-green-700',
    security: 'bg-red-50 text-red-700',
    usability: 'bg-yellow-50 text-yellow-700',
    compatibility: 'bg-teal-50 text-teal-700',
    reliability: 'bg-purple-50 text-purple-700'
  }
  const baseClass = 'inline-flex items-center px-2 py-0.5 text-xs font-medium rounded'
  const lowerCode = (code || '').toLowerCase()
  return `${baseClass} ${colorMap[lowerCode] || 'bg-gray-50 text-gray-700'}`
}

onMounted(async () => {
  // 先加载配置数据
  await Promise.all([loadDesignMethods(), loadTestCategories()])
  // 再加载测试用例数据
  loadData()
})
</script>

<style scoped>
.rotate-90 {
  transform: rotate(90deg);
}

:deep(.el-table__header) {
  font-weight: bold;
  color: #111;
}

/* Override Element Plus Checkbox Indeterminate and Checked Colors */
:deep(.el-checkbox__input.is-indeterminate .el-checkbox__inner),
:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: black !important;
  border-color: black !important;
}

:deep(.el-checkbox__input.is-checked + .el-checkbox__label) {
  color: black !important;
}
</style>
