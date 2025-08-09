/**
 * API统一导出 (最终版)
 * 基于最终版数据库结构的API接口统一导出
 */

// 导出所有API模块
export { projectsApi } from './projects'
export { categoriesApi } from './categories'
export { tagsApi } from './tags'
export { sessionsApi } from './sessions'
export { mindmapsApi } from './mindmaps'
export { exportsApi } from './exports'
export { systemApi } from './system'

// 导出更新后的测试用例API
export { testCaseGenerateApi, testCaseManagementApi, fileApi } from './testCase'

// 导出类型定义
export type { Project, ProjectCreateRequest, ProjectUpdateRequest } from './projects'
export type { Category, CategoryCreateRequest, CategoryUpdateRequest } from './categories'
export type { Tag, TagCreateRequest, TagUpdateRequest } from './tags'
export type { ProcessingSession } from './sessions'
export type { MindMap, MindMapCreateRequest, MindMapUpdateRequest } from './mindmaps'
export type { ExportRecord, ExportRequest } from './exports'
export type { SystemConfig, SystemStatus, SystemInfo, HealthCheck } from './system'

// 导出测试用例相关类型
export type { TestCase, GenerateRequest, GenerateResponse } from './testCase'

// 默认导出所有API
const api = {
  projects: () => import('./projects').then(m => m.projectsApi),
  categories: () => import('./categories').then(m => m.categoriesApi),
  tags: () => import('./tags').then(m => m.tagsApi),
  sessions: () => import('./sessions').then(m => m.sessionsApi),
  mindmaps: () => import('./mindmaps').then(m => m.mindmapsApi),
  exports: () => import('./exports').then(m => m.exportsApi),
  system: () => import('./system').then(m => m.systemApi),
  testCase: () => import('./testCase').then(m => ({ 
    generate: m.testCaseGenerateApi, 
    management: m.testCaseManagementApi 
  }))
}

export default api
