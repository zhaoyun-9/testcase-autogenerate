/**
 * 项目管理API接口
 */

import request from '@/utils/request'

// 项目状态枚举
export enum ProjectStatus {
  ACTIVE = 'active',
  ARCHIVED = 'archived'
}

// 项目数据类型
export interface Project {
  id: string
  name: string
  description?: string
  status: ProjectStatus
  test_case_count: number
  category_count: number
  tag_count: number
  created_at: string
  updated_at: string
}

// 项目创建请求
export interface ProjectCreateRequest {
  name: string
  description?: string
}

// 项目更新请求
export interface ProjectUpdateRequest {
  name?: string
  description?: string
  status?: ProjectStatus
}

// 项目列表响应
export interface ProjectListResponse {
  items: Project[]
  total: number
  page: number
  page_size: number
}

// 项目统计信息
export interface ProjectStats {
  total_projects: number
  active_projects: number
  archived_projects: number
  total_test_cases: number
  recent_activity: {
    date: string
    project_count: number
    test_case_count: number
  }[]
}

// 项目管理API
export const projectApi = {
  /**
   * 获取项目列表
   */
  getProjects(params: {
    page?: number
    page_size?: number
    search?: string
    status?: ProjectStatus
  } = {}): Promise<ProjectListResponse> {
    return request.get('/projects', { params })
  },

  /**
   * 获取项目详情
   */
  getProject(id: string): Promise<Project> {
    return request.get(`/projects/${id}`)
  },

  /**
   * 创建项目
   */
  createProject(data: ProjectCreateRequest): Promise<Project> {
    return request.post('/projects', data)
  },

  /**
   * 更新项目
   */
  updateProject(id: string, data: ProjectUpdateRequest): Promise<Project> {
    return request.put(`/projects/${id}`, data)
  },

  /**
   * 删除项目
   */
  deleteProject(id: string): Promise<void> {
    return request.delete(`/projects/${id}`)
  },

  /**
   * 批量删除项目
   */
  batchDeleteProjects(ids: string[]): Promise<void> {
    return request.post('/projects/batch-delete', { ids })
  },

  /**
   * 归档项目
   */
  archiveProject(id: string): Promise<Project> {
    return request.put(`/projects/${id}`, { status: ProjectStatus.ARCHIVED })
  },

  /**
   * 激活项目
   */
  activateProject(id: string): Promise<Project> {
    return request.put(`/projects/${id}`, { status: ProjectStatus.ACTIVE })
  },

  /**
   * 获取项目统计信息
   */
  getProjectStats(): Promise<ProjectStats> {
    return request.get('/projects/stats')
  },

  /**
   * 复制项目
   */
  duplicateProject(id: string, name: string): Promise<Project> {
    return request.post(`/projects/${id}/duplicate`, { name })
  },

  /**
   * 导出项目数据
   */
  exportProject(id: string, format: 'excel' | 'json' = 'excel'): Promise<Blob> {
    return request.get(`/projects/${id}/export`, {
      params: { format },
      responseType: 'blob'
    })
  },

  /**
   * 获取项目活动日志
   */
  getProjectActivity(id: string, params: {
    page?: number
    page_size?: number
    type?: string
  } = {}): Promise<{
    items: {
      id: string
      type: string
      description: string
      user: string
      created_at: string
    }[]
    total: number
    page: number
    page_size: number
  }> {
    return request.get(`/projects/${id}/activity`, { params })
  }
}

// 项目相关的工具函数
export const projectUtils = {
  /**
   * 获取项目状态标签类型
   */
  getStatusTagType(status: ProjectStatus): 'success' | 'info' | 'warning' | 'danger' {
    switch (status) {
      case ProjectStatus.ACTIVE:
        return 'success'
      case ProjectStatus.ARCHIVED:
        return 'info'
      default:
        return 'info'
    }
  },

  /**
   * 获取项目状态文本
   */
  getStatusText(status: ProjectStatus): string {
    switch (status) {
      case ProjectStatus.ACTIVE:
        return '活跃'
      case ProjectStatus.ARCHIVED:
        return '已归档'
      default:
        return '未知'
    }
  },

  /**
   * 格式化项目统计数据
   */
  formatProjectStats(project: Project): {
    label: string
    value: number
    color: string
  }[] {
    return [
      {
        label: '测试用例',
        value: project.test_case_count,
        color: '#2563eb'
      },
      {
        label: '分类',
        value: project.category_count,
        color: '#10b981'
      },
      {
        label: '标签',
        value: project.tag_count,
        color: '#f59e0b'
      }
    ]
  },

  /**
   * 验证项目名称
   */
  validateProjectName(name: string): {
    valid: boolean
    message?: string
  } {
    if (!name || name.trim().length === 0) {
      return { valid: false, message: '项目名称不能为空' }
    }
    
    if (name.length > 255) {
      return { valid: false, message: '项目名称不能超过255个字符' }
    }
    
    // 检查特殊字符
    const invalidChars = /[<>:"/\\|?*]/
    if (invalidChars.test(name)) {
      return { valid: false, message: '项目名称不能包含特殊字符 < > : " / \\ | ? *' }
    }
    
    return { valid: true }
  },

  /**
   * 生成项目颜色
   */
  generateProjectColor(name: string): string {
    const colors = [
      '#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
      '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1'
    ]
    
    let hash = 0
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash)
    }
    
    return colors[Math.abs(hash) % colors.length]
  }
}
