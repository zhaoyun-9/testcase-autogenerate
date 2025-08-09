/**
 * 分类管理API接口
 */

import { request } from '@/utils/request'

// 分类数据类型
export interface Category {
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

// 分类创建请求
export interface CategoryCreateRequest {
  name: string
  description?: string
  color?: string
  project_id?: string
}

// 分类更新请求
export interface CategoryUpdateRequest {
  name?: string
  description?: string
  color?: string
}

// 分类列表响应
export interface CategoryListResponse {
  items: Category[]
  total: number
  page: number
  page_size: number
}

// 分类管理API
export const categoryApi = {
  /**
   * 获取分类列表
   */
  getCategories(params: {
    page?: number
    page_size?: number
    search?: string
    project_id?: string
  } = {}): Promise<CategoryListResponse> {
    return request.get('/categories', { params })
  },

  /**
   * 获取分类详情
   */
  getCategory(id: string): Promise<Category> {
    return request.get(`/categories/${id}`)
  },

  /**
   * 创建分类
   */
  createCategory(data: CategoryCreateRequest): Promise<Category> {
    return request.post('/categories', data)
  },

  /**
   * 更新分类
   */
  updateCategory(id: string, data: CategoryUpdateRequest): Promise<Category> {
    return request.put(`/categories/${id}`, data)
  },

  /**
   * 删除分类
   */
  deleteCategory(id: string): Promise<void> {
    return request.delete(`/categories/${id}`)
  },

  /**
   * 批量删除分类
   */
  batchDeleteCategories(ids: string[]): Promise<void> {
    return request.post('/categories/batch-delete', { ids })
  },

  /**
   * 获取分类统计信息
   */
  getCategoryStats(projectId?: string): Promise<{
    total_categories: number
    categories_by_project: Record<string, number>
    test_cases_by_category: Record<string, number>
  }> {
    return request.get('/categories/stats', { 
      params: projectId ? { project_id: projectId } : {} 
    })
  }
}

// 分类相关的工具函数
export const categoryUtils = {
  /**
   * 生成分类颜色
   */
  generateCategoryColor(name: string): string {
    const colors = [
      '#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
      '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1'
    ]
    
    let hash = 0
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash)
    }
    
    return colors[Math.abs(hash) % colors.length]
  },

  /**
   * 验证分类名称
   */
  validateCategoryName(name: string): {
    valid: boolean
    message?: string
  } {
    if (!name || name.trim().length === 0) {
      return { valid: false, message: '分类名称不能为空' }
    }
    
    if (name.length > 100) {
      return { valid: false, message: '分类名称不能超过100个字符' }
    }
    
    return { valid: true }
  },

  /**
   * 格式化分类显示名称
   */
  formatCategoryName(category: Category): string {
    return category.project_name 
      ? `${category.name} (${category.project_name})`
      : category.name
  }
}
