// 需求管理相关类型定义

export interface Requirement {
  id: string
  requirement_id: string
  title: string
  description?: string
  requirement_type: RequirementType
  priority: RequirementPriority
  status: RequirementStatus
  project_id: string
  document_id?: string
  session_id?: string
  source_file_path?: string
  source_section?: string
  ai_generated: boolean
  ai_confidence?: number
  ai_model_info?: Record<string, any>
  extra_metadata?: Record<string, any>
  created_at: string
  updated_at: string
}

export enum RequirementType {
  FUNCTIONAL = 'functional',
  NON_FUNCTIONAL = 'non_functional',
  BUSINESS = 'business',
  TECHNICAL = 'technical',
  INTERFACE = 'interface',
  PERFORMANCE = 'performance',
  SECURITY = 'security',
  USABILITY = 'usability'
}

export enum RequirementPriority {
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low'
}

export enum RequirementStatus {
  DRAFT = 'draft',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  DEPRECATED = 'deprecated'
}

export interface RequirementListResponse {
  items: Requirement[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface TestCaseInfo {
  id: string
  title: string
  description?: string
  test_type: string
  test_level: string
  priority: string
  status: string
  created_at: string
}

export interface TestCaseRequirement {
  id: string
  test_case_id: string
  requirement_id: string
  coverage_type: string
  coverage_description?: string
  created_at: string
  requirement?: Requirement
  test_case?: TestCaseInfo
}

export interface RequirementCoverageStats {
  total_requirements: number
  covered_requirements: number
  uncovered_requirements: number
  coverage_rate: number
  requirements_by_type: Record<string, number>
  requirements_by_priority: Record<string, number>
}

export interface RequirementQuery {
  project_id?: string
  requirement_type?: RequirementType
  priority?: RequirementPriority
  status?: RequirementStatus
  keyword?: string
  page?: number
  page_size?: number
}

export interface RequirementTypeStats {
  [key: string]: {
    total: number
    draft: number
    approved: number
    rejected: number
    deprecated: number
  }
}

export interface RequirementPriorityStats {
  [key: string]: {
    total: number
    draft: number
    approved: number
    rejected: number
    deprecated: number
  }
}

// 需求类型显示名称映射
export const RequirementTypeLabels: Record<RequirementType, string> = {
  [RequirementType.FUNCTIONAL]: '功能需求',
  [RequirementType.NON_FUNCTIONAL]: '非功能需求',
  [RequirementType.BUSINESS]: '业务需求',
  [RequirementType.TECHNICAL]: '技术需求',
  [RequirementType.INTERFACE]: '接口需求',
  [RequirementType.PERFORMANCE]: '性能需求',
  [RequirementType.SECURITY]: '安全需求',
  [RequirementType.USABILITY]: '可用性需求'
}

// 需求优先级显示名称映射
export const RequirementPriorityLabels: Record<RequirementPriority, string> = {
  [RequirementPriority.HIGH]: '高',
  [RequirementPriority.MEDIUM]: '中',
  [RequirementPriority.LOW]: '低'
}

// 需求状态显示名称映射
export const RequirementStatusLabels: Record<RequirementStatus, string> = {
  [RequirementStatus.DRAFT]: '草稿',
  [RequirementStatus.APPROVED]: '已批准',
  [RequirementStatus.REJECTED]: '已拒绝',
  [RequirementStatus.DEPRECATED]: '已废弃'
}

// 需求类型颜色映射
export const RequirementTypeColors: Record<RequirementType, string> = {
  [RequirementType.FUNCTIONAL]: '#1890ff',
  [RequirementType.NON_FUNCTIONAL]: '#722ed1',
  [RequirementType.BUSINESS]: '#13c2c2',
  [RequirementType.TECHNICAL]: '#52c41a',
  [RequirementType.INTERFACE]: '#fa8c16',
  [RequirementType.PERFORMANCE]: '#eb2f96',
  [RequirementType.SECURITY]: '#f5222d',
  [RequirementType.USABILITY]: '#faad14'
}

// 需求优先级颜色映射
export const RequirementPriorityColors: Record<RequirementPriority, string> = {
  [RequirementPriority.HIGH]: '#f5222d',
  [RequirementPriority.MEDIUM]: '#fa8c16',
  [RequirementPriority.LOW]: '#52c41a'
}

// 需求状态颜色映射
export const RequirementStatusColors: Record<RequirementStatus, string> = {
  [RequirementStatus.DRAFT]: '#d9d9d9',
  [RequirementStatus.APPROVED]: '#52c41a',
  [RequirementStatus.REJECTED]: '#f5222d',
  [RequirementStatus.DEPRECATED]: '#8c8c8c'
}

// 测试用例类型标签映射
export const TestCaseTypeLabels: Record<string, string> = {
  'functional': '功能测试',
  'performance': '性能测试',
  'security': '安全测试',
  'integration': '集成测试',
  'unit': '单元测试',
  'ui': 'UI测试',
  'api': 'API测试'
}

// 测试用例级别标签映射
export const TestCaseLevelLabels: Record<string, string> = {
  'unit': '单元级',
  'integration': '集成级',
  'system': '系统级',
  'acceptance': '验收级'
}

// 测试用例优先级标签映射
export const TestCasePriorityLabels: Record<string, string> = {
  'P0': 'P0',
  'P1': 'P1',
  'P2': 'P2',
  'P3': 'P3'
}

// 测试用例状态标签映射
export const TestCaseStatusLabels: Record<string, string> = {
  'DRAFT': '草稿',
  'APPROVED': '已批准',
  'DEPRECATED': '已废弃',
  'draft': '草稿',
  'approved': '已批准',
  'deprecated': '已废弃'
}

// 测试用例类型颜色映射
export const TestCaseTypeColors: Record<string, string> = {
  'functional': '#1890ff',
  'performance': '#eb2f96',
  'security': '#f5222d',
  'integration': '#13c2c2',
  'unit': '#52c41a',
  'ui': '#fa8c16',
  'api': '#722ed1'
}

// 测试用例优先级颜色映射
export const TestCasePriorityColors: Record<string, string> = {
  'P0': '#f5222d',
  'P1': '#fa8c16',
  'P2': '#faad14',
  'P3': '#52c41a'
}

// 测试用例状态颜色映射
export const TestCaseStatusColors: Record<string, string> = {
  'DRAFT': '#d9d9d9',
  'APPROVED': '#52c41a',
  'DEPRECATED': '#8c8c8c',
  'draft': '#d9d9d9',
  'approved': '#52c41a',
  'deprecated': '#8c8c8c'
}
