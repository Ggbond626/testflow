<template>
  <div class="min-h-screen flex items-center justify-center p-4">
    <div class="glass-card w-full max-w-md p-8 rounded-3xl animate-fade-in">
      <div class="text-center mb-8">
        <div class="w-16 h-16 mx-auto mb-6 shadow-lg shadow-black/20 rounded-2xl overflow-hidden">
          <img src="@/assets/logo.svg" alt="TestFlow Logo" class="w-full h-full" />
        </div>
        <h2 class="text-2xl font-bold text-gray-900 tracking-tight">创建新账号</h2>
        <p class="text-sm text-gray-500 mt-2">加入 TestFlow 智能测试平台</p>
      </div>
      
      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        class="space-y-5"
        @submit.prevent="handleRegister"
      >
        <el-form-item prop="username" class="!mb-0">
          <div class="space-y-1.5 w-full">
            <label class="text-sm font-bold text-gray-700 ml-1">用户名</label>
            <el-input
              v-model="registerForm.username"
              placeholder="请输入用户名"
              size="large"
              :prefix-icon="User"
              class="custom-input w-full"
            />
          </div>
        </el-form-item>
        
        <el-form-item prop="email" class="!mb-0">
          <div class="space-y-1.5 w-full">
            <label class="text-sm font-bold text-gray-700 ml-1">邮箱地址</label>
            <el-input
              v-model="registerForm.email"
              placeholder="请输入邮箱地址"
              size="large"
              :prefix-icon="Message"
              class="custom-input w-full"
            />
          </div>
        </el-form-item>
        
        <el-form-item prop="password" class="!mb-0">
          <div class="space-y-1.5 w-full">
            <label class="text-sm font-bold text-gray-700 ml-1">密码</label>
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              :prefix-icon="Lock"
              show-password
              class="custom-input w-full"
            />
          </div>
        </el-form-item>
        
        <el-form-item prop="confirmPassword" class="!mb-0">
          <div class="space-y-1.5 w-full">
            <label class="text-sm font-bold text-gray-700 ml-1">确认密码</label>
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              size="large"
              :prefix-icon="Lock"
              show-password
              class="custom-input w-full"
              @keyup.enter="handleRegister"
            />
          </div>
        </el-form-item>
        
        <div class="pt-4 flex justify-center">
          <button
            type="button"
            class="w-2/3 bg-black hover:bg-gray-800 text-white py-3.5 rounded-xl font-bold shadow-lg shadow-black/20 transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2"
            :disabled="authStore.loading"
            @click="handleRegister"
          >
            <el-icon v-if="authStore.loading" class="is-loading"><Loading /></el-icon>
            <span>{{ authStore.loading ? '注册中...' : '立即注册' }}</span>
          </button>
        </div>
      </el-form>
      
      <div class="mt-8 text-center">
        <p class="text-sm text-gray-500">
          已有账号？
          <router-link to="/login" class="text-black font-bold hover:underline">
            立即登录
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Message, Loading } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

// 表单引用
const registerFormRef = ref<FormInstance>()

// 注册表单数据
const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 确认密码验证器
const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// 表单验证规则
const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在3-50个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度在6-100个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 处理注册
const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  try {
    await registerFormRef.value.validate()
    
    await authStore.register({
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password
    })
    
    // 注册成功后跳转到登录页
    router.push('/login')
  } catch (error) {
    if (error instanceof Error) {
      ElMessage.error(error.message)
    }
  }
}
</script>

<style scoped>
/* Custom Input Styles to override Element Plus */
:deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.6) inset;
  border-radius: 0.75rem; /* rounded-xl */
  padding: 8px 16px;
  transition: all 0.2s;
  width: 100%;
}

:deep(.el-input__wrapper.is-focus) {
  background-color: #ffffff;
  box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.1) inset !important;
}

:deep(.el-input__inner) {
  height: 28px;
  color: #374151;
  font-weight: 500;
}
</style>
