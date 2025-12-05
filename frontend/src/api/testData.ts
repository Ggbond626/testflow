/**
 * 测试数据管理API
 * 用于 GenerationResultsV2.vue 查询和管理测试层级数据
 */
import api from './index'

// ========== 类型定义 ==========

export interface RequirementPoint {
  id: number
  requirement_file_id: number
  content: string
  order_index: number
  status: string
  created_by_ai: boolean
  edited_by_user: boolean
  created_at: string
  updated_at: string
}

export interface TestPoint {
  id: number
  requirement_point_id: number
  content: string
  test_type: string
  priority: string
  status: string
  created_by_ai: boolean
  edited_by_user: boolean
  created_at: string
  updated_at: string
}

export interface TestCase {
  id: number
  test_point_id: number
  title: string
  description?: string
  preconditions?: string
  test_steps?: Array<{
    step: number
    action: string
    expected: string
  }>
  expected_result?: string
  test_method: string
  test_category: string
  status: string
  created_by_ai: boolean
  edited_by_user: boolean
  created_at: string
  updated_at: string
}

export interface TestPointWithCases extends TestPoint {
  test_cases: TestCase[]
}

export interface RequirementPointWithTestPoints extends RequirementPoint {
  test_points: TestPointWithCases[]
}

export interface TestHierarchy {
  project_id: number
  file_id?: number
  requirement_points: RequirementPointWithTestPoints[]
  statistics: {
    total_requirement_points: number
    total_test_points: number
    total_test_cases: number
  }
}

// ========== API方法 ==========

export const testDataApi = {
  /**
   * 获取完整的测试层级结构
   */
  getTestHierarchy: (projectId: number, options?: { fileId?: number; moduleId?: number }): Promise<TestHierarchy> => {
    const params: Record<string, number> = {}
    if (options?.fileId) params.file_id = options.fileId
    if (options?.moduleId) params.module_id = options.moduleId
    return api.get(`/api/test-data/projects/${projectId}/test-hierarchy`, { params })
  },

  /**
   * 更新需求点
   */
  updateRequirementPoint: (pointId: number, content: string): Promise<RequirementPoint> => {
    return api.put(`/api/test-data/requirement-points/${pointId}`, { content })
  },

  /**
   * 更新测试点
   */
  updateTestPoint: (
    pointId: number,
    data: {
      content: string
      test_type?: string
      priority?: string
    }
  ): Promise<TestPoint> => {
    return api.put(`/api/test-data/test-points/${pointId}`, data)
  },

  /**
   * 更新测试用例
   */
  updateTestCase: (caseId: number, data: Partial<TestCase>): Promise<TestCase> => {
    return api.put(`/api/test-data/test-cases/${caseId}`, data)
  },

  /**
   * 删除需求点
   */
  deleteRequirementPoint: (pointId: number): Promise<void> => {
    return api.delete(`/api/test-data/requirement-points/${pointId}`)
  },

  /**
   * 删除测试点
   */
  deleteTestPoint: (pointId: number): Promise<void> => {
    return api.delete(`/api/test-data/test-points/${pointId}`)
  },

  /**
   * 删除测试用例
   */
  deleteTestCase: (caseId: number): Promise<void> => {
    return api.delete(`/api/test-data/test-cases/${caseId}`)
  }
}

// ========== 辅助函数 ==========

export function getTestTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    functional: '功能测试',
    performance: '性能测试',
    automation: '自动化测试',
    security: '安全测试',
    usability: '可用性测试'
  }
  return labels[type] || type
}

export function getPriorityLabel(priority: string): string {
  const labels: Record<string, string> = {
    high: '高',
    medium: '中',
    low: '低'
  }
  return labels[priority] || priority
}

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: '草稿',
    confirmed: '已确认',
    under_review: '审核中',
    approved: '已批准',
    rejected: '已拒绝',
    completed: '已完成'
  }
  return labels[status] || status
}

export function getTestMethodLabel(method: string): string {
  const labels: Record<string, string> = {
    black_box: '黑盒测试',
    white_box: '白盒测试',
    gray_box: '灰盒测试'
  }
  return labels[method] || method
}
