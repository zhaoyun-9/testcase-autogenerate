<template>
  <div class="progress-monitor">
    <!-- 连接状态指示器 -->
    <div class="connection-status">
      <el-tag
        :type="connectionStatusType"
        size="small"
        effect="dark"
      >
        <el-icon class="status-icon">
          <component :is="connectionStatusIcon" />
        </el-icon>
        {{ connectionStatusText }}
      </el-tag>
    </div>

    <!-- 进度条 -->
    <div v-if="progress.status !== 'idle'" class="progress-section">
      <el-progress
        :percentage="progress.progress"
        :status="progressStatus"
        :stroke-width="8"
        :show-text="true"
      />
      
      <div class="progress-info">
        <div class="current-stage">
          <el-icon class="stage-icon">
            <Loading v-if="progress.status === 'processing'" />
            <CircleCheck v-else-if="progress.status === 'completed'" />
            <CircleClose v-else-if="progress.status === 'failed'" />
            <Clock v-else />
          </el-icon>
          <span>{{ progress.currentStage || '准备中...' }}</span>
        </div>
        
        <div v-if="progress.testCasesCount > 0" class="test-cases-count">
          已生成测试用例: {{ progress.testCasesCount }} 个
        </div>
        
        <div v-if="progress.error" class="error-message">
          <el-alert
            :title="progress.error"
            type="error"
            :closable="false"
            show-icon
          />
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div v-if="showActions && progress.status !== 'idle'" class="actions">
      <el-button
        v-if="progress.status === 'processing'"
        type="danger"
        size="small"
        @click="handleCancel"
      >
        取消
      </el-button>
      
      <el-button
        v-if="progress.status === 'failed'"
        type="primary"
        size="small"
        @click="handleRetry"
      >
        重试
      </el-button>
      
      <el-button
        v-if="progress.status === 'completed'"
        type="success"
        size="small"
        @click="handleViewResults"
      >
        查看结果
      </el-button>
    </div>

    <!-- 消息日志 -->
    <div v-if="showLogs" class="logs-section">
      <div class="logs-header">
        <span>处理日志</span>
        <el-button
          type="text"
          size="small"
          @click="clearLogs"
        >
          清空
        </el-button>
      </div>
      
      <div class="logs-content" ref="logsContentRef">
        <div
          v-for="(message, index) in messages"
          :key="index"
          class="log-entry"
          :class="getMessageTypeClass(message.type)"
        >
          <div class="log-time">{{ formatTime(message.timestamp) }}</div>
          <div class="log-type">
            <el-tag :type="getMessageTagType(message.type)" size="small">
              {{ message.type }}
            </el-tag>
          </div>
          <div class="log-content">{{ message.message || message.content }}</div>
        </div>
        
        <div v-if="messages.length === 0" class="empty-logs">
          暂无日志信息
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Loading,
  CircleCheck,
  CircleClose,
  Clock,
  Connection,
  Close
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { SSEClient } from '@/utils/sse'
import type { SSEMessage } from '@/types/sse'

// 定义Props
interface Props {
  sessionId?: string
  streamUrl?: string
  autoConnect?: boolean
  showLogs?: boolean
  showActions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoConnect: true,
  showLogs: true,
  showActions: true
})

// 定义Emits
const emit = defineEmits<{
  connected: []
  disconnected: []
  progress: [progress: GenerationProgress]
  completed: [result: any]
  failed: [error: string]
  cancel: []
  retry: []
  'view-results': []
  message: [message: SSEMessage]
}>()

// 进度信息接口
interface GenerationProgress {
  sessionId: string
  status: 'idle' | 'processing' | 'completed' | 'failed'
  progress: number
  currentStage: string
  testCasesCount: number
  message?: string
  error?: string
}

// 响应式数据
const sseClient = ref<SSEClient | null>(null)
const isConnected = ref(false)
const messages = ref<SSEMessage[]>([])
const logsContentRef = ref<HTMLElement>()

const progress = ref<GenerationProgress>({
  sessionId: '',
  status: 'idle',
  progress: 0,
  currentStage: '',
  testCasesCount: 0
})

// 计算属性
const connectionStatusType = computed(() => {
  return isConnected.value ? 'success' : 'danger'
})

const connectionStatusIcon = computed(() => {
  return isConnected.value ? Connection : Close
})

const connectionStatusText = computed(() => {
  return isConnected.value ? '已连接' : '未连接'
})

const progressStatus = computed(() => {
  switch (progress.value.status) {
    case 'completed':
      return 'success'
    case 'failed':
      return 'exception'
    default:
      return undefined
  }
})

// 处理SSE消息
const handleSSEMessage = (message: SSEMessage | string | any) => {
  console.log('收到SSE消息:', message)
  console.log('消息类型:', typeof message)

  let parsedMessage: SSEMessage

  // 处理不同类型的消息输入
  if (typeof message === 'string') {
    // 如果是字符串，可能是原始SSE事件字符串
    try {
      // 尝试直接解析为JSON
      parsedMessage = JSON.parse(message)
    } catch (error) {
      // 如果直接解析失败，尝试提取data:后面的JSON字符串
      try {
        const dataMatch = message.match(/data:\s*(.+)/)
        if (dataMatch && dataMatch[1]) {
          parsedMessage = JSON.parse(dataMatch[1])
          console.log('从SSE事件中解析出消息:', parsedMessage)
        } else {
          console.warn('无法从字符串中提取消息数据:', message)
          return
        }
      } catch (parseError) {
        console.error('解析SSE消息失败:', parseError, message)
        return
      }
    }
  } else if (message && typeof message === 'object') {
    // 如果是对象，直接使用
    parsedMessage = message as SSEMessage
  } else {
    console.warn('无效的消息格式:', message)
    return
  }

  // 确保消息有必要的字段
  if (!parsedMessage.content && !parsedMessage.type) {
    console.warn('消息缺少必要字段:', parsedMessage)
    return
  }

  // 发出消息事件供父组件处理
  console.log('ProgressMonitor发出消息事件:', parsedMessage)
  emit('message', parsedMessage)

  // 添加到消息日志
  messages.value.push({
    ...parsedMessage,
    timestamp: parsedMessage.timestamp || new Date().toISOString()
  })

  // 更新进度信息
  if (parsedMessage.type === 'progress' && parsedMessage.result) {
    const progressData = parsedMessage.result as any
    progress.value = {
      sessionId: props.sessionId || '',
      status: progressData.status || 'processing',
      progress: progressData.progress || 0,
      currentStage: progressData.currentStage || progressData.stage || '',
      testCasesCount: progressData.testCasesCount || 0,
      message: progressData.message || ''
    }
    emit('progress', progress.value)
  }

  // 处理完成状态
  if (parsedMessage.type === 'complete' || parsedMessage.type === 'completion' || parsedMessage.type === 'final_result') {
    progress.value.status = 'completed'
    progress.value.progress = 100
    emit('completed', progress.value)
  }

  // 处理错误状态
  if (parsedMessage.type === 'error') {
    progress.value.status = 'failed'
    emit('failed', parsedMessage.result || parsedMessage.error)
  }

  // 自动滚动到底部
  nextTick(() => {
    scrollToBottom()
  })
}

// 处理心跳消息
const handleHeartbeat = (message: any) => {
  console.log('收到心跳:', message)
  // 心跳消息不需要特殊处理，只是保持连接活跃
}

// 处理流式文本消息
const handleStreamText = (data: { content: string; eventType?: string; timestamp: string }) => {
  console.log('收到流式文本:', data)

  // 将流式文本转换为SSE消息格式
  const message: SSEMessage = {
    message_id: `stream-${Date.now()}`,
    type: data.eventType || 'message',
    source: 'stream',
    content: data.content,
    region: 'process',
    platform: 'test_case',
    is_final: false,
    timestamp: data.timestamp
  }

  // 发出消息事件供父组件处理
  emit('message', message)

  // 添加到消息日志
  messages.value.push(message)

  // 自动滚动到底部
  nextTick(() => {
    scrollToBottom()
  })
}

// 连接SSE
const connectSSE = async () => {
  console.log('=== connectSSE 被调用 ===')
  console.log('sessionId:', props.sessionId)
  console.log('streamUrl:', props.streamUrl)

  if (!props.sessionId && !props.streamUrl) {
    console.warn('缺少sessionId或streamUrl，无法建立SSE连接')
    return
  }

  // 关闭现有连接
  console.log('准备关闭现有SSE连接')
  disconnectSSE(true) // 完全清理旧连接

  const url = props.streamUrl || `/api/v1/generate/stream/${props.sessionId}`
  console.log('建立SSE连接:', url)
  sseClient.value = new SSEClient(url)

  // 注册连接状态事件
  sseClient.value.on('connected', () => {
    isConnected.value = true
    emit('connected')
    ElMessage.success('已连接到处理流')
  })

  sseClient.value.on('error', (error) => {
    isConnected.value = false
    emit('disconnected')
    console.error('SSE连接错误:', error)
  })

  // 注册消息处理事件
  console.log('注册SSE事件监听器')
  sseClient.value.on('message', handleSSEMessage)
  console.log('已注册message事件监听器')
  sseClient.value.on('progress', handleSSEMessage)
  sseClient.value.on('stage', handleSSEMessage)
  sseClient.value.on('result', handleSSEMessage)
  sseClient.value.on('complete', handleSSEMessage)
  sseClient.value.on('completion', handleSSEMessage)
  sseClient.value.on('final_result', handleSSEMessage)
  sseClient.value.on('heartbeat', handleHeartbeat)
  console.log('所有SSE事件监听器注册完成')

  // 处理流式文本消息
  sseClient.value.on('stream-text', handleStreamText)
  sseClient.value.on('message-text', handleStreamText)
  sseClient.value.on('progress-text', handleStreamText)
  sseClient.value.on('stage-text', handleStreamText)
  sseClient.value.on('result-text', handleStreamText)
  sseClient.value.on('complete-text', handleStreamText)

  try {
    await sseClient.value.connect()
  } catch (error) {
    console.error('SSE连接失败:', error)
    ElMessage.error('连接处理流失败')
  }
}

// 断开SSE连接
const disconnectSSE = (clearListeners: boolean = false) => {
  console.log('=== disconnectSSE 被调用 ===, clearListeners:', clearListeners)
  if (sseClient.value) {
    console.log('关闭现有SSE客户端')
    sseClient.value.close(clearListeners)
    sseClient.value = null
  }
  isConnected.value = false
}

// 监听sessionId和streamUrl变化
watch([() => props.sessionId, () => props.streamUrl], () => {
  if (props.autoConnect && (props.sessionId || props.streamUrl)) {
    connectSSE()
  }
}, { immediate: true })

// 滚动到底部
const scrollToBottom = () => {
  if (logsContentRef.value) {
    logsContentRef.value.scrollTop = logsContentRef.value.scrollHeight
  }
}

// 清空日志
const clearLogs = () => {
  messages.value = []
}

// 格式化时间
const formatTime = (timestamp: string) => {
  return dayjs(timestamp).format('HH:mm:ss')
}

// 获取消息类型标签类型
const getMessageTagType = (type: string) => {
  switch (type) {
    case 'error':
      return 'danger'
    case 'complete':
    case 'final_result':
      return 'success'
    case 'progress':
      return 'primary'
    default:
      return 'info'
  }
}

// 获取消息类型样式类
const getMessageTypeClass = (type: string) => {
  return `log-${type}`
}

// 事件处理函数
const handleCancel = () => {
  emit('cancel')
}

const handleRetry = () => {
  emit('retry')
}

const handleViewResults = () => {
  emit('view-results')
}

// 暴露方法
defineExpose({
  connect: connectSSE,
  disconnect: disconnectSSE,
  clearLogs,
  getProgress: () => progress.value,
  getMessages: () => messages.value
})

// 组件卸载时断开连接
onUnmounted(() => {
  console.log('组件卸载，清空所有监听器')
  disconnectSSE(true) // 组件卸载时清空listeners
})
</script>

<style lang="scss" scoped>
.progress-monitor {
  .connection-status {
    margin-bottom: 16px;
    
    .status-icon {
      margin-right: 4px;
    }
  }
  
  .progress-section {
    margin-bottom: 16px;
    
    .progress-info {
      margin-top: 12px;
      
      .current-stage {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
        
        .stage-icon {
          margin-right: 8px;
          color: var(--el-color-primary);
        }
      }
      
      .test-cases-count {
        font-size: 14px;
        color: var(--el-color-success);
        margin-bottom: 8px;
      }
      
      .error-message {
        margin-top: 8px;
      }
    }
  }
  
  .actions {
    margin-bottom: 16px;
    
    .el-button + .el-button {
      margin-left: 8px;
    }
  }
  
  .logs-section {
    .logs-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      font-weight: 500;
    }
    
    .logs-content {
      max-height: 300px;
      overflow-y: auto;
      border: 1px solid var(--el-border-color);
      border-radius: 4px;
      padding: 8px;
      background: var(--el-bg-color-page);
      
      .log-entry {
        display: flex;
        align-items: flex-start;
        margin-bottom: 8px;
        font-size: 12px;
        
        .log-time {
          width: 60px;
          flex-shrink: 0;
          color: var(--el-text-color-secondary);
          margin-right: 8px;
        }
        
        .log-type {
          width: 80px;
          flex-shrink: 0;
          margin-right: 8px;
        }
        
        .log-content {
          flex: 1;
          word-break: break-word;
        }
        
        &.log-error {
          .log-content {
            color: var(--el-color-danger);
          }
        }
        
        &.log-success {
          .log-content {
            color: var(--el-color-success);
          }
        }
      }
      
      .empty-logs {
        text-align: center;
        color: var(--el-text-color-placeholder);
        padding: 20px;
      }
    }
  }
}
</style>
