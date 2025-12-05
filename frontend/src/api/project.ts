import api from './index'
import type { User } from './auth'

// 项目相关接口类型定义
export interface Project {
  id: number
  name: string
  description?: string
  owner_id: number
  created_at: string
  updated_at: string
}

export interface ProjectDetail extends Project {
  owner: User
  members: ProjectMember[]
  member_count: number
  requirement_files_count: number
  requirement_points_count: number
  test_cases_count: number
}

export interface ProjectMember {
  id: number
  project_id: number
  user_id: number
  role: 'owner' | 'member' | 'viewer'
  joined_at: string
  user: User
}

export interface ProjectCreateRequest {
  name: string
  description?: string
}

export interface ProjectUpdateRequest {
  name?: string
  description?: string
}

export interface ProjectListParams {
  skip?: number
  limit?: number
  search?: string
  owner_id?: number
}

export interface ProjectListResponse {
  projects: Project[]
  total: number
  skip: number
  limit: number
}

export interface ProjectMemberCreateRequest {
  user_id: number
  role: 'member' | 'viewer'
}

export interface ProjectStats {
  total_projects: number
  owned_projects: number
  member_projects: number
  active_projects: number
}

// 项目统计信息（详细）
export interface ProjectStatsDetail {
  module_count: number
  member_count: number
  requirement_points_count: number
  test_cases_count: number
  modules_by_status: Record<string, number>
  modules_by_priority: Record<string, number>
  recent_activities: any[]
}

// 项目API
export const projectApi = {
  // 创建项目
  createProject: (data: ProjectCreateRequest): Promise<Project> => {
    return api.post('/api/projects', data)
  },

  // 创建项目（管理员）
  createProjectAdmin: (data: ProjectCreateRequest): Promise<Project> => {
    return api.post('/api/projects/admin', data)
  },

  // 获取项目列表
  getProjectList: (params?: ProjectListParams): Promise<ProjectListResponse> => {
    return api.get('/api/projects', { params })
  },

  // 获取所有项目列表（管理员专用）
  getAllProjectsAdmin: (params?: ProjectListParams): Promise<ProjectListResponse> => {
    return api.get('/api/projects/admin', { params })
  },

  // 获取项目详情
  getProject: (projectId: number): Promise<ProjectDetail> => {
    return api.get(`/api/projects/${projectId}`)
  },

  // 获取项目详情（管理员）
  getProjectAdmin: (projectId: number): Promise<ProjectDetail> => {
    return api.get(`/api/projects/admin/${projectId}`)
  },

  // 更新项目
  updateProject: (projectId: number, data: ProjectUpdateRequest): Promise<Project> => {
    return api.put(`/api/projects/${projectId}`, data)
  },

  // 删除项目
  deleteProject: (projectId: number): Promise<{ message: string }> => {
    return api.delete(`/api/projects/${projectId}`)
  },

  // 删除项目（管理员）
  deleteProjectAdmin: (projectId: number): Promise<{ message: string }> => {
    return api.delete(`/api/projects/admin/${projectId}`)
  },

  // 添加项目成员
  addProjectMember: (projectId: number, data: ProjectMemberCreateRequest): Promise<ProjectMember> => {
    return api.post(`/api/projects/${projectId}/members`, data)
  },

  // 添加项目成员（管理员）
  addProjectMemberAdmin: (projectId: number, data: ProjectMemberCreateRequest): Promise<ProjectMember> => {
    return api.post(`/api/projects/admin/${projectId}/members`, data)
  },

  // 获取项目成员列表
  getProjectMembers: (projectId: number): Promise<ProjectMember[]> => {
    return api.get(`/api/projects/${projectId}/members`)
  },

  // 获取项目成员列表（管理员）
  getProjectMembersAdmin: (projectId: number): Promise<ProjectMember[]> => {
    return api.get(`/api/projects/admin/${projectId}/members`)
  },

  // 移除项目成员
  removeProjectMember: (projectId: number, userId: number): Promise<{ message: string }> => {
    return api.delete(`/api/projects/${projectId}/members/${userId}`)
  },

  // 移除项目成员（管理员）
  removeProjectMemberAdmin: (projectId: number, userId: number): Promise<{ message: string }> => {
    return api.delete(`/api/projects/admin/${projectId}/members/${userId}`)
  },

  // 获取项目统计信息
  getProjectStats: (projectId: number): Promise<ProjectStatsDetail> => {
    return api.get(`/api/projects/${projectId}/stats`)
  },

  // 获取项目测试用例列表
  getProjectTestCases: (projectId: number, params?: { view_mode?: 'hierarchy' | 'flat'; keyword?: string; status?: string; priority?: string }): Promise<any[]> => {
    return api.get(`/api/projects/${projectId}/test-cases`, { params })
  },

  // 批量删除测试用例
  batchDeleteTestCases: (projectId: number, ids: number[]): Promise<{ deleted_count: number; message: string }> => {
    return api.delete(`/api/projects/${projectId}/test-cases/batch`, { data: { ids } })
  },

  // 更新单个测试用例
  updateTestCase: (projectId: number, caseId: number, data: any): Promise<{ message: string; id: number }> => {
    return api.put(`/api/projects/${projectId}/test-cases/${caseId}`, data)
  },

  // 删除单个测试用例
  deleteTestCase: (projectId: number, caseId: number): Promise<{ message: string; id: number }> => {
    return api.delete(`/api/projects/${projectId}/test-cases/${caseId}`)
  },

  // 导出测试用例（支持 excel 和 xmind 格式）
  exportTestCases: (projectId: number, ids?: number[], format: string = 'excel'): Promise<Blob> => {
    return api.post(`/api/projects/${projectId}/test-cases/export`,
      { ids, format },
      { responseType: 'blob' }
    )
  },

  // 下载导入模板
  downloadImportTemplate: (projectId: number): Promise<Blob> => {
    return api.get(`/api/projects/${projectId}/test-cases/template`, {
      responseType: 'blob'
    })
  },

  // 导入测试用例
  importTestCases: (projectId: number, formData: FormData): Promise<any> => {
    return api.post(`/api/projects/${projectId}/test-cases/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}

