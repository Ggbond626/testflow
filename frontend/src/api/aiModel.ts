/**
 * AI模型管理相关API接口
 */
import api from './index'

export interface AIModelCreate {
  name: string
  provider?: string
  model_id: string
  base_url: string
  api_key?: string
  max_tokens?: number
  temperature?: number
  stream_support?: boolean
  is_active?: boolean
}

export interface AIModelUpdate {
  name?: string
  provider?: string
  model_id?: string
  base_url?: string
  api_key?: string
  max_tokens?: number
  temperature?: number
  stream_support?: boolean
  is_active?: boolean
}

export interface AIModelTest {
  message?: string
}

export interface AgentCreate {
  name: string
  type: string
  ai_model_id: number
  prompt_template?: string
  system_prompt?: string
  temperature?: number
  max_tokens?: number
}

export interface AgentUpdate {
  name?: string
  ai_model_id?: number
  prompt_template?: string
  system_prompt?: string
  temperature?: number
  max_tokens?: number
  is_active?: boolean
}

export interface AIModelResponse {
  id: number
  name: string
  provider: string
  model_id: string
  base_url: string
  max_tokens: number
  temperature: number
  stream_support: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AIModelTestResponse {
  success: boolean
  message: string
  response?: any
  error?: string
}

export interface AgentResponse {
  id: number
  name: string
  type: string
  type_display: string
  ai_model_name: string
  temperature: number
  max_tokens: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export const aiModelApi = {
  // AI模型管理
  /**
   * 创建AI模型
   */
  createAIModel(data: AIModelCreate): Promise<AIModelResponse> {
    return api.post('/api/ai/models', data)
  },

  /**
   * 获取AI模型详情（包含API密钥）
   */
  getAIModelDetail(id: number): Promise<AIModelResponse & { api_key: string }> {
    return api.get(`/api/ai/models/${id}`)
  },

  /**
   * 获取AI模型列表
   */
  getAIModels(params?: { skip?: number; limit?: number; is_active?: boolean }): Promise<AIModelResponse[]> {
    return api.get('/api/ai/models', { params })
  },

  /**
   * 更新AI模型
   */
  updateAIModel(id: number, data: AIModelUpdate): Promise<AIModelResponse> {
    return api.put(`/api/ai/models/${id}`, data)
  },

  /**
   * 删除AI模型
   */
  deleteAIModel(id: number): Promise<{ message: string }> {
    return api.delete(`/api/ai/models/${id}`)
  },

  /**
   * 测试AI模型
   */
  testAIModel(id: number, data: AIModelTest = {}): Promise<AIModelTestResponse> {
    return api.post(`/api/ai/models/${id}/test`, data)
  },

  // 智能体管理
  /**
   * 创建智能体
   */
  createAgent(data: AgentCreate): Promise<AgentResponse> {
    return api.post('/api/ai/agents', data)
  },

  /**
   * 获取智能体列表
   */
  getAgents(params?: { skip?: number; limit?: number }): Promise<AgentResponse[]> {
    return api.get('/api/ai/agents', { params })
  },

  /**
   * 更新智能体
   */
  updateAgent(agentId: number, data: AgentUpdate): Promise<AgentResponse> {
    return api.put(`/api/ai/agents/${agentId}`, data)
  },

  /**
   * 删除智能体
   */
  deleteAgent(agentId: number): Promise<{ message: string }> {
    return api.delete(`/api/ai/agents/${agentId}`)
  }
}

export default aiModelApi
