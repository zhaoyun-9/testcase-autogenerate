/**
 * 项目管理API (最终版)
 * 基于最终版数据库结构的项目管理接口
 */
import { request } from '@/utils/request'

// 类型定义
export interface Project {
  id: string
  name: string
  description?: string
  status: 'active' | 'archived'
  test_case_count: number
  category_count: number
  tag_count: number
  created_at: string
  updated_at: string
}

export interface ProjectCreateRequest {
  name: string
  description?: string
}

export interface ProjectUpdateRequest {
  name?: string
  description?: string
  status?: 'active' | 'archived'
}

export interface ProjectListResponse {
  items: Project[]
  total: number
  page: number
  page_size: number
}

export interface ProjectStats {
  test_cases: {
    by_type: Record<string, number>
    by_level: Record<string, number>
    by_priority: Record<string, number>
    by_status: Record<string, number>
    total: number
  }
}

// 项目管理API
export const projectsApi = {
  // 获取项目列表
  getProjects(params: {
    page?: number
    page_size?: number
    search?: string
    status?: 'active' | 'archived'
  } = {}): Promise<ProjectListResponse> {
    return request.get('/projects', { params })
  },

  // 创建项目
  createProject(data: ProjectCreateRequest): Promise<Project> {
    return request.post('/projects', data)
  },

  // 获取项目详情
  getProject(id: string): Promise<Project> {
    return request.get(`/projects/${id}`)
  },

  // 更新项目
  updateProject(id: string, data: ProjectUpdateRequest): Promise<Project> {
    return request.put(`/projects/${id}`, data)
  },

  // 删除项目
  deleteProject(id: string): Promise<{ message: string }> {
    return request.delete(`/projects/${id}`)
  },

  // 获取项目统计信息
  getProjectStats(id: string): Promise<ProjectStats> {
    return request.get(`/projects/${id}/stats`)
  }
}

export default projectsApi
