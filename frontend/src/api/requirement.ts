// 需求管理API服务

import { request } from '@/utils/request'
import type {
  Requirement,
  RequirementListResponse,
  RequirementQuery,
  RequirementCoverageStats,
  RequirementTypeStats,
  RequirementPriorityStats,
  TestCaseRequirement
} from '@/types/requirement'

/**
 * 获取需求列表
 */
export function getRequirements(params: RequirementQuery = {}): Promise<RequirementListResponse> {
  return request.get('/requirements/', { params })
}

/**
 * 获取需求详情
 */
export function getRequirement(id: string): Promise<Requirement> {
  return request.get(`/requirements/${id}`)
}

/**
 * 获取需求关联的测试用例
 */
export function getRequirementTestCases(requirementId: string): Promise<TestCaseRequirement[]> {
  return request.get(`/requirements/${requirementId}/test-cases`)
}

/**
 * 获取需求覆盖统计
 */
export function getRequirementCoverageStats(projectId?: string): Promise<RequirementCoverageStats> {
  const params = projectId ? { project_id: projectId } : {}
  return request.get('/requirements/stats/coverage', { params })
}

/**
 * 按类型统计需求
 */
export function getRequirementsByType(projectId?: string): Promise<RequirementTypeStats> {
  const params = projectId ? { project_id: projectId } : {}
  return request.get('/requirements/stats/by-type', { params })
}

/**
 * 按优先级统计需求
 */
export function getRequirementsByPriority(projectId?: string): Promise<RequirementPriorityStats> {
  const params = projectId ? { project_id: projectId } : {}
  return request.get('/requirements/stats/by-priority', { params })
}

/**
 * 根据会话ID获取需求
 */
export function getRequirementsBySession(sessionId: string): Promise<Requirement[]> {
  return request.get(`/requirements/sessions/${sessionId}`)
}

/**
 * 搜索需求
 */
export function searchRequirements(
  keyword: string,
  projectId?: string,
  requirementType?: string,
  limit: number = 50
): Promise<RequirementListResponse> {
  const params: RequirementQuery = {
    keyword,
    page_size: limit
  }
  
  if (projectId) {
    params.project_id = projectId
  }
  
  if (requirementType) {
    params.requirement_type = requirementType as any
  }
  
  return request.get('/requirements/', { params })
}
