/**
 * 导出功能API (最终版)
 * 基于最终版数据库结构的导出功能接口
 */
import { request } from '@/utils/request'

// 类型定义
export interface ExportRecord {
  id: string
  export_type: 'excel' | 'word' | 'pdf'
  test_case_count: number
  project_id?: string
  project_name?: string
  session_id?: string
  file_name: string
  file_path: string
  file_size?: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string
}

export interface ExportRequest {
  export_type: 'excel' | 'word' | 'pdf'
  test_case_ids: string[]
  project_id?: string
  session_id?: string
  export_config?: Record<string, any>
}

export interface ExportListResponse {
  items: ExportRecord[]
  total: number
}

// 导出功能API
export const exportsApi = {
  // 创建导出任务
  createExport(data: ExportRequest): Promise<ExportRecord> {
    return request.post('/exports', data)
  },

  // 获取导出记录列表
  getExports(params: {
    project_id?: string
    session_id?: string
    export_type?: 'excel' | 'word' | 'pdf'
    status?: 'pending' | 'processing' | 'completed' | 'failed'
  } = {}): Promise<ExportListResponse> {
    return request.get('/exports', { params })
  },

  // 获取导出记录详情
  getExport(id: string): Promise<ExportRecord> {
    return request.get(`/exports/${id}`)
  },

  // 下载导出文件
  downloadExport(id: string): Promise<Blob> {
    return request.get(`/exports/${id}/download`, {
      responseType: 'blob'
    })
  },

  // 删除导出记录
  deleteExport(id: string): Promise<{ message: string }> {
    return request.delete(`/exports/${id}`)
  }
}

export default exportsApi
