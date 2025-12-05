import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, type User, type LoginRequest, type RegisterRequest } from '@/api/auth'
import { ElMessage } from 'element-plus'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const user = ref<User | null>(null)
  const loading = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  // 初始化用户信息
  const initUser = async () => {
    if (!token.value) return

    try {
      const userData = await authApi.getCurrentUser()
      user.value = userData
    } catch (error) {
      // 如果获取用户信息失败，清除token
      logout()
    }
  }

  // 登录
  const login = async (loginData: LoginRequest) => {
    loading.value = true
    try {
      const response = await authApi.login(loginData)
      
      // 保存token和用户信息
      token.value = response.access_token
      refreshToken.value = response.refresh_token
      user.value = response.user
      
      // 保存到localStorage
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)
      
      ElMessage.success('登录成功')
      
      // 跳转到首页
      router.push('/')
      
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  // 注册
  const register = async (registerData: RegisterRequest) => {
    loading.value = true
    try {
      const userData = await authApi.register(registerData)
      ElMessage.success('注册成功，请登录')
      return userData
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  // 登出
  const logout = async () => {
    try {
      if (token.value) {
        await authApi.logout()
      }
    } catch (error) {
      // 忽略登出接口错误
    } finally {
      // 清除本地状态
      token.value = null
      refreshToken.value = null
      user.value = null
      
      // 清除localStorage
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      
      // 跳转到登录页
      router.push('/login')
    }
  }

  // 刷新token
  const refreshAccessToken = async () => {
    if (!refreshToken.value) {
      logout()
      return false
    }

    try {
      const response = await authApi.refreshToken({
        refresh_token: refreshToken.value
      })
      
      token.value = response.access_token
      localStorage.setItem('access_token', response.access_token)
      
      return true
    } catch (error) {
      logout()
      return false
    }
  }

  // 更新用户信息
  const updateUserInfo = async (updateData: { username?: string; email?: string }) => {
    try {
      const updatedUser = await authApi.updateCurrentUser(updateData)
      user.value = updatedUser
      ElMessage.success('用户信息更新成功')
      return updatedUser
    } catch (error) {
      throw error
    }
  }

  // 修改密码
  const changePassword = async (passwordData: { current_password: string; new_password: string }) => {
    try {
      await authApi.changePassword(passwordData)
      ElMessage.success('密码修改成功')
    } catch (error) {
      throw error
    }
  }

  return {
    // 状态
    token,
    refreshToken,
    user,
    loading,
    
    // 计算属性
    isAuthenticated,
    isAdmin,
    
    // 方法
    initUser,
    login,
    register,
    logout,
    refreshAccessToken,
    updateUserInfo,
    changePassword
  }
})
