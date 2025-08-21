// 测试用例生成完整流程工具类

import { ElMessage } from 'element-plus'
import { testCaseGenerateApi } from '@/api/testCase'
import type { GenerateRequest, TestCaseSession } from '@/types/testCase'

export class TestCaseGenerationFlow {
  private session: TestCaseSession | null = null
  private onProgress?: (progress: any) => void
  private onComplete?: (result: any) => void
  private onError?: (error: string) => void

  constructor(callbacks?: {
    onProgress?: (progress: any) => void
    onComplete?: (result: any) => void
    onError?: (error: string) => void
  }) {
    this.onProgress = callbacks?.onProgress
    this.onComplete = callbacks?.onComplete
    this.onError = callbacks?.onError
  }

  /**
   * 开始生成流程
   */
  async startGeneration(config: GenerateRequest & { inputType: 'file' | 'text' }, files?: File[]) {
    try {
      // 1. 创建会话
      ElMessage.info('正在创建生成会话...')
      const sessionResponse = await testCaseGenerateApi.createSession(config)
      
      this.session = {
        sessionId: sessionResponse.sessionId,
        inputType: sessionResponse.inputType as 'file' | 'text',
        status: 'created',
        streamUrl: sessionResponse.streamUrl,
        createdAt: sessionResponse.createdAt
      }

      ElMessage.success('会话创建成功')
      console.log('会话创建成功:', this.session)

      // 2. 根据输入类型处理
      if (config.inputType === 'file' && files && files.length > 0) {
        await this.handleFileUpload(files, config.analysisTarget)
      } else if (config.inputType === 'text' && config.requirementText) {
        await this.handleTextInput(config.requirementText, config.analysisTarget)
      } else {
        throw new Error('输入参数不完整')
      }

      return this.session

    } catch (error: any) {
      console.error('生成流程启动失败:', error)
      this.onError?.(error.message || '生成流程启动失败')
      throw error
    }
  }

  /**
   * 处理文件上传
   */
  private async handleFileUpload(files: File[], description?: string) {
    if (!this.session) throw new Error('会话未创建')

    try {
      this.session.status = 'uploading'
      ElMessage.info(`开始上传 ${files.length} 个文件...`)

      // 逐个上传文件
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        ElMessage.info(`正在上传文件 ${i + 1}/${files.length}: ${file.name}`)

        const uploadResult = await testCaseGenerateApi.uploadFile(
          this.session.sessionId,
          file,
          description
        )

        console.log(`文件上传成功:`, uploadResult)

        // 发送进度更新
        this.onProgress?.({
          stage: `文件 ${file.name} 上传成功`,
          progress: ((i + 1) / files.length) * 20, // 上传阶段占20%
          status: 'uploading'
        })
      }

      // 文件上传完成后，等待后端启动处理过程
      this.session.status = 'processing'
      ElMessage.success('所有文件上传完成，智能分析即将开始...')

      // 等待一下让后端处理文件并准备SSE连接
      console.log('等待后端处理文件并准备SSE连接...')
      await new Promise(resolve => setTimeout(resolve, 2000)) // 等待2秒

      // 启动SSE连接监听处理过程
      await this.startSSEConnection()

      ElMessage.success('已连接到实时处理流，请查看日志')

    } catch (error: any) {
      this.session.status = 'failed'
      throw new Error(`文件上传失败: ${error.message}`)
    }
  }

  /**
   * 处理文本输入
   */
  private async handleTextInput(requirementText: string, analysisTarget?: string) {
    if (!this.session) throw new Error('会话未创建')

    try {
      this.session.status = 'processing'
      ElMessage.info('开始分析需求文本...')

      // 文本输入模式下，后端会立即启动处理，等待一下再连接SSE
      console.log('等待后端启动文本处理...')
      await new Promise(resolve => setTimeout(resolve, 1000)) // 等待1秒

      // 启动SSE连接监听处理过程
      await this.startSSEConnection()

      console.log('文本分析已启动:', { requirementText, analysisTarget })
      ElMessage.success('已连接到实时处理流，请查看日志')

    } catch (error: any) {
      this.session.status = 'failed'
      throw new Error(`文本分析失败: ${error.message}`)
    }
  }

  /**
   * 启动SSE连接
   */
  private async startSSEConnection() {
    if (!this.session) throw new Error('会话未创建')

    try {
      const streamUrl = this.session.streamUrl || `/api/v1/generate/stream/${this.session.sessionId}`
      console.log('启动SSE连接:', streamUrl)

      // 建立SSE连接
      const fullUrl = streamUrl.startsWith('http') ? streamUrl : `${window.location.origin}${streamUrl}`
      const eventSource = new EventSource(fullUrl)

      eventSource.onopen = (event) => {
        console.log('SSE连接已建立:', fullUrl)
        ElMessage.success('已连接到实时处理流')
      }

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('收到SSE消息:', data)

          // 处理进度更新
          if (data.type === 'progress') {
            this.onProgress?.(data)
          } else if (data.type === 'complete') {
            this.onComplete?.(data)
            eventSource.close()
          } else if (data.type === 'error') {
            this.onError?.(data.message || '处理过程中发生错误')
            eventSource.close()
          }
        } catch (error) {
          console.error('解析SSE消息失败:', error)
        }
      }

      eventSource.onerror = (error) => {
        console.error('SSE连接错误:', error)
        this.onError?.('实时连接中断')
        eventSource.close()
      }

    } catch (error: any) {
      console.error('启动SSE连接失败:', error)
      throw new Error(`启动SSE连接失败: ${error.message}`)
    }
  }

  /**
   * 获取当前会话
   */
  getSession() {
    return this.session
  }

  /**
   * 重置流程
   */
  reset() {
    this.session = null
  }

  /**
   * 取消生成
   */
  async cancel() {
    if (!this.session) return

    try {
      await testCaseGenerateApi.cancelGeneration(this.session.sessionId)
      this.session.status = 'failed'
      ElMessage.info('已取消生成任务')
    } catch (error) {
      console.error('取消生成失败:', error)
    }
  }

  /**
   * 连接到现有会话的SSE流
   */
  async connectToExistingSession(sessionId: string, streamUrl: string) {
    try {
      console.log('连接到现有会话SSE流:', sessionId, streamUrl)

      // 设置会话信息
      this.session = {
        sessionId,
        inputType: 'text', // 默认值，实际会从API获取
        status: 'processing',
        streamUrl,
        createdAt: new Date().toISOString()
      }

      // 建立SSE连接
      const fullUrl = streamUrl.startsWith('http') ? streamUrl : `${window.location.origin}${streamUrl}`
      const eventSource = new EventSource(fullUrl)

      eventSource.onopen = (event) => {
        console.log('SSE连接已建立:', fullUrl)
        ElMessage.success('已连接到会话流式输出')
      }

      eventSource.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          console.log('收到SSE消息:', message)

          // 处理不同类型的消息
          if (message.type === 'progress') {
            this.onProgress?.(message)
          } else if (message.type === 'complete') {
            this.onComplete?.(message)
            eventSource.close()
          } else if (message.type === 'error') {
            this.onError?.(message.content || '处理出错')
            eventSource.close()
          }

          // 如果是最终消息，关闭连接
          if (message.is_final) {
            eventSource.close()
          }
        } catch (error) {
          console.error('解析SSE消息失败:', error, event.data)
        }
      }

      eventSource.onerror = (event) => {
        console.error('SSE连接错误:', event)
        this.onError?.('SSE连接中断')
        eventSource.close()
      }

      // 保存EventSource引用以便后续关闭
      this.eventSource = eventSource

    } catch (error: any) {
      console.error('连接到现有会话失败:', error)
      this.onError?.(error.message || '连接失败')
      throw error
    }
  }

  private eventSource?: EventSource

  /**
   * 关闭SSE连接
   */
  closeSSEConnection() {
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = undefined
      console.log('SSE连接已关闭')
    }
  }
}

/**
 * 文件类型检测工具
 */
export class FileTypeDetector {
  private static readonly TYPE_MAPPING = {
    // 图片文件
    'image/jpeg': { category: 'image', agent: 'image_analyzer', description: '图片分析' },
    'image/png': { category: 'image', agent: 'image_analyzer', description: '图片分析' },
    'image/gif': { category: 'image', agent: 'image_analyzer', description: '图片分析' },
    
    // 文档文件
    'application/pdf': { category: 'document', agent: 'document_parser', description: 'PDF文档解析' },
    'application/msword': { category: 'document', agent: 'document_parser', description: 'Word文档解析' },
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': { 
      category: 'document', agent: 'document_parser', description: 'Word文档解析' 
    },
    'text/plain': { category: 'document', agent: 'document_parser', description: '文本文档解析' },
    
    // API规范文件
    'application/json': { category: 'api_spec', agent: 'api_analyzer', description: 'API规范分析' },
    'application/x-yaml': { category: 'api_spec', agent: 'api_analyzer', description: 'API规范分析' },
    'text/yaml': { category: 'api_spec', agent: 'api_analyzer', description: 'API规范分析' },
    
    // 视频文件
    'video/mp4': { category: 'video', agent: 'video_analyzer', description: '视频分析' },
    'video/avi': { category: 'video', agent: 'video_analyzer', description: '视频分析' },
    'video/quicktime': { category: 'video', agent: 'video_analyzer', description: '视频分析' },
    'video/x-msvideo': { category: 'video', agent: 'video_analyzer', description: '视频分析' },
    'video/x-ms-wmv': { category: 'video', agent: 'video_analyzer', description: '视频分析' },
    'video/x-flv': { category: 'video', agent: 'video_analyzer', description: '视频分析' },
    'video/webm': { category: 'video', agent: 'video_analyzer', description: '视频分析' }
  }

  /**
   * 检测文件类型并推荐智能体
   */
  static detectFileType(file: File) {
    const mapping = this.TYPE_MAPPING[file.type as keyof typeof this.TYPE_MAPPING]
    
    if (mapping) {
      return {
        category: mapping.category,
        recommendedAgent: mapping.agent,
        description: mapping.description,
        confidence: 0.9
      }
    }

    // 根据文件扩展名进行备用检测
    const extension = file.name.split('.').pop()?.toLowerCase()
    
    if (extension) {
      const extensionMapping: Record<string, any> = {
        'jpg': { category: 'image', agent: 'image_analyzer', description: '图片分析' },
        'jpeg': { category: 'image', agent: 'image_analyzer', description: '图片分析' },
        'png': { category: 'image', agent: 'image_analyzer', description: '图片分析' },
        'pdf': { category: 'document', agent: 'document_parser', description: 'PDF文档解析' },
        'doc': { category: 'document', agent: 'document_parser', description: 'Word文档解析' },
        'docx': { category: 'document', agent: 'document_parser', description: 'Word文档解析' },
        'txt': { category: 'document', agent: 'document_parser', description: '文本文档解析' },
        'json': { category: 'api_spec', agent: 'api_analyzer', description: 'API规范分析' },
        'yaml': { category: 'api_spec', agent: 'api_analyzer', description: 'API规范分析' },
        'yml': { category: 'api_spec', agent: 'api_analyzer', description: 'API规范分析' },
        'sql': { category: 'database', agent: 'database_analyzer', description: '数据库分析' },
        'mp4': { category: 'video', agent: 'video_analyzer', description: '视频分析' },
        'avi': { category: 'video', agent: 'video_analyzer', description: '视频分析' },
        'mov': { category: 'video', agent: 'video_analyzer', description: '视频分析' },
        'wmv': { category: 'video', agent: 'video_analyzer', description: '视频分析' },
        'flv': { category: 'video', agent: 'video_analyzer', description: '视频分析' },
        'webm': { category: 'video', agent: 'video_analyzer', description: '视频分析' }
      }

      const extMapping = extensionMapping[extension]
      if (extMapping) {
        return {
          category: extMapping.category,
          recommendedAgent: extMapping.agent,
          description: extMapping.description,
          confidence: 0.7
        }
      }
    }

    // 默认返回文档解析
    return {
      category: 'document',
      recommendedAgent: 'document_parser',
      description: '通用文档解析',
      confidence: 0.5
    }
  }

  /**
   * 验证文件大小
   */
  static validateFileSize(file: File, maxSizeMB: number = 50): boolean {
    const maxSizeBytes = maxSizeMB * 1024 * 1024
    return file.size <= maxSizeBytes
  }

  /**
   * 格式化文件大小
   */
  static formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }
}

/**
 * 生成配置验证器
 */
export class GenerationConfigValidator {
  /**
   * 验证生成配置
   */
  static validate(config: GenerateRequest & { inputType: 'file' | 'text' }, files?: File[]): {
    isValid: boolean
    errors: string[]
  } {
    const errors: string[] = []

    // 验证分析目标
    if (!config.analysisTarget || config.analysisTarget.trim().length === 0) {
      errors.push('请输入分析目标')
    }

    // 验证输入内容
    if (config.inputType === 'file') {
      if (!files || files.length === 0) {
        errors.push('请选择要上传的文件')
      } else {
        // 验证文件大小
        for (const file of files) {
          if (!FileTypeDetector.validateFileSize(file)) {
            errors.push(`文件 ${file.name} 超过大小限制 50MB`)
          }
        }
      }
    } else if (config.inputType === 'text') {
      if (!config.requirementText || config.requirementText.trim().length === 0) {
        errors.push('请输入需求描述')
      } else if (config.requirementText.trim().length < 10) {
        errors.push('需求描述至少需要10个字符')
      }
    }

    // 验证最大用例数
    if (config.maxTestCases && (config.maxTestCases < 1 || config.maxTestCases > 200)) {
      errors.push('最大用例数应在1-200之间')
    }

    return {
      isValid: errors.length === 0,
      errors
    }
  }
}
