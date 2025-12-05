import api from './index'

// 模块状态枚举
export type ModuleStatus = 'planning' | 'in_progress' | 'completed' | 'on_hold'

// 模块优先级枚举
export type ModulePriority = 'low' | 'medium' | 'high' | 'critical'

// 模块统计信息
export interface ModuleStats {
  requirement_files_count: number
  requirement_points_count: number
  test_points_count: number
  test_cases_count: number
  test_cases_approved: number
  completion_rate: number
}

// 模块负责人
export interface ModuleAssignee {
  id: number
  user_id: number
  username: string
  role: string
  assigned_at: string
  assigned_by?: number
}

// 模块接口
export interface Module {
  id: number
  project_id: number
  name: string
  description?: string
  priority: ModulePriority
  status: ModuleStatus
  order_num: number
  created_at: string
  updated_at: string
}

// 模块详情（包含统计和负责人）
export interface ModuleDetail extends Module {
  stats: ModuleStats
  assignees: ModuleAssignee[]
}

// 模块列表响应
export interface ModuleListResponse {
  modules: ModuleDetail[]
  total: number
}

// 模块创建请求
export interface ModuleCreateRequest {
  name: string
  description?: string
  priority?: ModulePriority
  status?: ModuleStatus
}

// 模块更新请求
export interface ModuleUpdateRequest {
  name?: string
  description?: string
  priority?: ModulePriority
  status?: ModuleStatus
}

// 模块排序请求
export interface ModuleReorderRequest {
  module_orders: Array<{ id: number; order_num: number }>
}

// 模块分配请求
export interface ModuleAssignmentCreateRequest {
  user_id: number
  role?: string
}

// 项目统计信息
export interface ProjectStatsResponse {
  module_count: number
  member_count: number
  requirement_points_count: number
  test_cases_count: number
  modules_by_status: Record<string, number>
  modules_by_priority: Record<string, number>
  recent_activities: any[]
}

// 模块API
export const moduleApi = {
  // 获取项目统计信息
  getProjectStats: (projectId: number): Promise<ProjectStatsResponse> => {
    return api.get(`/api/projects/${projectId}/stats`)
  },

  // 获取模块列表
  getModules: (projectId: number, priority?: ModulePriority): Promise<ModuleListResponse> => {
    const params = priority ? { priority } : undefined
    return api.get(`/api/projects/${projectId}/modules`, { params })
  },

  // 创建模块
  createModule: (projectId: number, data: ModuleCreateRequest): Promise<ModuleDetail> => {
    return api.post(`/api/projects/${projectId}/modules`, data)
  },

  // 获取模块详情
  getModule: (projectId: number, moduleId: number): Promise<ModuleDetail> => {
    return api.get(`/api/projects/${projectId}/modules/${moduleId}`)
  },

  // 更新模块
  updateModule: (projectId: number, moduleId: number, data: ModuleUpdateRequest): Promise<ModuleDetail> => {
    return api.put(`/api/projects/${projectId}/modules/${moduleId}`, data)
  },

  // 删除模块
  deleteModule: (projectId: number, moduleId: number): Promise<void> => {
    return api.delete(`/api/projects/${projectId}/modules/${moduleId}`)
  },

  // 调整模块顺序
  reorderModules: (projectId: number, data: ModuleReorderRequest): Promise<{ success: boolean; message: string }> => {
    return api.put(`/api/projects/${projectId}/modules/reorder`, data)
  },

  // 分配模块负责人
  assignModule: (projectId: number, moduleId: number, data: ModuleAssignmentCreateRequest): Promise<ModuleAssignee> => {
    return api.post(`/api/projects/${projectId}/modules/${moduleId}/assign`, data)
  },

  // 移除模块负责人
  removeAssignment: (projectId: number, moduleId: number, userId: number): Promise<void> => {
    return api.delete(`/api/projects/${projectId}/modules/${moduleId}/assign/${userId}`)
  },

  // 获取模块负责人列表
  getModuleAssignees: (projectId: number, moduleId: number): Promise<ModuleAssignee[]> => {
    return api.get(`/api/projects/${projectId}/modules/${moduleId}/assignees`)
  }
}

