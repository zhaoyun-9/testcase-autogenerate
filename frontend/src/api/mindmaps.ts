/**
 * 思维导图API (最终版)
 * 基于最终版数据库结构的思维导图管理接口
 */
import { request } from '@/utils/request'

// 类型定义
export interface MindMap {
  id: string
  name: string
  session_id: string
  project_id?: string
  project_name?: string
  mind_map_data: Record<string, any>
  layout_config?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface MindMapCreateRequest {
  name: string
  session_id: string
  project_id?: string
  mind_map_data: Record<string, any>
  layout_config?: Record<string, any>
}

export interface MindMapUpdateRequest {
  name?: string
  mind_map_data?: Record<string, any>
  layout_config?: Record<string, any>
}

export interface MindMapListResponse {
  items: MindMap[]
  total: number
}

export interface MindMapExportResponse {
  format: string
  data: {
    name: string
    mind_map_data: Record<string, any>
    layout_config?: Record<string, any>
    created_at: string
    updated_at: string
  }
}

// 思维导图API
export const mindmapsApi = {
  // 获取思维导图列表
  getMindmaps(params: {
    project_id?: string
    session_id?: string
  } = {}): Promise<MindMapListResponse> {
    return request.get('/mindmaps', { params })
  },

  // 创建思维导图
  createMindmap(data: MindMapCreateRequest): Promise<MindMap> {
    return request.post('/mindmaps', data)
  },

  // 获取思维导图详情
  getMindmap(id: string): Promise<MindMap> {
    return request.get(`/mindmaps/${id}`)
  },

  // 更新思维导图
  updateMindmap(id: string, data: MindMapUpdateRequest): Promise<MindMap> {
    return request.put(`/mindmaps/${id}`, data)
  },

  // 删除思维导图
  deleteMindmap(id: string): Promise<{ message: string }> {
    return request.delete(`/mindmaps/${id}`)
  },

  // 根据会话ID获取思维导图
  getMindmapBySession(sessionId: string): Promise<MindMap> {
    return request.get(`/mindmaps/session/${sessionId}`)
  },

  // 导出思维导图
  exportMindmap(id: string, format: string = 'json'): Promise<MindMapExportResponse> {
    return request.post(`/mindmaps/${id}/export`, { format })
  }
}

export default mindmapsApi
