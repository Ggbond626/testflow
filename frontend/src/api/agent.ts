/**
 * AI智能体相关API接口
 */
import request from './index'

export interface RequirementAnalysisRequest {
  requirement_content: string
  project_context?: string
  agent_id?: number
  image_paths?: string[]  // 图片文件路径列表（用于多模态分析）
}

export interface TestPointGenerationRequest {
  /** 需求点列表 */
  requirement_points: any[]
  /** 指定智能体ID（可选，不指定则使用默认智能体） */
  agent_id?: number
  // 注意：test_types 和 coverage_requirements 已移除
  // 测试分类和设计方法由后端从系统设置自动加载
}

export interface TestCaseDesignRequest {
  test_points: any[]
  test_environment?: string
  test_data_requirements?: string
  agent_id?: number
}

export interface TestCaseOptimizationRequest {
  original_test_cases: any[]
  review_feedback?: any[]
  optimization_requirements?: string
  agent_id?: number
}

export interface AgentTaskResponse {
  success: boolean
  data?: any
  error?: string
  task_id?: number
}

export interface AsyncTaskResponse {
  task_id: string
  status: string
  message: string
}

export interface AsyncTaskStatusResponse {
  task_id: string
  task_type: string
  status: string
  progress: number
  total_batches: number
  completed_batches: number
  result?: any
  error?: string
}

export interface AgentListResponse {
  agents: any[]
  total: number
}

export interface TaskLogResponse {
  logs: any[]
  total: number
}

// AI调用超时时间（5分钟）
const AI_TIMEOUT = 300000

export const agentApi = {
  /**
   * 需求分析
   */
  analyzeRequirements(data: RequirementAnalysisRequest): Promise<AgentTaskResponse> {
    return request.post('/api/agents/requirement-analysis', data, { timeout: AI_TIMEOUT })
  },

  /**
   * 生成测试点（同步模式）
   */
  generateTestPoints(data: TestPointGenerationRequest): Promise<AgentTaskResponse> {
    return request.post('/api/agents/test-point-generation', data, { timeout: AI_TIMEOUT })
  },

  /**
   * 异步生成测试点（适用于大量需求点）
   */
  generateTestPointsAsync(data: TestPointGenerationRequest): Promise<AsyncTaskResponse> {
    return request.post('/api/agents/test-point-generation/async', data)
  },

  /**
   * 获取异步任务状态
   */
  getTaskStatus(taskId: string): Promise<AsyncTaskStatusResponse> {
    return request.get(`/api/agents/tasks/${taskId}/status`)
  },

  /**
   * 取消异步任务
   */
  cancelTask(taskId: string): Promise<{ success: boolean; message: string }> {
    return request.post(`/api/agents/tasks/${taskId}/cancel`)
  },

  /**
   * 设计测试用例（异步模式，支持进度轮询和自动优化）
   */
  designTestCasesAsync(data: {
    test_points: any[]
    module_id: number
    clear_existing?: boolean
    agent_id?: number
  }): Promise<AsyncTaskResponse> {
    return request.post('/api/agents/test-case-design/async', data)
  },

  /**
   * 优化测试用例
   */
  optimizeTestCases(data: TestCaseOptimizationRequest): Promise<AgentTaskResponse> {
    return request.post('/api/agents/test-case-optimization', data, { timeout: AI_TIMEOUT })
  },

  /**
   * 批量优化测试用例（异步模式）
   */
  optimizeTestCasesBatch(data: {
    test_cases: any[]
    module_id: number
    review_feedback?: any[]
    optimization_requirements?: string
    auto_save?: boolean
    agent_id?: number
  }): Promise<AsyncTaskResponse> {
    return request.post('/api/agents/test-case-optimization/batch', data)
  },

  /**
   * 获取智能体列表
   */
  getAgentList(): Promise<AgentListResponse> {
    return request.get('/api/agents/list')
  },

  /**
   * 获取任务执行日志
   */
  getTaskLogs(params?: { agent_id?: number; limit?: number }): Promise<TaskLogResponse> {
    return request.get('/api/agents/task-logs', { params })
  },

  /**
   * 获取智能体类型列表
   */
  getAgentTypes(): Promise<{ agent_types: any[] }> {
    return request.get('/api/agents/types')
  },

  /**
   * 获取测试类型列表（从系统设置加载启用的测试分类）
   */
  getTestTypes(): Promise<{ test_types: any[] }> {
    return request.get('/api/agents/test-types')
  },

  /**
   * 获取测试设计方法列表（从系统设置加载启用的设计方法）
   */
  getDesignMethods(): Promise<{ design_methods: any[] }> {
    return request.get('/api/agents/design-methods')
  },

  /**
   * 获取测试类别列表（从系统设置加载启用的测试分类）
   */
  getTestCategories(): Promise<{ test_categories: any[] }> {
    return request.get('/api/agents/test-types')
      .then(response => ({
        test_categories: response.test_types.map((t: any) => ({
          code: t.value,
          name: t.label
        }))
      }))
  }
}

export default agentApi
