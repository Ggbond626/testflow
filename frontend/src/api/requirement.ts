import api from './index'

// 需求文件相关接口
export interface RequirementFile {
  id: number
  project_id: number
  filename: string
  file_path: string
  file_size: number
  file_type: string
  uploaded_by: number
  upload_time: string
  extracted_content?: string | null
  is_extracted: boolean
  extract_error?: string | null
  uploader?: {
    id: number
    username: string
  }
}

export interface RequirementFileContent {
  id: number
  filename: string
  file_type: string
  extracted_content?: string | null
  is_extracted: boolean
  extract_error?: string | null
  requirement_points?: RequirementPoint[]
}

export interface RequirementPoint {
  id: number
  requirement_file_id: number
  content: string
  order_index: number
  status: 'draft' | 'confirmed' | 'processing' | 'completed'
  created_by_ai: boolean
  edited_by_user: boolean
  created_by: number
  updated_by?: number
  created_at: string
  updated_at: string
  creator?: {
    id: number
    username: string
  }
  updater?: {
    id: number
    username: string
  }
}

// 需求文件API
export const requirementApi = {
  // ========== 需求文件管理 ==========

  // 获取项目需求文件列表
  getFileList: (projectId: number): Promise<RequirementFile[]> => {
    return api.get(`/requirements/${projectId}/files`)
  },

  // 下载需求文件
  downloadFile: (projectId: number, fileId: number): Promise<Blob> => {
    return api.get(`/requirements/${projectId}/files/${fileId}/download`, {
      responseType: 'blob'
    })
  },

  // 重命名文件
  renameFile: (projectId: number, fileId: number, newFilename: string): Promise<RequirementFile> => {
    const formData = new FormData()
    formData.append('new_filename', newFilename)
    return api.put(`/requirements/${projectId}/files/${fileId}/rename`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 获取文件内容
  getFileContent: (projectId: number, fileId: number): Promise<RequirementFileContent> => {
    return api.get(`/requirements/${projectId}/files/${fileId}/content`)
  },

  // 删除需求文件
  deleteFile: (projectId: number, fileId: number): Promise<{ message: string }> => {
    return api.delete(`/requirements/${projectId}/files/${fileId}`)
  },

  // ========== 按模块管理需求点 ==========

  // 获取模块的需求点列表
  getModuleRequirementPoints: (projectId: number, moduleId: number): Promise<RequirementPoint[]> => {
    return api.get(`/api/projects/${projectId}/modules/${moduleId}/requirement-points`)
  },

  // 创建需求点
  createModuleRequirementPoint: (
    projectId: number,
    moduleId: number,
    data: { content: string; priority?: string }
  ): Promise<RequirementPoint> => {
    return api.post(`/api/projects/${projectId}/modules/${moduleId}/requirement-points`, null, {
      params: data
    })
  },

  // 更新需求点
  updateModuleRequirementPoint: (
    projectId: number,
    moduleId: number,
    pointId: number,
    data: { content: string; priority?: string }
  ): Promise<RequirementPoint> => {
    return api.put(`/api/projects/${projectId}/modules/${moduleId}/requirement-points/${pointId}`, null, {
      params: data
    })
  },

  // 删除需求点
  deleteModuleRequirementPoint: (projectId: number, moduleId: number, pointId: number): Promise<{ message: string }> => {
    return api.delete(`/api/projects/${projectId}/modules/${moduleId}/requirement-points/${pointId}`)
  },

  // ========== 按模块管理测试点 ==========

  // 获取模块的测试点列表（按需求点分组）
  getModuleTestPoints: (projectId: number, moduleId: number): Promise<{
    requirement_points: Array<{
      id: number
      content: string
      priority: string
      created_by_ai: boolean
      test_points: Array<{
        id: number
        content: string
        test_type: string
        priority: string
        created_by_ai: boolean
      }>
    }>
    statistics: {
      total_requirement_points: number
      total_test_points: number
    }
  }> => {
    return api.get(`/api/projects/${projectId}/modules/${moduleId}/test-points`)
  },

  // 创建测试点
  createModuleTestPoint: (
    projectId: number,
    moduleId: number,
    data: { content: string; requirement_point_id: number; test_type?: string; priority?: string }
  ): Promise<any> => {
    return api.post(`/api/projects/${projectId}/modules/${moduleId}/test-points`, null, {
      params: data
    })
  },

  // 批量创建测试点
  batchCreateModuleTestPoints: (
    projectId: number,
    moduleId: number,
    points: Array<{
      content: string
      test_type?: string
      priority?: string
      requirement_point_id?: number
      created_by_ai?: boolean
    }>,
    clearExisting: boolean = false
  ): Promise<{ success: boolean; created_count: number; deleted_count?: number; points: any[] }> => {
    return api.post(`/api/projects/${projectId}/modules/${moduleId}/test-points/batch`, {
      points,
      clear_existing: clearExisting
    })
  },

  // 更新测试点
  updateModuleTestPoint: (
    projectId: number,
    moduleId: number,
    pointId: number,
    data: { content: string; test_type?: string; priority?: string }
  ): Promise<any> => {
    return api.put(`/api/projects/${projectId}/modules/${moduleId}/test-points/${pointId}`, null, {
      params: data
    })
  },

  // 删除测试点
  deleteModuleTestPoint: (projectId: number, moduleId: number, pointId: number): Promise<{ message: string }> => {
    return api.delete(`/api/projects/${projectId}/modules/${moduleId}/test-points/${pointId}`)
  },

  // ========== 按模块管理测试用例 ==========

  // 获取模块的测试用例列表（按测试点分组）
  getModuleTestCases: (projectId: number, moduleId: number): Promise<{
    test_points: Array<{
      id: number
      content: string
      test_type: string
      priority: string
      created_by_ai: boolean
      test_cases: Array<{
        id: number
        test_point_id: number
        module_id: number
        title: string
        description?: string
        preconditions?: string
        test_steps?: Array<{ step: number; action: string; expected: string }>
        expected_result?: string
        test_method?: string
        test_category?: string
        status: string
        created_by_ai: boolean
        edited_by_user: boolean
        created_at: string
        updated_at?: string
      }>
    }>
    total_test_points: number
    total_test_cases: number
  }> => {
    return api.get(`/api/projects/${projectId}/modules/${moduleId}/test-cases`)
  },

  // 创建测试用例
  createModuleTestCase: (
    projectId: number,
    moduleId: number,
    data: {
      title: string
      test_point_id: number
      description?: string
      preconditions?: string
      test_steps?: Array<{ step: number; action: string; expected: string }>
      expected_result?: string
      test_method?: string
      status?: string
      created_by_ai?: boolean
    }
  ): Promise<any> => {
    return api.post(`/api/projects/${projectId}/modules/${moduleId}/test-cases`, data)
  },

  // 更新测试用例
  updateModuleTestCase: (
    projectId: number,
    moduleId: number,
    caseId: number,
    data: {
      title?: string
      description?: string
      preconditions?: string
      test_steps?: Array<{ step: number; action: string; expected: string }>
      expected_result?: string
      test_method?: string
      status?: string
    }
  ): Promise<any> => {
    return api.put(`/api/projects/${projectId}/modules/${moduleId}/test-cases/${caseId}`, data)
  },

  // 删除测试用例
  deleteModuleTestCase: (projectId: number, moduleId: number, caseId: number): Promise<{ message: string }> => {
    return api.delete(`/api/projects/${projectId}/modules/${moduleId}/test-cases/${caseId}`)
  },

  // 批量创建测试用例
  batchCreateModuleTestCases: (
    projectId: number,
    moduleId: number,
    testCases: Array<{
      title: string
      test_point_id: number
      description?: string
      preconditions?: string
      test_steps?: Array<{ step: number; action: string; expected: string }>
      expected_result?: string
      test_method?: string
      created_by_ai?: boolean
    }>,
    clearExisting: boolean = false
  ): Promise<{ success: boolean; created_count: number; deleted_count?: number; test_cases: any[] }> => {
    return api.post(`/api/projects/${projectId}/modules/${moduleId}/test-cases/batch`, {
      test_cases: testCases,
      clear_existing: clearExisting
    })
  }
}
