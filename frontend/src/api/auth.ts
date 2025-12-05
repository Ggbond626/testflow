import api from './index'

// 用户相关接口类型定义
export interface User {
  id: number
  username: string
  email: string
  role: 'admin' | 'user'
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  role?: 'admin' | 'user'
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface PasswordUpdateRequest {
  current_password: string
  new_password: string
}

export interface UserUpdateRequest {
  username?: string
  email?: string
  role?: 'admin' | 'user'
  is_active?: boolean
}

export interface UserListParams {
  skip?: number
  limit?: number
  role?: 'admin' | 'user'
  is_active?: boolean
  search?: string
}

export interface UserListResponse {
  users: User[]
  total: number
  skip: number
  limit: number
}

// 认证API
export const authApi = {
  // 用户登录
  login: (data: LoginRequest): Promise<LoginResponse> => {
    return api.post('/api/auth/login', data)
  },

  // 用户注册
  register: (data: RegisterRequest): Promise<User> => {
    return api.post('/api/auth/register', data)
  },

  // 刷新令牌
  refreshToken: (data: RefreshTokenRequest): Promise<{ access_token: string; token_type: string }> => {
    return api.post('/api/auth/refresh', data)
  },

  // 获取当前用户信息
  getCurrentUser: (): Promise<User> => {
    return api.get('/api/auth/me')
  },

  // 更新当前用户信息
  updateCurrentUser: (data: UserUpdateRequest): Promise<User> => {
    return api.put('/api/auth/me', data)
  },

  // 修改密码
  changePassword: (data: PasswordUpdateRequest): Promise<{ message: string }> => {
    return api.put('/api/auth/me/password', data)
  },

  // 用户登出
  logout: (): Promise<{ message: string }> => {
    return api.post('/api/auth/logout')
  },

  // 获取用户列表（管理员专用）
  getUserList: (params?: UserListParams): Promise<UserListResponse> => {
    return api.get('/api/auth/users', { params })
  },

  // 创建用户（管理员专用）
  createUser: (data: RegisterRequest): Promise<User> => {
    return api.post('/api/auth/users', data)
  },

  // 获取用户详情（管理员专用）
  getUser: (userId: number): Promise<User> => {
    return api.get(`/api/auth/users/${userId}`)
  },

  // 更新用户信息（管理员专用）
  updateUser: (userId: number, data: UserUpdateRequest): Promise<User> => {
    return api.put(`/api/auth/users/${userId}`, data)
  },

  // 删除用户（管理员专用）
  deleteUser: (userId: number): Promise<{ message: string }> => {
    return api.delete(`/api/auth/users/${userId}`)
  },

  // 更新用户状态（管理员专用）
  updateUserStatus: (userId: number, isActive: boolean): Promise<{ message: string }> => {
    return api.put(`/api/auth/users/${userId}/status`, { is_active: isActive })
  },

  // 更新用户角色（管理员专用）
  updateUserRole: (userId: number, role: 'admin' | 'user'): Promise<{ message: string }> => {
    return api.put(`/api/auth/users/${userId}/role`, { role })
  }
}
