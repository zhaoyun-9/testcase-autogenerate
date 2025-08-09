import { request } from '@/utils/request'
import type {
  GenerateRequest,
  GenerateResponse,
  TestCase,
  PaginatedTestCaseResponse,
  TestCaseStats,
  TestCaseFilters
} from '@/types/testCase'

// 测试用例生成相关API (最终版)
export const testCaseGenerateApi = {
  // 创建生成会话 (实际上就是生成测试用例的端点)
  createSession(data: GenerateRequest): Promise<GenerateResponse> {
    return request.post('/generate/generate', data)
  },

  // 生成测试用例 (别名，保持向后兼容)
  generate(data: GenerateRequest): Promise<GenerateResponse> {
    return request.post('/generate/generate', data)
  },

  // 获取生成进度流
  getGenerationStream(sessionId: string): EventSource {
    return new EventSource(`/api/v1/generate/stream/${sessionId}`)
  },

  // 上传文件
  uploadFile(sessionId: string, file: File, description?: string): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    if (description) {
      formData.append('description', description)
    }

    return request.post(`/generate/upload/${sessionId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 取消生成
  cancelGeneration(sessionId: string): Promise<{ message: string }> {
    return request.post(`/generate/cancel/${sessionId}`)
  },

  // 处理文本分析 (如果需要的话)
  processText(sessionId: string, requirementText: string, analysisTarget: string): Promise<any> {
    return request.post(`/generate/process-text/${sessionId}`, {
      requirement_text: requirementText,
      analysis_target: analysisTarget
    })
  },

  // 获取会话列表
  getSessions(): Promise<{
    sessions: Array<{
      session_id: string
      status: string
      input_type: string
      file_name?: string
      selected_agent?: string
      progress: number
      created_at: string
      completed_at?: string
    }>
    total: number
  }> {
    return request.get('/generate/sessions')
  },

  // 获取会话状态
  getSessionStatus(sessionId: string): Promise<{
    session_id: string
    status: string
    input_type: string
    file_info?: any
    progress: number
    current_stage: string
    selected_agent?: string
    test_cases_count: number
    created_at: string
    completed_at?: string
    error?: string
  }> {
    return request.get(`/generate/status/${sessionId}`)
  },

  // 获取会话智能体日志
  getSessionAgentLogs(sessionId: string, params?: {
    agent_type?: string
    message_type?: string
    limit?: number
  }): Promise<{
    items: Array<{
      id: string
      session_id: string
      message_id: string
      agent_type: string
      agent_name: string
      message_type: string
      content: string
      region: string
      source?: string
      is_final: boolean
      result_data?: any
      error_info?: any
      metrics_data?: any
      processing_stage?: string
      timestamp: string
      created_at: string
    }>
    total: number
    session_id: string
    session_info?: any
  }> {
    return request.get(`/agent-logs/session/${sessionId}/logs`, { params })
  },

  // 获取会话智能体日志摘要
  getSessionLogsSummary(sessionId: string): Promise<{
    session_id: string
    total_messages: number
    message_types: Record<string, number>
    agents: Record<string, {
      count: number
      name: string
      first_message: string
      last_message: string
    }>
    processing_stages: string[]
    errors: Array<{
      agent: string
      content: string
      timestamp: string
    }>
    key_events: Array<{
      agent: string
      content: string
      timestamp: string
      result_data?: any
    }>
    key_metrics?: any
    processing_stages_detail?: any[]
  }> {
    return request.get(`/agent-logs/session/${sessionId}/summary`)
  },

  // 删除会话
  deleteSession(sessionId: string): Promise<{
    status: string
    message: string
    session_id: string
  }> {
    return request.delete(`/generate/session/${sessionId}`)
  }
}

// 测试用例管理相关API (最终版)
export const testCaseManagementApi = {
  // 获取测试用例列表
  getTestCases(params: {
    page?: number
    page_size?: number
    search?: string
    project_id?: string
    category_id?: string
    test_type?: string[]
    test_level?: string[]
    priority?: string[]
    status?: string[]
    tags?: string[]
    session_id?: string
  }): Promise<PaginatedTestCaseResponse> {
    return request.get('/test-cases', { params })
  },

  // 获取测试用例详情
  getTestCase(id: string): Promise<TestCase> {
    return request.get(`/test-cases/${id}`)
  },

  // 创建测试用例
  createTestCase(data: Partial<TestCase>): Promise<TestCase> {
    return request.post('/test-cases', data)
  },

  // 更新测试用例
  updateTestCase(id: string, data: Partial<TestCase>): Promise<TestCase> {
    return request.put(`/test-cases/${id}`, data)
  },

  // 删除测试用例
  deleteTestCase(id: string): Promise<void> {
    return request.delete(`/test-cases/${id}`)
  },

  // 批量删除测试用例
  batchDeleteTestCases(ids: string[]): Promise<void> {
    return request.post('/test-cases/batch-delete', { ids })
  },

  // 批量更新测试用例状态
  batchUpdateStatus(ids: string[], status: string): Promise<void> {
    return request.post('/test-cases/batch-update-status', { ids, status })
  },

  // 获取测试用例统计信息
  getStats(): Promise<TestCaseStats> {
    return request.get('/test-cases/stats')
  },

  // 获取测试用例统计信息 (别名方法，兼容现有代码)
  getTestCaseStats(): Promise<TestCaseStats> {
    return request.get('/test-cases/stats')
  }
}

// 导出相关API
export const exportApi = {
  // 导出测试用例到Excel
  exportToExcel(data: {
    testCaseIds?: string[]
    sessionId?: string
    exportConfig?: any
    templateType?: string
  }): Promise<{
    exportId: string
    status: string
    message: string
    downloadUrl?: string
  }> {
    return request.post('/exports/test-cases/excel', data)
  },

  // 获取导出状态
  getExportStatus(exportId: string): Promise<{
    exportId: string
    status: string
    message: string
    fileName?: string
    fileSize?: number
    downloadUrl?: string
  }> {
    return request.get(`/exports/status/${exportId}`)
  },

  // 下载导出文件
  downloadExportFile(exportId: string): Promise<any> {
    return request.download(`/exports/download/${exportId}`)
  }
}

// 思维导图相关API
export const mindmapApi = {
  // 获取思维导图列表
  getMindmaps(params?: {
    page?: number
    pageSize?: number
    sessionId?: string
    projectId?: string
  }): Promise<any> {
    return request.get('/mindmaps', { params })
  },

  // 获取思维导图详情
  getMindmapData(mindmapId: string): Promise<any> {
    return request.get(`/mindmaps/${mindmapId}`)
  },

  // 根据会话ID获取思维导图
  getMindmapBySession(sessionId: string): Promise<any> {
    return request.get(`/mindmaps/session/${sessionId}`)
  },

  // 创建思维导图
  createMindmap(data: {
    name: string
    sessionId: string
    projectId?: string
    mindMapData: any
    layoutConfig?: any
  }): Promise<any> {
    return request.post('/mindmaps', data)
  },

  // 更新思维导图
  updateMindmap(mindmapId: string, data: {
    name?: string
    mindMapData?: any
    layoutConfig?: any
  }): Promise<any> {
    return request.put(`/mindmaps/${mindmapId}`, data)
  },

  // 删除思维导图
  deleteMindmap(mindmapId: string): Promise<any> {
    return request.delete(`/mindmaps/${mindmapId}`)
  }
}

// 文件相关API
export const fileApi = {
  // 获取文件列表
  getFiles(params: {
    page?: number
    pageSize?: number
    search?: string
    fileType?: string
    startDate?: string
    endDate?: string
  } = {}): Promise<{
    items: Array<{
      id: string
      original_name: string
      file_name: string
      file_path: string
      file_type: string
      file_size: number
      mime_type: string
      usage_count: number
      created_at: string
    }>
    total: number
    page: number
    pageSize: number
  }> {
    return request.get('/files', { params })
  },

  // 上传文件
  uploadFile(file: File, options?: {
    description?: string
    category?: string
    uploadSource?: string
    projectId?: string
    sessionId?: string
  }): Promise<{
    id: string
    original_name: string
    file_path: string
    file_type: string
    file_size: number
  }> {
    const formData = new FormData()
    formData.append('file', file)

    // 根据文件类型自动确定upload_source
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    let uploadSource = options?.uploadSource

    if (!uploadSource) {
      // 自动映射文件类型到upload_source
      if (['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'].includes(fileExtension)) {
        uploadSource = 'image'
      } else if (['.pdf', '.doc', '.docx', '.txt', '.md'].includes(fileExtension)) {
        uploadSource = 'document'
      } else if (['.json', '.yaml', '.yml'].includes(fileExtension)) {
        uploadSource = 'api_spec'
      } else if (['.sql', '.db', '.sqlite', '.ddl'].includes(fileExtension)) {
        uploadSource = 'database_schema'
      } else if (['.mp4', '.avi', '.mov', '.wmv', '.flv'].includes(fileExtension)) {
        uploadSource = 'video'
      } else {
        uploadSource = 'document' // 默认为文档类型
      }
    }

    formData.append('upload_source', uploadSource)

    if (options?.description) {
      formData.append('description', options.description)
    }
    if (options?.category) {
      formData.append('category', options.category)
    }
    if (options?.projectId) {
      formData.append('project_id', options.projectId)
    }
    if (options?.sessionId) {
      formData.append('session_id', options.sessionId)
    }

    return request.upload('/files/upload', formData)
  },

  // 删除文件
  deleteFile(fileId: string): Promise<void> {
    return request.delete(`/files/${fileId}`)
  },

  // 批量删除文件
  batchDeleteFiles(fileIds: string[]): Promise<void> {
    return request.post('/files/batch-delete', { file_ids: fileIds })
  },

  // 获取文件统计
  getFileStats(): Promise<{
    total_files: number
    total_size: number
    image_count: number
    video_count: number
    document_count: number
    by_type: Record<string, number>
    by_month: Array<{
      month: string
      count: number
      size: number
    }>
  }> {
    return request.get('/files/stats')
  },

  // 分析文件类型和推荐智能体
  analyzeFile(file: File): Promise<{
    fileType: string
    fileCategory: string
    recommendedAgent: string
    confidence: number
    supportedFormats: string[]
  }> {
    const formData = new FormData()
    formData.append('file', file)
    return request.upload('/files/analyze', formData)
  },

  // 获取支持的文件类型
  getSupportedFileTypes(): Promise<{
    categories: Record<string, {
      name: string
      extensions: string[]
      maxSize: number
      description: string
    }>
  }> {
    return request.get('/files/supported-types')
  },

  // 清理未使用的文件
  cleanupUnusedFiles(olderThanDays: number = 30): Promise<{
    deleted_count: number
    freed_space: number
  }> {
    return request.post('/files/cleanup', { older_than_days: olderThanDays })
  }
}
