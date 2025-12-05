<template>
  <div class="profile">
    <div class="page-header">
      <h1>个人资料</h1>
    </div>

    <el-row :gutter="24">
      <el-col :span="8">
        <!-- 用户信息卡片 -->
        <div class="glass-card rounded-3xl p-6 user-info-card">
          <div class="card-header mb-6 pb-4 border-b border-gray-200">
            <span class="font-bold text-lg">基本信息</span>
          </div>

          <div class="user-avatar">
            <el-avatar :size="80" class="bg-gradient-to-br from-gray-700 to-black text-white font-bold text-3xl">
              {{ authStore.user?.username?.charAt(0).toUpperCase() }}
            </el-avatar>
          </div>

          <div class="user-details">
            <h3 class="text-xl font-bold text-gray-900 mt-4 mb-2">{{ authStore.user?.username }}</h3>
            <p class="user-role mb-4">
              <span class="px-3 py-1 rounded-lg text-xs font-bold" :class="authStore.user?.role === 'admin' ? 'bg-black text-white' : 'bg-gray-100 text-gray-600'">
                {{ authStore.user?.role === 'admin' ? '管理员' : '普通用户' }}
              </span>
            </p>
            <p class="user-email text-gray-600 mb-2">{{ authStore.user?.email }}</p>
            <p class="user-status mb-2">
              <span class="px-2 py-1 rounded-lg text-xs font-bold" :class="authStore.user?.is_active ? 'bg-green-100 text-green-700' : 'bg-red-50 text-red-600'">
                {{ authStore.user?.is_active ? '激活' : '禁用' }}
              </span>
            </p>
            <p class="join-date text-xs text-gray-400">
              加入时间：{{ formatDate(authStore.user?.created_at) }}
            </p>
          </div>
        </div>
      </el-col>

      <el-col :span="16">
        <!-- 编辑资料表单 -->
        <div class="glass-card rounded-3xl p-6">
          <div class="card-header mb-6 pb-4 border-b border-gray-200">
            <span class="font-bold text-lg">编辑资料</span>
          </div>

          <el-form
            ref="profileFormRef"
            :model="profileForm"
            :rules="profileRules"
            label-width="100px"
            class="profile-form"
            label-position="left"
          >
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="profileForm.username"
                placeholder="请输入用户名"
                :disabled="updating"
                class="custom-input"
              />
            </el-form-item>

            <el-form-item label="邮箱" prop="email">
              <el-input
                v-model="profileForm.email"
                placeholder="请输入邮箱"
                :disabled="updating"
                class="custom-input"
              />
            </el-form-item>

            <el-form-item>
              <button
                @click="updateProfile"
                :disabled="updating"
                class="bg-black hover:bg-gray-800 text-white px-6 py-2 rounded-xl font-bold shadow-lg shadow-black/20 transition-all transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {{ updating ? '保存中...' : '保存修改' }}
              </button>
              <button 
                @click="resetProfileForm"
                class="ml-3 px-6 py-2 rounded-xl text-gray-600 font-bold hover:bg-gray-100 transition-colors"
              >
                重置
              </button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 修改密码表单 -->
        <div class="glass-card rounded-3xl p-6 mt-6">
          <div class="card-header mb-6 pb-4 border-b border-gray-200">
            <span class="font-bold text-lg">修改密码</span>
          </div>

          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="100px"
            class="password-form"
            label-position="left"
          >
            <el-form-item label="当前密码" prop="current_password">
              <el-input
                v-model="passwordForm.current_password"
                type="password"
                placeholder="请输入当前密码"
                show-password
                :disabled="changingPassword"
                class="custom-input"
              />
            </el-form-item>

            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                placeholder="请输入新密码"
                show-password
                :disabled="changingPassword"
                class="custom-input"
              />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirm_password">
              <el-input
                v-model="passwordForm.confirm_password"
                type="password"
                placeholder="请再次输入新密码"
                show-password
                :disabled="changingPassword"
                class="custom-input"
              />
            </el-form-item>

            <el-form-item>
              <button
                @click="changePassword"
                :disabled="changingPassword"
                class="bg-black hover:bg-gray-800 text-white px-6 py-2 rounded-xl font-bold shadow-lg shadow-black/20 transition-all transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {{ changingPassword ? '修改中...' : '修改密码' }}
              </button>
              <button 
                @click="resetPasswordForm"
                class="ml-3 px-6 py-2 rounded-xl text-gray-600 font-bold hover:bg-gray-100 transition-colors"
              >
                重置
              </button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import dayjs from 'dayjs'

const authStore = useAuthStore()

// 表单引用
const profileFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()

// 加载状态
const updating = ref(false)
const changingPassword = ref(false)

// 个人资料表单
const profileForm = reactive({
  username: '',
  email: ''
})

// 密码修改表单
const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

// 个人资料表单验证规则
const profileRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email' as const, message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

// 密码修改表单验证规则
const passwordRules = {
  current_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度在 6 到 100 个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string, callback: Function) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 格式化日期
const formatDate = (date?: string) => {
  if (!date) return ''
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

// 初始化个人资料表单
const initProfileForm = () => {
  if (authStore.user) {
    profileForm.username = authStore.user.username
    profileForm.email = authStore.user.email
  }
}

// 重置个人资料表单
const resetProfileForm = () => {
  initProfileForm()
  profileFormRef.value?.clearValidate()
}

// 重置密码表单
const resetPasswordForm = () => {
  passwordForm.current_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''
  passwordFormRef.value?.resetFields()
}

// 更新个人资料
const updateProfile = async () => {
  if (!profileFormRef.value) return

  try {
    await profileFormRef.value.validate()
    updating.value = true

    await authApi.updateCurrentUser({
      username: profileForm.username,
      email: profileForm.email
    })

    // 更新本地用户信息
    await authStore.initUser()

    ElMessage.success('个人资料更新成功')
  } catch (error: any) {
    console.error('更新个人资料失败:', error)
    ElMessage.error(error.response?.data?.detail || '更新失败')
  } finally {
    updating.value = false
  }
}

// 修改密码
const changePassword = async () => {
  if (!passwordFormRef.value) return

  try {
    await passwordFormRef.value.validate()
    changingPassword.value = true

    await authApi.changePassword({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password
    })

    ElMessage.success('密码修改成功')
    resetPasswordForm()
  } catch (error: any) {
    console.error('修改密码失败:', error)
    ElMessage.error(error.response?.data?.detail || '修改失败')
  } finally {
    changingPassword.value = false
  }
}

// 初始化
onMounted(() => {
  initProfileForm()
})
</script>

<style scoped>
.profile {
  padding: 0;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.user-info-card {
  text-align: center;
}

.user-avatar {
  margin-bottom: 16px;
}

.user-details h3 {
  margin: 16px 0 8px 0;
  font-size: 20px;
  color: #303133;
}

.user-details p {
  margin: 8px 0;
  color: #606266;
}

.user-role {
  margin-bottom: 16px;
}

.profile-form,
.password-form {
  max-width: 500px;
}

.card-header {
  font-weight: 600;
}
</style>
