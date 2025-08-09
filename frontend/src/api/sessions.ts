/**
 * 处理会话API (最终版)
 * 基于最终版数据库结构的会话管理接口
 */
import { request } from '@/utils/request'

// 类型定义
export interface ProcessingSession {
  id: string
  session_type: 'document_parse' | 'image_analysis' | 'api_spec_parse' | 'database_schema_parse' | 'video_analysis' | 'manual_input'
  status: 'created' | 'processing' | 'completed' | 'failed'
  progress: number
  project_id?: string
  project_name?: string
  agent_type?: string
  processing_time?: number
  error_message?: string
  generated_count: number
  started_at?: string
  completed_at?: string
  created_at: string
  updated_at: string
}

export interface SessionListResponse {
  items: ProcessingSession[]
  total: number
  page: number
  page_size: number
}

export interface SessionTestCasesResponse {
  session: {
    id: string
    session_type: string
    status: string
    generated_count: number
  }
  test_cases: Array<{
    id: string
    title: string
    test_type: string
    test_level: string
    priority: string
    status: string
    ai_generated: boolean
    ai_confidence?: number
    created_at: string
  }>
  total: number
}

export interface SessionStats {
  total_sessions: number
  status_stats: Record<string, number>
  type_stats: Record<string, number>
  total_generated_test_cases: number
  avg_processing_time: number
}

// 会话管理API
export const sessionsApi = {
  // 获取会话列表
  getSessions(params: {
    page?: number
    page_size?: number
    project_id?: string
    session_type?: string
    status?: string
  } = {}): Promise<SessionListResponse> {
    return request.get('/sessions', { params })
  },

  // 获取会话详情
  getSession(id: string): Promise<ProcessingSession> {
    return request.get(`/sessions/${id}`)
  },

  // 删除会话
  deleteSession(id: string): Promise<{ message: string }> {
    return request.delete(`/sessions/${id}`)
  },

  // 获取会话生成的测试用例
  getSessionTestCases(id: string, params?: {
    page?: number
    page_size?: number
  }): Promise<SessionTestCasesResponse> {
    return request.get(`/sessions/${id}/test-cases`, { params })
  },

  // 获取会话的思维导图
  getSessionMindmap(id: string): Promise<any> {
    return request.get(`/sessions/${id}/mindmap`)
  },

  // 获取会话统计信息
  getSessionStats(): Promise<SessionStats> {
    return request.get('/sessions/stats/summary')
  },

  // 取消会话处理
  cancelSession(id: string): Promise<{ message: string }> {
    return request.post(`/sessions/${id}/cancel`)
  }
}

export default sessionsApi
