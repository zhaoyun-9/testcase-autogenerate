// 测试用例相关类型定义

export interface TestCase {
  id: string
  title: string
  description?: string
  testType: string
  testLevel: string
  priority: string
  status: string
  preconditions?: string
  testSteps: TestStep[]
  expectedResults?: string
  tags: string[]
  category?: string
  sessionId?: string
  createdAt: string
  updatedAt?: string
}

export interface TestStep {
  step: number
  action: string
  expectedResult?: string
  data?: any
}

export interface TestCaseSession {
  sessionId: string
  inputType: 'file' | 'text'
  status: 'created' | 'processing' | 'completed' | 'failed'
  uploadUrl?: string
  streamUrl: string
  createdAt: string
  fileInfo?: FileInfo
  requirementText?: string
}

export interface FileInfo {
  fileName: string
  fileSize: number
  fileSizeMb: string
  fileType: string
  selectedAgent: string
}

export interface GenerationProgress {
  sessionId: string
  status: 'idle' | 'processing' | 'completed' | 'failed'
  progress: number
  currentStage: string
  testCasesCount: number
  error?: string
  completedAt?: string
}

export interface GenerateRequest {
  requirementText?: string
  analysisTarget: string
  generateMindMap: boolean
  exportExcel: boolean
  maxTestCases?: number
  tags: string[]
  projectId?: string
}

export interface GenerateResponse {
  sessionId: string
  uploadUrl?: string
  streamUrl: string
  status: string
  inputType: string
  createdAt: string
}

export interface UploadFileRequest {
  file: File
  description?: string
}

export interface TestCaseFilters {
  search: string
  testType: string[]
  testLevel: string[]
  priority: string[]
  status: string[]
  tags: string[]
  sessionId?: string
}

export interface PaginatedTestCaseResponse {
  data: TestCase[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export interface TestCaseStats {
  totalCount: number
  byType: Record<string, number>
  byPriority: Record<string, number>
  byStatus: Record<string, number>
  byLevel: Record<string, number>
  recentActivity: Record<string, number>
}

// SSE消息类型
export interface SSEMessage {
  message_id: string
  type: string
  source: string
  content: string
  region: string
  platform: string
  is_final: boolean
  result?: Record<string, any>
  error?: string
  timestamp: string
  // 兼容性字段
  sessionId?: string
  progress?: number
  stage?: string
  testCasesCount?: number
}

// 文件类型映射
export const FILE_TYPE_MAPPING = {
  // 图片文件
  '.jpg': 'image',
  '.jpeg': 'image', 
  '.png': 'image',
  '.gif': 'image',
  '.bmp': 'image',
  '.webp': 'image',
  
  // 文档文件
  '.pdf': 'document',
  '.doc': 'document',
  '.docx': 'document',
  '.txt': 'document',
  '.md': 'document',
  
  // API规范文件
  '.json': 'api_spec',
  '.yaml': 'api_spec',
  '.yml': 'api_spec',
  
  // 数据库文件
  '.sql': 'database',
  '.db': 'database',
  '.sqlite': 'database',
  
  // 视频文件
  '.mp4': 'video',
  '.avi': 'video',
  '.mov': 'video',
  '.wmv': 'video',
  '.flv': 'video',
  '.webm': 'video'
} as const

// 测试类型选项
export const TEST_TYPE_OPTIONS = [
  { label: '功能测试', value: 'functional' },
  { label: '接口测试', value: 'interface' },
  { label: '性能测试', value: 'performance' },
  { label: '安全测试', value: 'security' },
  { label: '兼容性测试', value: 'compatibility' },
  { label: '易用性测试', value: 'usability' }
]

// 测试级别选项
export const TEST_LEVEL_OPTIONS = [
  { label: '单元测试', value: 'unit' },
  { label: '集成测试', value: 'integration' },
  { label: '系统测试', value: 'system' },
  { label: '验收测试', value: 'acceptance' }
]

// 优先级选项
export const PRIORITY_OPTIONS = [
  { label: 'P0 - 最高', value: 'P0' },
  { label: 'P1 - 高', value: 'P1' },
  { label: 'P2 - 中', value: 'P2' },
  { label: 'P3 - 低', value: 'P3' },
  { label: 'P4 - 最低', value: 'P4' }
]

// 状态选项
export const STATUS_OPTIONS = [
  { label: '草稿', value: 'draft' },
  { label: '待审核', value: 'review' },
  { label: '已通过', value: 'approved' },
  { label: '已废弃', value: 'deprecated' }
]

// 生成请求
export interface GenerateRequest {
  requirementText?: string
  analysisTarget: string
  generateMindMap?: boolean
  exportExcel?: boolean
  maxTestCases?: number
  tags?: string[]
  projectId?: string
}

// 生成响应
export interface GenerateResponse {
  sessionId: string
  inputType: string
  streamUrl: string
  uploadUrl?: string
  createdAt: string
  status: string
  message: string
}

// 文件上传响应
export interface FileUploadResponse {
  status: string
  message: string
  session_id: string
  filename: string
  file_size_mb: number
  selected_agent: string
  file_path: string
  progress?: number
}

// 测试用例会话
export interface TestCaseSession {
  sessionId: string
  inputType: 'file' | 'text'
  status: 'created' | 'uploading' | 'processing' | 'completed' | 'failed'
  streamUrl?: string
  uploadUrl?: string
  createdAt: string
  completedAt?: string
}

// 生成进度
export interface GenerationProgress {
  sessionId: string
  status: 'idle' | 'processing' | 'completed' | 'failed'
  progress: number
  currentStage: string
  testCasesCount: number
  error?: string
}
