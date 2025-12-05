<template>
  <div class="member-list">
    <!-- 操作栏 -->
    <div class="mb-6 flex justify-between items-center">
      <h3 class="text-lg font-bold text-gray-900">项目成员</h3>
      <button
        v-if="canEdit"
        @click="showAddDialog"
        class="bg-black hover:bg-gray-800 text-white px-6 py-2 rounded-xl font-bold shadow-lg shadow-black/20 transition-all transform hover:-translate-y-0.5 flex items-center gap-2"
      >
        <el-icon><Plus /></el-icon>
        添加成员
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="py-12">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 空状态 -->
    <div v-else-if="members.length === 0" class="text-center py-16">
      <el-empty description="暂无成员" :image-size="120">
        <button
          v-if="canEdit"
          @click="showAddDialog"
          class="mt-4 px-6 py-2 bg-black text-white rounded-xl text-sm font-bold hover:bg-gray-800 transition-colors"
        >
          添加第一个成员
        </button>
      </el-empty>
    </div>

    <!-- 成员列表 -->
    <div v-else class="bg-white/50 rounded-2xl border border-gray-100 overflow-hidden">
      <div
        v-for="member in members"
        :key="member.id"
        class="flex items-center justify-between p-4 border-b border-gray-100 last:border-b-0 hover:bg-white/80 transition-colors"
      >
        <div class="flex items-center gap-4">
          <div class="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
            <el-icon :size="20" class="text-gray-600"><User /></el-icon>
          </div>
          <div>
            <div class="font-bold text-gray-900">{{ member.user.username }}</div>
            <div class="text-sm text-gray-500">{{ member.user.email }}</div>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <span class="w-16 text-center px-3 py-1 rounded-lg text-xs font-bold" :class="getRoleClass(member.role)">
            {{ getRoleLabel(member.role) }}
          </span>
          <span class="w-24 text-xs text-gray-400">
            {{ formatDate(member.joined_at) }}
          </span>
          <div class="w-12">
            <button
              v-if="canEdit && member.role !== 'owner'"
              @click="removeMember(member)"
              class="text-red-500 hover:text-red-700 px-3 py-1 rounded-lg text-xs font-bold hover:bg-red-50 transition-colors"
            >
              移除
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加成员对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="添加成员"
      width="500px"
      align-center
      class="member-dialog"
    >
      <el-form label-width="80px">
        <el-form-item label="选择用户">
          <el-select v-model="selectedUserId" placeholder="请选择用户" class="w-full" filterable>
            <el-option
              v-for="user in availableUsers"
              :key="user.id"
              :label="`${user.username} (${user.email})`"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="selectedRole" class="w-full">
            <el-option label="成员" value="member" />
            <el-option label="查看者" value="viewer" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="flex justify-end gap-3">
          <button @click="dialogVisible = false" class="px-5 py-2 rounded-xl text-gray-600 font-bold hover:bg-gray-100 transition-colors">取消</button>
          <button @click="handleAdd" :disabled="!selectedUserId" class="px-5 py-2 bg-black text-white rounded-xl font-bold hover:bg-gray-800 transition-colors shadow-lg shadow-black/20">
            添加
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, User } from '@element-plus/icons-vue'
import { projectApi, type ProjectMember } from '@/api/project'
import { authApi, type User as UserType } from '@/api/auth'
import dayjs from 'dayjs'

const props = defineProps<{
  projectId: number
  canEdit: boolean
}>()

// 数据状态
const members = ref<ProjectMember[]>([])
const allUsers = ref<UserType[]>([])
const loading = ref(false)

// 对话框状态
const dialogVisible = ref(false)
const selectedUserId = ref<number | null>(null)
const selectedRole = ref<'member' | 'viewer'>('member')

// 可用用户（排除已是成员的）
const availableUsers = computed(() => {
  const memberUserIds = members.value.map(m => m.user_id)
  return allUsers.value.filter(u => !memberUserIds.includes(u.id))
})

// 角色标签
const getRoleLabel = (role: string) => {
  const labels: Record<string, string> = {
    owner: '所有者',
    member: '成员',
    viewer: '查看者'
  }
  return labels[role] || role
}

// 角色样式
const getRoleClass = (role: string) => {
  const classes: Record<string, string> = {
    owner: 'bg-black text-white',
    member: 'bg-blue-100 text-blue-700',
    viewer: 'bg-gray-100 text-gray-600'
  }
  return classes[role] || 'bg-gray-100 text-gray-600'
}

// 格式化日期
const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD')
}

// 加载成员列表
const loadMembers = async () => {
  loading.value = true
  try {
    members.value = await projectApi.getProjectMembers(props.projectId)
  } catch (error: any) {
    console.error('加载成员列表失败:', error)
    ElMessage.error('加载成员列表失败')
  } finally {
    loading.value = false
  }
}

// 加载所有用户
const loadAllUsers = async () => {
  try {
    const response = await authApi.getUserList({ limit: 1000 })
    allUsers.value = response.users
  } catch (error: any) {
    console.error('加载用户列表失败:', error)
  }
}

// 显示添加对话框
const showAddDialog = () => {
  selectedUserId.value = null
  selectedRole.value = 'member'
  dialogVisible.value = true
}

// 添加成员
const handleAdd = async () => {
  if (!selectedUserId.value) return

  try {
    await projectApi.addProjectMember(props.projectId, {
      user_id: selectedUserId.value,
      role: selectedRole.value
    })
    ElMessage.success('成员添加成功')
    dialogVisible.value = false
    loadMembers()
  } catch (error: any) {
    console.error('添加成员失败:', error)
    ElMessage.error(error.response?.data?.detail || '添加成员失败')
  }
}

// 移除成员
const removeMember = async (member: ProjectMember) => {
  try {
    await ElMessageBox.confirm(
      `确定要移除成员 "${member.user.username}" 吗？`,
      '确认移除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: '!bg-black !border-black'
      }
    )

    await projectApi.removeProjectMember(props.projectId, member.user_id)
    ElMessage.success('成员移除成功')
    loadMembers()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('移除成员失败:', error)
      ElMessage.error(error.response?.data?.detail || '移除失败')
    }
  }
}

// 初始化
onMounted(() => {
  loadMembers()
  loadAllUsers()
})
</script>

<style scoped>
/* 对话框样式优化 */
:deep(.el-dialog) {
  border-radius: 1.5rem !important;
}
</style>

