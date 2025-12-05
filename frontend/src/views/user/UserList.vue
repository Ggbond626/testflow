<template>
  <div class="user-list">
    <div class="page-header mb-6 flex justify-between items-center">
      <p class="text-gray-500">管理系统用户账户，查看用户信息、权限设置和活动状态</p>
      <button @click="showCreateDialog" class="bg-black hover:bg-gray-800 text-white px-6 py-2.5 rounded-xl font-bold shadow-lg shadow-black/20 transition-all transform hover:-translate-y-0.5 flex items-center gap-2">
        <el-icon><Plus /></el-icon>
        创建用户
      </button>
    </div>

    <div class="glass-card rounded-3xl p-6">
      <!-- 搜索和筛选 -->
      <div class="mb-6">
        <div class="flex flex-wrap gap-4">
          <div class="flex-1 min-w-[200px]">
            <el-input
              v-model="searchForm.search"
              placeholder="搜索用户名或邮箱"
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
          <div class="w-40">
            <el-select v-model="searchForm.role" placeholder="角色筛选" clearable @change="handleSearch" class="w-full">
              <el-option label="管理员" value="admin" />
              <el-option label="普通用户" value="user" />
            </el-select>
          </div>
          <div class="w-40">
            <el-select v-model="searchForm.is_active" placeholder="状态筛选" clearable @change="handleSearch" class="w-full">
              <el-option label="激活" :value="true" />
              <el-option label="禁用" :value="false" />
            </el-select>
          </div>
          <button @click="handleSearch" class="px-6 py-2 bg-gray-900 hover:bg-black text-white rounded-xl font-bold transition-colors flex items-center gap-2">
            <el-icon><Search /></el-icon>
            搜索
          </button>
        </div>
      </div>

      <!-- 用户表格 -->
      <div class="overflow-hidden rounded-2xl border border-gray-100">
        <el-table
          v-loading="loading"
          :data="userList"
          :style="{ width: '100%' }"
          @selection-change="handleSelectionChange"
          :header-cell-style="{ background: 'transparent', color: '#9ca3af', fontWeight: '700', textTransform: 'uppercase', fontSize: '12px', borderBottom: '1px solid rgba(229, 231, 235, 0.5)' }"
          :row-style="{ background: 'transparent' }"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="id" label="ID" width="80">
            <template #default="{ row }">
              <span class="font-mono text-gray-500">#{{ row.id }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="username" label="用户名" min-width="120">
            <template #default="{ row }">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-gray-700 to-black text-white flex items-center justify-center font-bold text-xs">
                  {{ row.username.charAt(0).toUpperCase() }}
                </div>
                <span class="font-bold text-gray-900">{{ row.username }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="email" label="邮箱" min-width="200">
            <template #default="{ row }">
              <span class="text-gray-600">{{ row.email }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="role" label="角色" width="120">
            <template #default="{ row }">
              <span class="px-2.5 py-1 rounded-lg text-xs font-bold" :class="row.role === 'admin' ? 'bg-black text-white' : 'bg-gray-100 text-gray-600'">
                {{ row.role === 'admin' ? '管理员' : '普通用户' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="100">
            <template #default="{ row }">
              <span class="px-2 py-1 rounded-lg text-xs font-bold" :class="row.is_active ? 'bg-green-100 text-green-700' : 'bg-red-50 text-red-600'">
                {{ row.is_active ? '激活' : '禁用' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              <span class="text-gray-500 text-sm font-mono">{{ formatDate(row.created_at) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <div class="flex gap-2">
                <button @click="showEditDialog(row)" class="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-xs font-bold transition-colors">
                  编辑
                </button>
                <button 
                  @click="toggleUserStatus(row)"
                  class="px-3 py-1.5 rounded-lg text-xs font-bold transition-colors"
                  :class="row.is_active ? 'bg-yellow-50 hover:bg-yellow-100 text-yellow-600' : 'bg-green-50 hover:bg-green-100 text-green-600'"
                >
                  {{ row.is_active ? '禁用' : '启用' }}
                </button>
                <button
                  @click="deleteUser(row)"
                  :disabled="row.id === currentUserId"
                  class="px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg text-xs font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
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

    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      @close="resetForm"
      class="!rounded-3xl"
    >
      <el-form
        ref="formRef"
        :model="userForm"
        :rules="formRules"
        label-width="80px"
        class="mt-4"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" placeholder="请输入用户名" class="custom-input" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" placeholder="请输入邮箱" class="custom-input" />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input
            v-model="userForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
            class="custom-input"
          />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" placeholder="请选择角色" class="w-full custom-select">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="isEdit" label="状态" prop="is_active">
          <el-switch
            v-model="userForm.is_active"
            active-text="激活"
            inactive-text="禁用"
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
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import type { User, UserListParams } from '@/api/auth'
import dayjs from 'dayjs'

const authStore = useAuthStore()

// 当前用户ID
const currentUserId = computed(() => authStore.user?.id)

// 数据状态
const loading = ref(false)
const userList = ref<User[]>([])
const selectedUsers = ref<User[]>([])

// 搜索表单
const searchForm = reactive<UserListParams>({
  search: '',
  role: undefined,
  is_active: undefined
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 对话框状态
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()

// 用户表单
const userForm = reactive({
  id: 0,
  username: '',
  email: '',
  password: '',
  role: 'user' as 'admin' | 'user',
  is_active: true
})

// 表单验证规则
const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email' as const, message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度在 6 到 100 个字符', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

// 对话框标题
const dialogTitle = computed(() => isEdit.value ? '编辑用户' : '创建用户')

// 格式化日期
const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

// 加载用户列表
const loadUserList = async () => {
  loading.value = true
  try {
    const params: any = {
      skip: (pagination.page - 1) * pagination.size,
      limit: pagination.size
    }

    // 只添加有值的搜索参数
    if (searchForm.search && searchForm.search.trim()) {
      params.search = searchForm.search.trim()
    }
    if (searchForm.role) {
      params.role = searchForm.role
    }
    if (searchForm.is_active !== undefined) {
      params.is_active = searchForm.is_active
    }

    const response = await authApi.getUserList(params)
    userList.value = response.users
    pagination.total = response.total
  } catch (error) {
    console.error('加载用户列表失败:', error)
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  pagination.page = 1
  loadUserList()
}

// 分页处理
const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.page = 1
  loadUserList()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadUserList()
}

// 选择处理
const handleSelectionChange = (selection: User[]) => {
  selectedUsers.value = selection
}

// 显示创建对话框
const showCreateDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
  resetForm()
}

// 显示编辑对话框
const showEditDialog = (user: User) => {
  isEdit.value = true
  dialogVisible.value = true

  // 填充表单数据
  userForm.id = user.id
  userForm.username = user.username
  userForm.email = user.email
  userForm.role = user.role
  userForm.is_active = user.is_active
  userForm.password = '' // 编辑时不显示密码
}

// 重置表单
const resetForm = () => {
  userForm.id = 0
  userForm.username = ''
  userForm.email = ''
  userForm.password = ''
  userForm.role = 'user'
  userForm.is_active = true

  formRef.value?.resetFields()
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    if (isEdit.value) {
      // 更新用户
      const updateData = {
        username: userForm.username,
        email: userForm.email,
        role: userForm.role,
        is_active: userForm.is_active
      }
      await authApi.updateUser(userForm.id, updateData)
      ElMessage.success('用户更新成功')
    } else {
      // 创建用户
      const createData = {
        username: userForm.username,
        email: userForm.email,
        password: userForm.password,
        role: userForm.role
      }
      await authApi.createUser(createData)
      ElMessage.success('用户创建成功')
    }

    dialogVisible.value = false
    loadUserList()
  } catch (error: any) {
    console.error('操作失败:', error)
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

// 切换用户状态
const toggleUserStatus = async (user: User) => {
  try {
    const action = user.is_active ? '禁用' : '启用'
    await ElMessageBox.confirm(
      `确定要${action}用户 "${user.username}" 吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: '!bg-black !border-black',
      }
    )

    await authApi.updateUserStatus(user.id, !user.is_active)
    ElMessage.success(`用户${action}成功`)
    loadUserList()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('更新用户状态失败:', error)
      ElMessage.error('操作失败')
    }
  }
}

// 删除用户
const deleteUser = async (user: User) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: '!bg-black !border-black',
      }
    )

    await authApi.deleteUser(user.id)
    ElMessage.success('用户删除成功')
    loadUserList()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 初始化
onMounted(() => {
  loadUserList()
})
</script>

<style scoped>

</style>
