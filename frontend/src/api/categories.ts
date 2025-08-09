/**
 * 分类管理API (最终版)
 * 基于最终版数据库结构的分类管理接口
 */
import { request } from '@/utils/request'

// 类型定义
export interface Category {
  id: string
  name: string
  description?: string
  parent_id?: string
  project_id: string
  sort_order: number
  test_case_count: number
  children?: Category[]
  created_at: string
}

export interface CategoryCreateRequest {
  name: string
  description?: string
  parent_id?: string
  project_id: string
  sort_order?: number
}

export interface CategoryUpdateRequest {
  name?: string
  description?: string
  parent_id?: string
  sort_order?: number
}

export interface CategoryListResponse {
  items: Category[]
  total: number
}

// 分类管理API
export const categoriesApi = {
  // 获取分类列表
  getCategories(params: {
    project_id?: string
    parent_id?: string
    include_children?: boolean
  } = {}): Promise<CategoryListResponse> {
    return request.get('/categories', { params })
  },

  // 创建分类
  createCategory(data: CategoryCreateRequest): Promise<Category> {
    return request.post('/categories', data)
  },

  // 获取分类详情
  getCategory(id: string): Promise<Category> {
    return request.get(`/categories/${id}`)
  },

  // 更新分类
  updateCategory(id: string, data: CategoryUpdateRequest): Promise<Category> {
    return request.put(`/categories/${id}`, data)
  },

  // 删除分类
  deleteCategory(id: string): Promise<{ message: string }> {
    return request.delete(`/categories/${id}`)
  },

  // 获取分类树结构
  getCategoryTree(id: string): Promise<Category> {
    return request.get(`/categories/${id}/tree`)
  }
}

export default categoriesApi
