import axios, { type AxiosInstance, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'

// 创建axios实例
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 添加认证token
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    const authStore = useAuthStore()

    if (error.response) {
      const { status, data } = error.response

      // 提取后端返回的错误消息
      let errorMessage = data.detail || data.message || ''

      switch (status) {
        case 401:
          // 如果是登录接口的401错误，直接使用后端返回的消息
          if (error.config?.url?.includes('/auth/login')) {
            errorMessage = errorMessage || '用户名或密码错误'
          } else {
            // 其他接口的401错误，说明token过期
            authStore.logout()
            window.location.href = '/login'
            errorMessage = '登录已过期，请重新登录'
          }
          break
        case 403:
          errorMessage = errorMessage || '权限不足'
          break
        case 404:
          errorMessage = errorMessage || '请求的资源不存在'
          break
        case 422:
          // 表单验证错误
          if (data.detail && Array.isArray(data.detail)) {
            const errors = data.detail.map((item: any) => item.msg).join(', ')
            errorMessage = `参数错误: ${errors}`
          } else {
            errorMessage = errorMessage || '参数错误'
          }
          break
        case 500:
          errorMessage = errorMessage || '服务器内部错误'
          break
        default:
          errorMessage = errorMessage || `请求失败 (${status})`
      }

      // 将错误消息附加到error对象上，供调用方使用
      error.message = errorMessage
    } else if (error.request) {
      error.message = '网络连接失败，请检查网络设置'
    } else {
      error.message = '请求配置错误'
    }

    return Promise.reject(error)
  }
)

export default api
