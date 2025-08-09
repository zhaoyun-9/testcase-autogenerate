/**
 * 系统配置API (最终版)
 * 基于最终版数据库结构的系统管理接口
 */
import { request } from '../utils/request'

// 类型定义
export interface SystemConfig {
  id: string
  config_key: string
  config_value: string
  config_type: 'string' | 'number' | 'boolean' | 'json'
  description?: string
  created_at: string
  updated_at: string
}

export interface SystemConfigCreateRequest {
  config_key: string
  config_value: string
  config_type?: 'string' | 'number' | 'boolean' | 'json'
  description?: string
}

export interface SystemConfigUpdateRequest {
  config_value?: string
  config_type?: 'string' | 'number' | 'boolean' | 'json'
  description?: string
}

export interface SystemConfigListResponse {
  items: SystemConfig[]
  total: number
}

export interface SystemStatus {
  status: string
  timestamp: string
  statistics: {
    projects: number
    test_cases: number
    total_sessions: number
    active_sessions: number
  }
  database: {
    status: string
    pool_size?: string
  }
}

export interface SystemInfo {
  system: {
    platform: string
    python_version: string
    architecture: string
  }
  application: {
    name: string
    version: string
    environment: string
  }
  timestamp: string
}

export interface HealthCheck {
  status: string
  timestamp: string
  services: {
    database: string
    api: string
  }
}

// 系统配置API
export const systemApi = {
  // 获取系统配置列表
  getConfigs(params: {
    search?: string
    config_type?: 'string' | 'number' | 'boolean' | 'json'
  } = {}): Promise<SystemConfigListResponse> {
    return request.get('/system/configs', { params })
  },

  // 创建系统配置
  createConfig(data: SystemConfigCreateRequest): Promise<SystemConfig> {
    return request.post('/system/configs', data)
  },

  // 获取系统配置
  getConfig(configKey: string): Promise<SystemConfig> {
    return request.get(`/system/configs/${configKey}`)
  },

  // 更新系统配置
  updateConfig(configKey: string, data: SystemConfigUpdateRequest): Promise<SystemConfig> {
    return request.put(`/system/configs/${configKey}`, data)
  },

  // 删除系统配置
  deleteConfig(configKey: string): Promise<{ message: string }> {
    return request.delete(`/system/configs/${configKey}`)
  },

  // 获取系统状态
  getStatus(): Promise<SystemStatus> {
    return request.get('/system/status')
  },

  // 健康检查
  healthCheck(): Promise<HealthCheck> {
    return request.get('/system/health')
  },

  // 获取系统信息
  getInfo(): Promise<SystemInfo> {
    return request.get('/system/info')
  },

  // 获取系统信息 (别名，兼容设置页面)
  getSystemInfo(): Promise<SystemInfo> {
    return request.get('/system/info')
  },

  // 获取系统统计信息
  getSystemStats(): Promise<{
    total_projects: number
    total_test_cases: number
    total_users: number
    total_sessions: number
  }> {
    return request.get('/system/status').then(response => ({
      total_projects: response.statistics?.projects || 0,
      total_test_cases: response.statistics?.test_cases || 0,
      total_users: 0, // 暂时返回0，后续可以添加用户统计
      total_sessions: response.statistics?.total_sessions || 0
    }))
  },

  // 批量更新配置
  batchUpdateConfigs(configs: Record<string, string>): Promise<{
    message: string
    updated_configs: string[]
  }> {
    return request.post('/system/configs/batch', configs)
  },

  // 导出所有配置
  exportConfigs(): Promise<{
    configs: Record<string, {
      value: string
      type: string
      description?: string
    }>
    export_time: string
    total_count: number
  }> {
    return request.get('/system/configs/export')
  }
}

export default systemApi
