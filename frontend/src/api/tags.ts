/**
 * 标签管理API (最终版)
 * 基于最终版数据库结构的标签管理接口
 */
import { request } from '@/utils/request'

// 类型定义
export interface Tag {
  id: string
  name: string
  color: string
  project_id?: string
  usage_count: number
  created_at: string
}

export interface TagCreateRequest {
  name: string
  color?: string
  project_id?: string
}

export interface TagUpdateRequest {
  name?: string
  color?: string
}

export interface TagListResponse {
  items: Tag[]
  total: number
}

export interface TagTestCasesResponse {
  tag: {
    id: string
    name: string
    color: string
  }
  test_cases: Array<{
    id: string
    title: string
    test_type: string
    test_level: string
    priority: string
    status: string
    created_at: string
  }>
  total: number
}

// 标签管理API
export const tagsApi = {
  // 获取标签列表
  getTags(params: {
    project_id?: string
    search?: string
    order_by?: 'name' | 'usage_count' | 'created_at'
  } = {}): Promise<TagListResponse> {
    return request.get('/tags', { params })
  },

  // 创建标签
  createTag(data: TagCreateRequest): Promise<Tag> {
    return request.post('/tags', data)
  },

  // 获取标签详情
  getTag(id: string): Promise<Tag> {
    return request.get(`/tags/${id}`)
  },

  // 更新标签
  updateTag(id: string, data: TagUpdateRequest): Promise<Tag> {
    return request.put(`/tags/${id}`, data)
  },

  // 删除标签
  deleteTag(id: string): Promise<{ message: string }> {
    return request.delete(`/tags/${id}`)
  },

  // 获取标签关联的测试用例
  getTagTestCases(id: string): Promise<TagTestCasesResponse> {
    return request.get(`/tags/${id}/test-cases`)
  },

  // 批量创建标签
  createTagsBatch(tags: TagCreateRequest[]): Promise<{
    created_count: number
    tags: Tag[]
  }> {
    return request.post('/tags/batch', tags)
  },

  // 获取热门标签
  getPopularTags(projectId: string, limit: number = 10): Promise<Tag[]> {
    return request.get(`/tags/popular/${projectId}`, { params: { limit } })
  }
}

export default tagsApi
