<template>
  <div class="project-list">
    <div class="page-header mb-6 flex justify-between items-center">
      <p class="text-gray-500">管理和组织您的测试项目，创建新项目或查看现有项目的详细信息</p>
      <button @click="showCreateProjectDialog" class="bg-black hover:bg-gray-800 text-white px-6 py-2.5 rounded-xl font-bold shadow-lg shadow-black/20 transition-all transform hover:-translate-y-0.5 flex items-center gap-2">
        <el-icon><Plus /></el-icon>
        创建项目
      </button>
    </div>
    
    <div class="glass-card rounded-3xl p-6 mb-8">
      <!-- 搜索和筛选 -->
      <div class="search-bar mb-6">
        <div class="flex flex-col md:flex-row gap-4">
          <div class="flex-1">
            <el-input
              v-model="searchForm.search"
              placeholder="搜索项目名称或描述"
              clearable
              @clear="handleSearch"
              @keyup.enter="handleSearch"
              class="custom-input"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
          <div v-if="authStore.isAdmin" class="w-full md:w-48">
            <el-select v-model="searchForm.owner_id" placeholder="项目所有者" clearable @change="handleSearch" class="w-full">
              <el-option
                v-for="user in userList"
                :key="user.id"
                :label="user.username"
                :value="user.id"
              />
            </el-select>
          </div>
          <button @click="handleSearch" class="bg-black hover:bg-gray-800 text-white px-6 py-2 rounded-xl font-bold transition-colors flex items-center justify-center gap-2">
            <el-icon><Search /></el-icon>
            搜索
          </button>
          
          <div class="flex bg-gray-100 p-1 rounded-xl">
            <button 
              @click="viewMode = 'grid'; handleViewModeChange()"
              class="px-3 py-1.5 rounded-lg transition-all flex items-center justify-center"
              :class="viewMode === 'grid' ? 'bg-white shadow-sm text-black' : 'text-gray-500 hover:text-gray-700'"
            >
              <el-icon><Grid /></el-icon>
            </button>
            <button 
              @click="viewMode = 'list'; handleViewModeChange()"
              class="px-3 py-1.5 rounded-lg transition-all flex items-center justify-center"
              :class="viewMode === 'list' ? 'bg-white shadow-sm text-black' : 'text-gray-500 hover:text-gray-700'"
            >
              <el-icon><List /></el-icon>
            </button>
          </div>
        </div>
      </div>

      <div v-if="loading" class="py-12">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="projectList.length === 0" class="text-center py-16">
        <el-empty description="暂无项目" :image-size="120">
          <button @click="showCreateProjectDialog" class="mt-4 px-6 py-2 bg-black text-white rounded-xl text-sm font-bold hover:bg-gray-800 transition-colors">
            创建第一个项目
          </button>
        </el-empty>
      </div>

      <div v-else>
        <!-- 网格视图 -->
        <div v-if="viewMode === 'grid'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="project in projectList"
            :key="project.id"
            class="group bg-white/50 hover:bg-white/80 border border-transparent hover:border-gray-200 rounded-2xl p-6 cursor-pointer transition-all duration-300 hover:-translate-y-1 hover:shadow-lg"
            @click="$router.push(`/projects/${project.id}`)"
          >
            <div class="flex justify-between items-start mb-4">
              <h3 class="text-lg font-bold text-gray-900 group-hover:text-black line-clamp-1">{{ project.name }}</h3>
              <el-dropdown @command="handleCommand" trigger="click">
                <button class="p-1 rounded-full hover:bg-gray-200 text-gray-400 hover:text-gray-600 transition-colors" @click.stop>
                  <el-icon><MoreFilled /></el-icon>
                </button>
                <template #dropdown>
                  <el-dropdown-menu class="!rounded-xl !border-0 !shadow-xl">
                    <el-dropdown-item :command="`edit-${project.id}`" class="!py-2 !px-4">编辑</el-dropdown-item>
                    <el-dropdown-item :command="`delete-${project.id}`" divided class="!text-red-500 !py-2 !px-4">删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
            <p class="text-sm text-gray-500 mb-6 line-clamp-2 h-10">{{ project.description || '暂无描述' }}</p>
            <div class="flex justify-between items-center text-xs text-gray-400 font-medium border-t border-gray-100 pt-4">
              <span class="bg-gray-100 px-2 py-1 rounded-md text-gray-600">{{ getOwnerName(project.owner_id) }}</span>
              <span class="font-mono">{{ formatTime(project.updated_at) }}</span>
            </div>
          </div>
        </div>

        <!-- 列表视图 -->
        <div v-else class="overflow-hidden rounded-2xl border border-gray-100">
          <el-table
            :data="projectList"
            :style="{ width: '100%' }"
            @row-click="handleRowClick"
            :header-cell-style="{ background: 'transparent', color: '#9ca3af', fontWeight: '700', textTransform: 'uppercase', fontSize: '12px', borderBottom: '1px solid rgba(229, 231, 235, 0.5)' }"
            :row-style="{ background: 'transparent' }"
          >
            <el-table-column prop="name" label="项目名称" min-width="200">
              <template #default="{ row }">
                <span class="font-bold text-gray-900">{{ row.name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="项目描述" min-width="300">
              <template #default="{ row }">
                <span class="text-gray-500">{{ row.description || '暂无描述' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="owner_id" label="所有者" width="120">
              <template #default="{ row }">
                <span class="bg-gray-100 px-2 py-1 rounded-md text-xs font-bold text-gray-600">{{ getOwnerName(row.owner_id) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="updated_at" label="更新时间" width="180">
              <template #default="{ row }">
                <span class="text-gray-400 font-mono text-xs">{{ formatTime(row.updated_at) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <div class="flex gap-2">
                  <button @click.stop="editProject(row)" class="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-xs font-bold transition-colors">
                    编辑
                  </button>
                  <button @click.stop="deleteProject(row)" class="px-3 py-1 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg text-xs font-bold transition-colors">
                    删除
                  </button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 分页 -->
        <div class="mt-6 flex justify-end">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
            background
          />
        </div>
      </div>
    </div>
    
    <!-- 创建/编辑项目对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      @close="resetForm"
      class="!rounded-3xl"
    >
      <el-form
        ref="formRef"
        :model="projectForm"
        :rules="formRules"
        label-width="80px"
        class="mt-4"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="projectForm.name" placeholder="请输入项目名称" class="custom-input" />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="projectForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入项目描述（可选）"
            class="custom-input"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="flex justify-end gap-3">
          <button @click="dialogVisible = false" class="px-5 py-2 rounded-xl text-gray-600 font-bold hover:bg-gray-100 transition-colors">取消</button>
          <button @click="handleSubmit" :disabled="submitting" class="px-5 py-2 bg-black text-white rounded-xl font-bold hover:bg-gray-800 transition-colors shadow-lg shadow-black/20">
            {{ isEdit ? '更新' : '创建' }}
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search, Grid, List, MoreFilled } from '@element-plus/icons-vue'
import { projectApi, type Project, type ProjectListParams } from '@/api/project'
import { authApi, type User } from '@/api/auth'
import dayjs from 'dayjs'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()
const authStore = useAuthStore()

// 数据状态
const loading = ref(false)
const projectList = ref<Project[]>([])
const userList = ref<User[]>([])

// 搜索表单
const searchForm = reactive<ProjectListParams>({
  search: '',
  owner_id: undefined
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 视图模式
const viewMode = ref<'grid' | 'list'>('grid')

// 对话框状态
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)

// 表单引用
const formRef = ref<FormInstance>()

// 项目表单
const projectForm = reactive({
  id: 0,
  name: '',
  description: ''
})

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 1, max: 100, message: '项目名称长度在1-100个字符', trigger: 'blur' }
  ]
}

// 对话框标题
const dialogTitle = computed(() => isEdit.value ? '编辑项目' : '创建项目')

// 格式化时间
const formatTime = (time: string) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

// 获取所有者名称
const getOwnerName = (ownerId: number) => {
  const user = userList.value.find(u => u.id === ownerId)
  return user ? user.username : '未知用户'
}

// 加载项目列表
const loadProjectList = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.size,
      limit: pagination.size,
      ...searchForm
    }

    // 根据用户角色选择不同的API
    const response = authStore.user?.role === 'admin'
      ? await projectApi.getAllProjectsAdmin(params)
      : await projectApi.getProjectList(params)
    projectList.value = response.projects
    pagination.total = response.total
  } catch (error: any) {
    console.error('加载项目列表失败:', error)
    ElMessage.error(error.response?.data?.detail || '加载项目列表失败')
  } finally {
    loading.value = false
  }
}

// 加载用户列表（管理员用）
const loadUserList = async () => {
  if (authStore.isAdmin) {
    try {
      const response = await authApi.getUserList({ limit: 1000 })
      userList.value = response.users
    } catch (error) {
      console.error('加载用户列表失败:', error)
    }
  }
}

// 搜索处理
const handleSearch = () => {
  pagination.page = 1
  loadProjectList()
}

// 分页处理
const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.page = 1
  loadProjectList()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadProjectList()
}

// 视图模式切换
const handleViewModeChange = () => {
  // 可以保存到本地存储
  localStorage.setItem('projectViewMode', viewMode.value)
}

// 表格行点击
const handleRowClick = (row: Project) => {
  router.push(`/projects/${row.id}`)
}

// 显示创建对话框
const showCreateProjectDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
  resetForm()
}

// 编辑项目
const editProject = (project: Project) => {
  isEdit.value = true
  dialogVisible.value = true

  // 填充表单数据
  projectForm.id = project.id
  projectForm.name = project.name
  projectForm.description = project.description || ''
}

// 删除项目
const deleteProject = async (project: Project) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目 "${project.name}" 吗？此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: '!bg-black !border-black',
      }
    )

    await projectApi.deleteProject(project.id)
    ElMessage.success('项目删除成功')
    loadProjectList()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除项目失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 处理命令
const handleCommand = async (command: string) => {
  const [action, id] = command.split('-')
  const projectId = parseInt(id)
  const project = projectList.value.find(p => p.id === projectId)

  if (!project) return

  if (action === 'edit') {
    editProject(project)
  } else if (action === 'delete') {
    deleteProject(project)
  }
}

// 重置表单
const resetForm = () => {
  projectForm.id = 0
  projectForm.name = ''
  projectForm.description = ''

  formRef.value?.resetFields()
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    if (isEdit.value) {
      // 更新项目
      const updateData = {
        name: projectForm.name,
        description: projectForm.description
      }
      await projectApi.updateProject(projectForm.id, updateData)
      ElMessage.success('项目更新成功')
    } else {
      // 创建项目
      const createData = {
        name: projectForm.name,
        description: projectForm.description
      }
      // 根据用户角色选择不同的API
      if (authStore.user?.role === 'admin') {
        await projectApi.createProjectAdmin(createData)
      } else {
        await projectApi.createProject(createData)
      }
      ElMessage.success('项目创建成功')
    }

    dialogVisible.value = false
    loadProjectList()
  } catch (error: any) {
    console.error('操作失败:', error)
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

// 处理创建（兼容旧的按钮）
const handleCreate = () => {
  showCreateProjectDialog()
}

// 初始化
onMounted(async () => {
  // 恢复视图模式
  const savedViewMode = localStorage.getItem('projectViewMode')
  if (savedViewMode === 'list' || savedViewMode === 'grid') {
    viewMode.value = savedViewMode
  }

  await loadUserList()
  await loadProjectList()

  // 检查是否有编辑查询参数
  const editId = route.query.edit
  if (editId) {
    const projectId = parseInt(editId as string)
    const project = projectList.value.find(p => p.id === projectId)
    if (project) {
      editProject(project)
    }
    // 清除查询参数
    router.replace({ path: '/projects' })
  }
})
</script>

<style scoped>
:deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.6) inset;
  border-radius: 0.75rem;
  padding: 8px 16px;
  transition: all 0.2s;
}
:deep(.el-input__wrapper.is-focus) {
  background-color: #ffffff;
  box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.1) inset !important;
}
</style>
