<template>
  <div class="module-list">
    <!-- 操作栏 -->
    <div class="mb-6">
      <div class="flex flex-col lg:flex-row gap-4 items-stretch lg:items-center">
        <!-- 左侧搜索框 - 独占一行或大部分空间 -->
        <div class="flex-1">
          <el-input
            v-model="searchText"
            placeholder="搜索模块名称或描述"
            clearable
            size="large"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        
        <!-- 右侧筛选和按钮 -->
        <div class="flex flex-col sm:flex-row gap-3 lg:flex-shrink-0">
          <!-- 优先级筛选 -->
          <div class="w-full sm:w-[140px] lg:w-[160px]">
            <el-select 
              v-model="filterPriority" 
              placeholder="筛选优先级" 
              clearable 
              class="w-full filter-select"
              size="large"
              popper-class="filter-dropdown"
            >
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
              <el-option label="紧急" value="critical" />
            </el-select>
          </div>
          
          <!-- 状态筛选 -->
          <div class="w-full sm:w-[140px] lg:w-[160px]">
            <el-select 
              v-model="filterStatus" 
              placeholder="筛选状态" 
              clearable 
              class="w-full filter-select"
              size="large"
              popper-class="filter-dropdown"
            >
              <el-option label="规划中" value="planning" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已完成" value="completed" />
              <el-option label="暂停" value="on_hold" />
            </el-select>
          </div>
          
          <!-- 创建按钮 -->
          <button
            v-if="canEdit"
            @click="showCreateDialog"
            class="bg-black hover:bg-gray-800 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-black/20 transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2 whitespace-nowrap"
          >
            <el-icon><Plus /></el-icon>
            创建模块
          </button>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="py-12">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 空状态 -->
    <div v-else-if="filteredModules.length === 0" class="text-center py-16">
      <el-empty description="暂无模块" :image-size="120">
        <button
          v-if="canEdit"
          @click="showCreateDialog"
          class="mt-4 px-6 py-2 bg-black text-white rounded-xl text-sm font-bold hover:bg-gray-800 transition-colors"
        >
          创建第一个模块
        </button>
      </el-empty>
    </div>

    <!-- 模块列表 -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      <div
        v-for="module in filteredModules"
        :key="module.id"
        class="group border rounded-2xl p-6 transition-all duration-300"
        :class="isAssignedToModule(module) 
          ? 'bg-white/50 hover:bg-white/80 border-gray-100 hover:border-gray-300 hover:-translate-y-1 hover:shadow-xl cursor-pointer' 
          : 'bg-gray-50/50 border-gray-200 opacity-70'"
      >
        <!-- 模块头部 -->
        <div class="flex justify-between items-start mb-4">
          <div 
            class="flex-1 mr-2" 
            :class="isAssignedToModule(module) ? 'cursor-pointer' : 'cursor-not-allowed'"
            @click="isAssignedToModule(module) && viewModule(module)"
          >
            <div class="flex items-center gap-2 mb-1">
              <h3 class="text-lg font-bold line-clamp-2" :class="isAssignedToModule(module) ? 'text-gray-900 group-hover:text-black' : 'text-gray-500'">
                {{ module.name }}
              </h3>
              <el-icon v-if="!isAssignedToModule(module)" class="text-gray-400" :size="16">
                <Lock />
              </el-icon>
            </div>
            <div class="text-xs text-gray-400">ID: {{ module.id }}</div>
          </div>
          <el-dropdown v-if="canEdit" @command="handleCommand" trigger="click">
            <button 
              class="p-2 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-700 transition-all flex-shrink-0" 
              @click.stop
            >
              <el-icon :size="18"><MoreFilled /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu class="!rounded-xl !border-0 !shadow-xl">
                <el-dropdown-item :command="`edit-${module.id}`" class="!py-2.5 !px-4">
                  <div class="flex items-center gap-2">
                    <el-icon><Edit /></el-icon>
                    <span>编辑</span>
                  </div>
                </el-dropdown-item>
                <el-dropdown-item :command="`assign-${module.id}`" class="!py-2.5 !px-4">
                  <div class="flex items-center gap-2">
                    <el-icon><User /></el-icon>
                    <span>分配负责人</span>
                  </div>
                </el-dropdown-item>
                <el-dropdown-item :command="`delete-${module.id}`" divided class="!text-red-500 !py-2.5 !px-4">
                  <div class="flex items-center gap-2">
                    <el-icon><Delete /></el-icon>
                    <span>删除</span>
                  </div>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <!-- 标签 -->
        <div class="flex gap-2 mb-4 flex-wrap">
          <span class="px-3 py-1 rounded-lg text-xs font-bold" :class="getPriorityClass(module.priority)">
            {{ getPriorityLabel(module.priority) }}
          </span>
          <span class="px-3 py-1 rounded-lg text-xs font-bold" :class="getStatusClass(module.status)">
            {{ getStatusLabel(module.status) }}
          </span>
        </div>

        <!-- 描述 -->
        <p class="text-sm text-gray-600 mb-4 line-clamp-2 min-h-[40px]">
          {{ module.description || '暂无描述' }}
        </p>

        <!-- 统计信息 -->
        <div class="grid grid-cols-3 gap-2 mb-4 text-center">
          <div class="bg-gray-50 rounded-xl p-3 hover:bg-gray-100 transition-colors">
            <div class="text-xl font-bold text-gray-900">{{ module.stats?.requirement_points_count || 0 }}</div>
            <div class="text-xs text-gray-500 mt-1">需求点</div>
          </div>
          <div class="bg-gray-50 rounded-xl p-3 hover:bg-gray-100 transition-colors">
            <div class="text-xl font-bold text-gray-900">{{ module.stats?.test_points_count || 0 }}</div>
            <div class="text-xs text-gray-500 mt-1">测试点</div>
          </div>
          <div class="bg-gray-50 rounded-xl p-3 hover:bg-gray-100 transition-colors">
            <div class="text-xl font-bold text-gray-900">{{ module.stats?.test_cases_count || 0 }}</div>
            <div class="text-xs text-gray-500 mt-1">用例</div>
          </div>
        </div>

        <!-- 进度条 -->
        <div class="mb-4">
          <div class="flex justify-between items-center mb-2">
            <span class="text-xs font-medium text-gray-600">完成度</span>
            <span class="text-sm font-bold text-gray-900">{{ (module.stats?.completion_rate || 0).toFixed(0) }}%</span>
          </div>
          <div class="bg-gray-100 rounded-full h-2 overflow-hidden">
            <div
              class="bg-gradient-to-r from-gray-800 to-black h-full rounded-full transition-all duration-500"
              :style="{ width: (module.stats?.completion_rate || 0) + '%' }"
            ></div>
          </div>
        </div>

        <!-- 负责人 -->
        <div class="flex items-center justify-between border-t border-gray-100 pt-4">
          <div v-if="module.assignees && module.assignees.length > 0" class="flex items-center gap-2 text-xs text-gray-600">
            <el-icon :size="16"><User /></el-icon>
            <span class="font-medium line-clamp-1">{{ module.assignees.map(a => a.username).join(', ') }}</span>
          </div>
          <div v-else class="flex items-center gap-2 text-xs text-gray-400">
            <el-icon :size="16"><User /></el-icon>
            <span>未分配</span>
          </div>
          <div class="text-xs text-gray-400">
            {{ formatDate(module.created_at) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑模块' : '创建模块'"
      width="560px"
      @close="resetForm"
      :close-on-click-modal="false"
      align-center
      class="module-dialog"
    >
      <el-form
        ref="formRef"
        :model="moduleForm"
        :rules="formRules"
        label-width="90px"
        label-position="left"
      >
        <el-form-item label="模块名称" prop="name">
          <el-input 
            v-model="moduleForm.name" 
            placeholder="请输入模块名称，例如：用户管理" 
            maxlength="100"
            show-word-limit
            size="large"
          />
        </el-form-item>
        
        <el-form-item label="模块描述" prop="description">
          <el-input
            v-model="moduleForm.description"
            type="textarea"
            :rows="4"
            placeholder="请简要描述该模块的功能和职责（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        
        <div class="grid grid-cols-2 gap-4">
          <el-form-item label="优先级" prop="priority">
            <el-select v-model="moduleForm.priority" class="w-full" size="large">
              <el-option label="低" value="low">
                <div class="flex items-center justify-between">
                  <span>低</span>
                  <span class="text-xs text-gray-400">可以延后</span>
                </div>
              </el-option>
              <el-option label="中" value="medium">
                <div class="flex items-center justify-between">
                  <span>中</span>
                  <span class="text-xs text-gray-400">正常优先</span>
                </div>
              </el-option>
              <el-option label="高" value="high">
                <div class="flex items-center justify-between">
                  <span>高</span>
                  <span class="text-xs text-gray-400">优先处理</span>
                </div>
              </el-option>
              <el-option label="紧急" value="critical">
                <div class="flex items-center justify-between">
                  <span>紧急</span>
                  <span class="text-xs text-gray-400">立即处理</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
          
          <el-form-item label="状态" prop="status">
            <el-select v-model="moduleForm.status" class="w-full" size="large">
              <el-option label="规划中" value="planning" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已完成" value="completed" />
              <el-option label="暂停" value="on_hold" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>

      <template #footer>
        <div class="flex justify-end gap-3 pt-4">
          <button 
            @click="dialogVisible = false" 
            class="px-6 py-2.5 rounded-xl text-gray-600 font-bold hover:bg-gray-100 transition-all border border-gray-200"
          >
            取消
          </button>
          <button 
            @click="handleSubmit" 
            :disabled="submitting" 
            class="px-6 py-2.5 bg-black text-white rounded-xl font-bold hover:bg-gray-800 transition-all shadow-lg shadow-black/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="submitting">提交中...</span>
            <span v-else>{{ isEdit ? '保存更新' : '创建模块' }}</span>
          </button>
        </div>
      </template>
    </el-dialog>

    <!-- 分配负责人对话框 -->
    <el-dialog
      v-model="assignDialogVisible"
      title="分配负责人"
      width="540px"
      :close-on-click-modal="false"
      align-center
      class="assign-dialog"
    >
      <!-- 当前负责人列表 -->
      <div class="mb-6">
        <h4 class="font-bold text-gray-800 mb-3 flex items-center gap-2">
          <el-icon><User /></el-icon>
          当前负责人
        </h4>
        <div v-if="currentAssignees.length === 0" class="text-center py-8 bg-gray-50 rounded-xl">
          <el-icon :size="32" class="text-gray-300 mb-2"><User /></el-icon>
          <div class="text-sm text-gray-400">暂无负责人</div>
        </div>
        <div v-else class="space-y-2">
          <div
            v-for="assignee in currentAssignees"
            :key="assignee.id"
            class="flex items-center justify-between bg-gray-50 hover:bg-gray-100 rounded-xl p-4 transition-colors"
          >
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-gradient-to-br from-gray-600 to-black text-white flex items-center justify-center font-bold text-sm">
                {{ assignee.username.charAt(0).toUpperCase() }}
              </div>
              <div>
                <div class="text-sm font-bold text-gray-900">{{ assignee.username }}</div>
                <div class="text-xs text-gray-500">{{ assignee.role || 'member' }}</div>
              </div>
            </div>
            <button
              @click="removeAssignee(assignee.user_id)"
              class="px-3 py-1.5 text-red-500 hover:bg-red-50 rounded-lg text-xs font-medium transition-colors"
            >
              移除
            </button>
          </div>
        </div>
      </div>

      <!-- 添加新成员 -->
      <div class="border-t border-gray-100 pt-6">
        <h4 class="font-bold text-gray-800 mb-3 flex items-center gap-2">
          <el-icon><Plus /></el-icon>
          添加成员
        </h4>
        <el-form label-width="0">
          <el-form-item>
            <el-select 
              v-model="assignUserId" 
              placeholder="选择项目成员" 
              class="w-full"
              size="large"
              filterable
            >
              <el-option
                v-for="member in availableMembers"
                :key="member.user_id"
                :label="member.user.username"
                :value="member.user_id"
              >
                <div class="flex items-center gap-3 py-1">
                  <div class="w-8 h-8 rounded-full bg-gradient-to-br from-gray-600 to-black text-white flex items-center justify-center font-bold text-xs">
                    {{ member.user.username.charAt(0).toUpperCase() }}
                  </div>
                  <div>
                    <div class="text-sm font-medium">{{ member.user.username }}</div>
                    <div class="text-xs text-gray-400">{{ member.user.email }}</div>
                  </div>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <div class="flex justify-end gap-3 pt-4">
          <button 
            @click="assignDialogVisible = false" 
            class="px-6 py-2.5 rounded-xl text-gray-600 font-bold hover:bg-gray-100 transition-all border border-gray-200"
          >
            关闭
          </button>
          <button 
            @click="handleAssign" 
            :disabled="!assignUserId" 
            class="px-6 py-2.5 bg-black text-white rounded-xl font-bold hover:bg-gray-800 transition-all shadow-lg shadow-black/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span class="flex items-center gap-2">
              <el-icon><Plus /></el-icon>
              分配负责人
            </span>
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search, MoreFilled, User, Edit, Delete, Lock } from '@element-plus/icons-vue'
import { moduleApi, type ModuleDetail, type ModuleCreateRequest, type ModuleUpdateRequest, type ModulePriority, type ModuleStatus } from '@/api/module'
import { projectApi, type ProjectMember } from '@/api/project'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  projectId: number
  canEdit: boolean
}>()

const authStore = useAuthStore()

// 检查当前用户是否被分配到该模块
const isAssignedToModule = (module: ModuleDetail): boolean => {
  // 管理员或项目所有者可以访问所有模块
  if (props.canEdit) return true
  
  // 检查当前用户是否在模块的负责人列表中
  const currentUserId = authStore.user?.id
  if (!currentUserId) return false
  
  return module.assignees?.some(a => a.user_id === currentUserId) || false
}

const router = useRouter()

// 数据状态
const modules = ref<ModuleDetail[]>([])
const projectMembers = ref<ProjectMember[]>([])
const loading = ref(false)
const searchText = ref('')
const filterPriority = ref<ModulePriority | ''>('')
const filterStatus = ref<ModuleStatus | ''>('')

// 对话框状态
const dialogVisible = ref(false)
const assignDialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const currentModuleId = ref(0)
const currentAssignees = ref<any[]>([])
const assignUserId = ref<number | null>(null)

// 表单
const formRef = ref<FormInstance>()
const moduleForm = ref<ModuleCreateRequest & { id?: number }>({
  name: '',
  description: '',
  priority: 'medium',
  status: 'planning'
})

// 表单验证
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入模块名称', trigger: 'blur' },
    { min: 1, max: 100, message: '模块名称长度在1-100个字符', trigger: 'blur' }
  ]
}

// 筛选后的模块
const filteredModules = computed(() => {
  return modules.value.filter(module => {
    const matchSearch = !searchText.value ||
      module.name.toLowerCase().includes(searchText.value.toLowerCase()) ||
      (module.description && module.description.toLowerCase().includes(searchText.value.toLowerCase()))
    
    const matchPriority = !filterPriority.value || module.priority === filterPriority.value
    
    const matchStatus = !filterStatus.value || module.status === filterStatus.value
    
    return matchSearch && matchPriority && matchStatus
  })
})

// 可用成员（排除已分配的）
const availableMembers = computed(() => {
  const assignedUserIds = currentAssignees.value.map(a => a.user_id)
  return projectMembers.value.filter(m => !assignedUserIds.includes(m.user_id))
})

// 优先级标签
const getPriorityLabel = (priority: string) => {
  const labels: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    critical: '紧急'
  }
  return labels[priority] || priority
}

// 优先级样式
const getPriorityClass = (priority: string) => {
  const classes: Record<string, string> = {
    low: 'bg-gray-100 text-gray-600',
    medium: 'bg-yellow-100 text-yellow-700',
    high: 'bg-orange-100 text-orange-700',
    critical: 'bg-red-100 text-red-700'
  }
  return classes[priority] || 'bg-gray-100 text-gray-600'
}

// 状态标签
const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    planning: '规划中',
    in_progress: '进行中',
    completed: '已完成',
    on_hold: '暂停'
  }
  return labels[status] || status
}

// 状态样式
const getStatusClass = (status: string) => {
  const classes: Record<string, string> = {
    planning: 'bg-blue-100 text-blue-700',
    in_progress: 'bg-green-100 text-green-700',
    completed: 'bg-gray-100 text-gray-600',
    on_hold: 'bg-yellow-100 text-yellow-700'
  }
  return classes[status] || 'bg-gray-100 text-gray-600'
}

// 加载模块列表
const loadModules = async () => {
  loading.value = true
  try {
    const response = await moduleApi.getModules(props.projectId)
    modules.value = response.modules
  } catch (error: any) {
    console.error('加载模块列表失败:', error)
    ElMessage.error('加载模块列表失败')
  } finally {
    loading.value = false
  }
}

// 加载项目成员
const loadProjectMembers = async () => {
  try {
    projectMembers.value = await projectApi.getProjectMembers(props.projectId)
  } catch (error: any) {
    console.error('加载项目成员失败:', error)
  }
}

// 查看模块
const viewModule = (module: ModuleDetail) => {
  if (!isAssignedToModule(module)) {
    ElMessage.warning('您没有权限访问此模块，请联系管理员分配任务')
    return
  }
  router.push(`/projects/${props.projectId}/modules/${module.id}`)
}

// 显示创建对话框
const showCreateDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
  resetForm()
}

// 编辑模块
const editModule = (module: ModuleDetail) => {
  isEdit.value = true
  dialogVisible.value = true
  
  moduleForm.value = {
    id: module.id,
    name: module.name,
    description: module.description,
    priority: module.priority,
    status: module.status
  }
}

// 删除模块
const deleteModule = async (module: ModuleDetail) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模块 "${module.name}" 吗？此操作将同时删除该模块下的所有需求和测试用例！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: '!bg-black !border-black'
      }
    )

    await moduleApi.deleteModule(props.projectId, module.id)
    ElMessage.success('模块删除成功')
    loadModules()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除模块失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 显示分配对话框
const showAssignDialog = async (module: ModuleDetail) => {
  currentModuleId.value = module.id
  currentAssignees.value = module.assignees
  assignUserId.value = null
  assignDialogVisible.value = true
}

// 处理命令
const handleCommand = (command: string) => {
  const [action, id] = command.split('-')
  const moduleId = parseInt(id)
  const module = modules.value.find(m => m.id === moduleId)

  if (!module) return

  if (action === 'edit') {
    editModule(module)
  } else if (action === 'delete') {
    deleteModule(module)
  } else if (action === 'assign') {
    showAssignDialog(module)
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    if (isEdit.value && moduleForm.value.id) {
      // 更新模块
      const updateData: ModuleUpdateRequest = {
        name: moduleForm.value.name,
        description: moduleForm.value.description,
        priority: moduleForm.value.priority,
        status: moduleForm.value.status
      }
      await moduleApi.updateModule(props.projectId, moduleForm.value.id, updateData)
      ElMessage.success('模块更新成功')
    } else {
      // 创建模块
      await moduleApi.createModule(props.projectId, moduleForm.value)
      ElMessage.success('模块创建成功')
    }

    dialogVisible.value = false
    loadModules()
  } catch (error: any) {
    console.error('操作失败:', error)
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

// 分配负责人
const handleAssign = async () => {
  if (!assignUserId.value) return

  try {
    await moduleApi.assignModule(props.projectId, currentModuleId.value, {
      user_id: assignUserId.value
    })
    ElMessage.success('负责人分配成功')
    assignDialogVisible.value = false
    loadModules()
  } catch (error: any) {
    console.error('分配失败:', error)
    ElMessage.error(error.response?.data?.detail || '分配失败')
  }
}

// 移除负责人
const removeAssignee = async (userId: number) => {
  try {
    await moduleApi.removeAssignment(props.projectId, currentModuleId.value, userId)
    ElMessage.success('负责人移除成功')
    currentAssignees.value = currentAssignees.value.filter(a => a.user_id !== userId)
    loadModules()
  } catch (error: any) {
    console.error('移除失败:', error)
    ElMessage.error(error.response?.data?.detail || '移除失败')
  }
}

// 重置表单
const resetForm = () => {
  moduleForm.value = {
    name: '',
    description: '',
    priority: 'medium',
    status: 'planning'
  }
  formRef.value?.resetFields()
}

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  if (days < 30) return `${Math.floor(days / 7)}周前`
  if (days < 365) return `${Math.floor(days / 30)}月前`
  return `${Math.floor(days / 365)}年前`
}

// 初始化
onMounted(() => {
  loadModules()
  loadProjectMembers()
})
</script>

<style scoped>
/* 输入框和选择器样式 */
:deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.6) inset;
  border-radius: 0.75rem;
  padding: 8px 16px;
  min-height: 44px;
  transition: all 0.2s;
}

:deep(.el-select .el-input__wrapper) {
  cursor: pointer;
}

:deep(.el-select .el-input.is-focus .el-input__wrapper) {
  box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.15) inset !important;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #9ca3af inset;
}

:deep(.el-input__wrapper.is-focus) {
  background-color: #ffffff;
  box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.15) inset !important;
}

:deep(.el-input__inner) {
  font-size: 15px;
  height: auto;
  color: #111827;
}

:deep(.el-input__inner::placeholder) {
  color: #9ca3af;
}

:deep(.el-select) {
  width: 100%;
}

:deep(.el-select .el-input__wrapper) {
  background-color: #ffffff;
  border: 1px solid #d1d5db;
  box-shadow: none;
  padding: 8px 16px;
  min-height: 44px;
  transition: all 0.2s;
}

:deep(.el-select .el-input__wrapper:hover) {
  border-color: #9ca3af;
}

:deep(.el-select.is-focus .el-input__wrapper) {
  border-color: #374151 !important;
}

:deep(.el-select .el-input__inner) {
  height: auto;
  font-size: 15px;
  color: #111827;
  text-align: left;
  font-weight: 500;
}

:deep(.el-input--large .el-input__wrapper) {
  padding: 12px 16px;
  min-height: 48px;
}

/* 筛选器专用样式 */
.filter-select :deep(.el-input__wrapper) {
  background-color: #ffffff !important;
  border: 2px solid #d1d5db !important;
  box-shadow: none !important;
}

.filter-select :deep(.el-input__wrapper:hover) {
  border-color: #9ca3af !important;
}

.filter-select :deep(.el-input.is-focus .el-input__wrapper) {
  border-color: #374151 !important;
}

.filter-select :deep(.el-input__inner) {
  color: #111827 !important;
  font-size: 14px !important;
  font-weight: 500 !important;
}

/* 强制显示 Placeholder */
.filter-select :deep(.el-input__inner)::placeholder {
  color: #6b7280 !important;
  opacity: 1 !important;
  font-weight: 500 !important;
}

.filter-select :deep(.el-select__placeholder) {
  color: #6b7280 !important;
  font-weight: 500 !important;
  opacity: 1 !important;
}

/* 确保没有选中值时显示 Placeholder */
.filter-select :deep(.el-select__selected-item) {
  display: block !important;
}

/* 下拉箭头样式 */
.filter-select :deep(.el-select__caret) {
  color: #6b7280 !important;
  font-size: 14px !important;
}

:deep(.el-input-group__prepend),
:deep(.el-input-group__append) {
  background-color: #f9fafb;
  border-radius: 0.75rem;
  padding: 10px 16px;
}

/* 对话框样式优化 */
:deep(.el-dialog) {
  border-radius: 1.5rem !important;
  overflow: hidden;
}

:deep(.el-dialog__header) {
  padding: 24px 24px 16px;
  border-bottom: 1px solid #f3f4f6;
}

:deep(.el-dialog__body) {
  padding: 24px;
}

:deep(.el-dialog__footer) {
  padding: 16px 24px 24px;
  border-top: 1px solid #f3f4f6;
}

:deep(.el-form-item__label) {
  font-weight: 600;
  color: #374151;
}

:deep(.el-textarea__inner) {
  background-color: #f9fafb;
  box-shadow: 0 0 0 1px #e5e7eb inset;
  border-radius: 0.75rem;
  padding: 12px 16px;
  font-size: 15px;
}

:deep(.el-textarea__inner:focus) {
  background-color: #ffffff;
  box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.1) inset !important;
}
</style>

