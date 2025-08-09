/**
 * 标签管理API接口
 */

import { request } from '@/utils/request'

// 标签数据类型
export interface Tag {
  id: string
  name: string
  description?: string
  color?: string
  project_id?: string
  project_name?: string
  test_case_count: number
  created_at: string
  updated_at: string
}

// 标签创建请求
export interface TagCreateRequest {
  name: string
  description?: string
  color?: string
  project_id?: string
}

// 标签更新请求
export interface TagUpdateRequest {
  name?: string
  description?: string
  color?: string
}

// 标签列表响应
export interface TagListResponse {
  items: Tag[]
  total: number
  page: number
  page_size: number
}

// 标签管理API
export const tagApi = {
  /**
   * 获取标签列表
   */
  getTags(params: {
    page?: number
    page_size?: number
    search?: string
    project_id?: string
  } = {}): Promise<TagListResponse> {
    return request.get('/tags', { params })
  },

  /**
   * 获取标签详情
   */
  getTag(id: string): Promise<Tag> {
    return request.get(`/tags/${id}`)
  },

  /**
   * 创建标签
   */
  createTag(data: TagCreateRequest): Promise<Tag> {
    return request.post('/tags', data)
  },

  /**
   * 更新标签
   */
  updateTag(id: string, data: TagUpdateRequest): Promise<Tag> {
    return request.put(`/tags/${id}`, data)
  },

  /**
   * 删除标签
   */
  deleteTag(id: string): Promise<void> {
    return request.delete(`/tags/${id}`)
  },

  /**
   * 批量删除标签
   */
  batchDeleteTags(ids: string[]): Promise<void> {
    return request.post('/tags/batch-delete', { ids })
  },

  /**
   * 获取标签统计信息
   */
  getTagStats(projectId?: string): Promise<{
    total_tags: number
    tags_by_project: Record<string, number>
    test_cases_by_tag: Record<string, number>
    popular_tags: Array<{
      name: string
      count: number
    }>
  }> {
    return request.get('/tags/stats', { 
      params: projectId ? { project_id: projectId } : {} 
    })
  },

  /**
   * 搜索标签建议
   */
  searchTagSuggestions(query: string, projectId?: string): Promise<{
    suggestions: Array<{
      name: string
      count: number
      color?: string
    }>
  }> {
    return request.get('/tags/suggestions', {
      params: {
        q: query,
        project_id: projectId
      }
    })
  }
}

// 标签相关的工具函数
export const tagUtils = {
  /**
   * 生成标签颜色
   */
  generateTagColor(name: string): string {
    const colors = [
      '#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
      '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1',
      '#64748b', '#0891b2', '#059669', '#dc2626', '#7c3aed'
    ]
    
    let hash = 0
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash)
    }
    
    return colors[Math.abs(hash) % colors.length]
  },

  /**
   * 验证标签名称
   */
  validateTagName(name: string): {
    valid: boolean
    message?: string
  } {
    if (!name || name.trim().length === 0) {
      return { valid: false, message: '标签名称不能为空' }
    }
    
    if (name.length > 50) {
      return { valid: false, message: '标签名称不能超过50个字符' }
    }

    // 检查特殊字符
    const invalidChars = /[<>:"/\\|?*,;]/
    if (invalidChars.test(name)) {
      return { valid: false, message: '标签名称不能包含特殊字符' }
    }
    
    return { valid: true }
  },

  /**
   * 格式化标签显示名称
   */
  formatTagName(tag: Tag): string {
    return tag.project_name 
      ? `${tag.name} (${tag.project_name})`
      : tag.name
  },

  /**
   * 解析标签字符串
   */
  parseTagString(tagString: string): string[] {
    return tagString
      .split(/[,;，；]/)
      .map(tag => tag.trim())
      .filter(tag => tag.length > 0)
  },

  /**
   * 格式化标签数组为字符串
   */
  formatTagsToString(tags: string[]): string {
    return tags.join(', ')
  },

  /**
   * 获取标签颜色类型
   */
  getTagColorType(color: string): 'primary' | 'success' | 'warning' | 'danger' | 'info' {
    const colorMap: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
      '#2563eb': 'primary',
      '#10b981': 'success', 
      '#f59e0b': 'warning',
      '#ef4444': 'danger',
      '#6366f1': 'info'
    }
    
    return colorMap[color] || 'primary'
  }
}
