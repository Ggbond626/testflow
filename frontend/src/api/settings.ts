/**
 * 系统设置API模块
 * 提供测试分类、测试设计方法和并发配置的API接口
 */
import api from './index'

// ============== Test Category Types ==============

/** 测试分类基础接口 */
export interface TestCategoryBase {
  name: string
  code: string
  description?: string | null
  is_active: boolean
  order_index: number
}

/** 测试分类创建请求 */
export interface TestCategoryCreate extends TestCategoryBase {}

/** 测试分类更新请求 */
export interface TestCategoryUpdate {
  name?: string
  code?: string
  description?: string | null
  is_active?: boolean
  order_index?: number
}

/** 测试分类响应 */
export interface TestCategoryResponse extends TestCategoryBase {
  id: number
  is_default: boolean
  created_at: string
  updated_at: string
}

// ============== Test Design Method Types ==============

/** 测试设计方法基础接口 */
export interface TestDesignMethodBase {
  name: string
  code: string
  description?: string | null
  is_active: boolean
  order_index: number
}

/** 测试设计方法创建请求 */
export interface TestDesignMethodCreate extends TestDesignMethodBase {}

/** 测试设计方法更新请求 */
export interface TestDesignMethodUpdate {
  name?: string
  code?: string
  description?: string | null
  is_active?: boolean
  order_index?: number
}

/** 测试设计方法响应 */
export interface TestDesignMethodResponse extends TestDesignMethodBase {
  id: number
  is_default: boolean
  created_at: string
  updated_at: string
}

// ============== Concurrency Config Types ==============

/** 并发配置接口 */
export interface ConcurrencyConfig {
  /** 最大并发任务数（范围：1-10） */
  max_concurrent_tasks: number
  /** 任务超时时间，单位秒（范围：30-600） */
  task_timeout: number
  /** 失败重试次数（范围：0-5） */
  retry_count: number
  /** 任务队列大小（范围：10-1000） */
  queue_size: number
}

// ============== API Response Types ==============

/** 删除操作响应 */
export interface DeleteResponse {
  message: string
}

// ============== Settings API ==============

export const settingsApi = {
  // ============== Test Categories ==============

  /**
   * 获取所有测试分类
   * @param activeOnly 是否只返回启用的分类
   */
  getTestCategories: (activeOnly: boolean = false): Promise<TestCategoryResponse[]> => {
    return api.get('/api/settings/test-categories', { params: { active_only: activeOnly } })
  },

  /**
   * 创建测试分类
   * @param data 测试分类创建数据
   */
  createTestCategory: (data: TestCategoryCreate): Promise<TestCategoryResponse> => {
    return api.post('/api/settings/test-categories', data)
  },

  /**
   * 更新测试分类
   * @param id 分类ID
   * @param data 更新数据
   */
  updateTestCategory: (id: number, data: TestCategoryUpdate): Promise<TestCategoryResponse> => {
    return api.put(`/api/settings/test-categories/${id}`, data)
  },

  /**
   * 删除测试分类（软删除）
   * @param id 分类ID
   */
  deleteTestCategory: (id: number): Promise<DeleteResponse> => {
    return api.delete(`/api/settings/test-categories/${id}`)
  },

  /**
   * 重置测试分类为默认值
   */
  resetTestCategories: (): Promise<TestCategoryResponse[]> => {
    return api.post('/api/settings/test-categories/reset')
  },

  // ============== Test Design Methods ==============

  /**
   * 获取所有测试设计方法
   * @param activeOnly 是否只返回启用的方法
   */
  getDesignMethods: (activeOnly: boolean = false): Promise<TestDesignMethodResponse[]> => {
    return api.get('/api/settings/design-methods', { params: { active_only: activeOnly } })
  },

  /**
   * 创建测试设计方法
   * @param data 测试设计方法创建数据
   */
  createDesignMethod: (data: TestDesignMethodCreate): Promise<TestDesignMethodResponse> => {
    return api.post('/api/settings/design-methods', data)
  },

  /**
   * 更新测试设计方法
   * @param id 方法ID
   * @param data 更新数据
   */
  updateDesignMethod: (id: number, data: TestDesignMethodUpdate): Promise<TestDesignMethodResponse> => {
    return api.put(`/api/settings/design-methods/${id}`, data)
  },

  /**
   * 删除测试设计方法（软删除）
   * @param id 方法ID
   */
  deleteDesignMethod: (id: number): Promise<DeleteResponse> => {
    return api.delete(`/api/settings/design-methods/${id}`)
  },

  /**
   * 重置测试设计方法为默认值
   */
  resetDesignMethods: (): Promise<TestDesignMethodResponse[]> => {
    return api.post('/api/settings/design-methods/reset')
  },

  // ============== Concurrency Config ==============

  /**
   * 获取并发配置
   */
  getConcurrencyConfig: (): Promise<ConcurrencyConfig> => {
    return api.get('/api/settings/concurrency')
  },

  /**
   * 更新并发配置
   * @param config 新的并发配置
   */
  updateConcurrencyConfig: (config: ConcurrencyConfig): Promise<ConcurrencyConfig> => {
    return api.put('/api/settings/concurrency', config)
  }
}

export default settingsApi
