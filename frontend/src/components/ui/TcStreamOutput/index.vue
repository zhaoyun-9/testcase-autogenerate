<template>
  <div class="tc-stream-output">
    <!-- 头部 -->
    <div class="tc-stream-output__header">
      <div class="tc-stream-output__title">
        <el-icon><Monitor /></el-icon>
        <span>{{ title }}</span>
        <el-tag
          :type="connectionStatus.type"
          size="small"
          effect="dark"
        >
          <el-icon class="status-icon">
            <component :is="connectionStatus.icon" />
          </el-icon>
          {{ connectionStatus.text }}
        </el-tag>
      </div>
      <div class="tc-stream-output__actions">
        <el-button
          type="text"
          size="small"
          :icon="Refresh"
          @click="handleClear"
          :disabled="!hasContent"
        >
          清空
        </el-button>
        <el-button
          type="text"
          size="small"
          :icon="showPanel ? 'Hide' : 'View'"
          @click="togglePanel"
        >
          {{ showPanel ? '隐藏' : '显示' }}
        </el-button>
      </div>
    </div>

    <!-- 内容区域 -->
    <div v-show="showPanel" class="tc-stream-output__content">
      <!-- 进度信息 -->
      <div v-if="progress && progress.status !== 'idle'" class="tc-stream-output__progress">
        <el-progress
          :percentage="progress.progress"
          :status="progressStatus"
          :stroke-width="6"
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
            已生成: {{ progress.testCasesCount }} 个测试用例
          </div>
        </div>
      </div>

      <!-- 流式文本输出 -->
      <div class="tc-stream-output__streams">
        <div class="streams-header">
          <span>实时输出内容 ({{ Object.keys(streamContents).length }} 个来源)</span>
          <el-button
            type="text"
            size="small"
            @click="clearAllStreams"
            :disabled="Object.keys(streamContents).length === 0"
          >
            清空全部
          </el-button>
        </div>
        <div class="streams-content" ref="streamsRef">
          <div v-if="Object.keys(streamContents).length > 0" class="stream-containers">
            <div
              v-for="(content, source) in streamContents"
              :key="source"
              class="stream-source-container"
            >
              <!-- 使用 Ant Design X 的 Bubble 组件 -->
              <Bubble
                :content="content.text"
                :typing="content.typing"
                :loading="content.status === 'loading'"
                placement="start"
                variant="outlined"
                :header="source"
                @typing-complete="onStreamFinish(source)"
              />
            </div>
          </div>
          <div v-else class="empty-streams">
            <el-empty description="等待流式输出..." :image-size="60" />
          </div>
        </div>
      </div>

      <!-- 消息日志 -->
      <div class="tc-stream-output__messages">
        <div class="messages-header">
          <span>消息日志</span>
          <el-tag size="small" type="info">{{ messages.length }} 条消息</el-tag>
        </div>
        <div class="messages-content" ref="messagesRef">
          <div
            v-for="(message, index) in messages"
            :key="index"
            class="stream-message"
            :class="`message-${message.type}`"
          >
            <div class="message-header">
              <el-tag
                :type="getMessageTagType(message.type)"
                size="small"
              >
                {{ getMessageTypeLabel(message.type) }}
              </el-tag>
              <span class="message-time">
                {{ formatTime(message.timestamp) }}
              </span>
            </div>
            <div class="message-content">
              {{ message.content }}
            </div>
            <div v-if="message.result" class="message-result">
              <el-collapse>
                <el-collapse-item title="详细数据" name="result">
                  <pre>{{ JSON.stringify(message.result, null, 2) }}</pre>
                </el-collapse-item>
              </el-collapse>
            </div>
          </div>
          <div v-if="messages.length === 0" class="empty-messages">
            <el-empty description="暂无消息" :image-size="80" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import { Bubble } from '@ant-design/x'
import {
  Monitor,
  Refresh,
  Loading,
  CircleCheck,
  CircleClose,
  Clock,
  Connection,
  Close
} from '@element-plus/icons-vue'
import { formatTime } from '../utils'

interface StreamContent {
  text: string
  typing: boolean | { step?: number; interval?: number }
  status: 'loading' | 'success' | 'error'
}

interface StreamMessage {
  type: string
  content: string
  timestamp: string
  source?: string
  result?: any
  is_final?: boolean
}

interface StreamProgress {
  sessionId: string
  status: 'idle' | 'processing' | 'completed' | 'failed'
  progress: number
  currentStage: string
  testCasesCount: number
}

interface TcStreamOutputProps {
  title?: string
  connected?: boolean
  progress?: StreamProgress | null
  streamContents?: Record<string, StreamContent>
  messages?: StreamMessage[]
  autoScroll?: boolean
  maxHeight?: string
}

interface TcStreamOutputEmits {
  (e: 'clear'): void
  (e: 'clear-streams'): void
  (e: 'stream-finish', source: string): void
  (e: 'toggle-panel', visible: boolean): void
}

const props = withDefaults(defineProps<TcStreamOutputProps>(), {
  title: '实时流式输出',
  connected: false,
  autoScroll: true,
  maxHeight: '400px',
  streamContents: () => ({}),
  messages: () => []
})

const emit = defineEmits<TcStreamOutputEmits>()

const showPanel = ref(true)
const streamsRef = ref<HTMLElement>()
const messagesRef = ref<HTMLElement>()

// 连接状态
const connectionStatus = computed(() => {
  if (props.connected) {
    return {
      type: 'success' as const,
      icon: 'Connection',
      text: '已连接'
    }
  } else if (props.progress?.status === 'failed') {
    return {
      type: 'danger' as const,
      icon: 'Close',
      text: '连接失败'
    }
  } else {
    return {
      type: 'info' as const,
      icon: 'Loading',
      text: '未连接'
    }
  }
})

// 进度状态
const progressStatus = computed(() => {
  if (!props.progress) return undefined
  
  switch (props.progress.status) {
    case 'completed':
      return 'success'
    case 'failed':
      return 'exception'
    case 'processing':
      return undefined
    default:
      return undefined
  }
})

// 是否有内容
const hasContent = computed(() => {
  return Object.keys(props.streamContents).length > 0 || props.messages.length > 0
})

// 切换面板显示
const togglePanel = () => {
  showPanel.value = !showPanel.value
  emit('toggle-panel', showPanel.value)
}

// 清空所有内容
const handleClear = () => {
  emit('clear')
}

// 清空流式内容
const clearAllStreams = () => {
  emit('clear-streams')
}

// 流式输出完成
const onStreamFinish = (source: string) => {
  emit('stream-finish', source)
}

// 获取消息标签类型
const getMessageTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    'progress': 'primary',
    'stage': 'info',
    'result': 'success',
    'complete': 'success',
    'completion': 'success',
    'final_result': 'success',
    'error': 'danger',
    'cancelled': 'warning',
    'message': 'info'
  }
  return typeMap[type] || 'info'
}

// 获取消息类型标签
const getMessageTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    'progress': '进度',
    'stage': '阶段',
    'result': '结果',
    'complete': '完成',
    'completion': '完成',
    'final_result': '最终结果',
    'error': '错误',
    'cancelled': '取消',
    'message': '消息'
  }
  return labelMap[type] || type
}

// 自动滚动到底部
const scrollToBottom = () => {
  if (!props.autoScroll) return
  
  nextTick(() => {
    if (streamsRef.value) {
      streamsRef.value.scrollTop = streamsRef.value.scrollHeight
    }
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

// 监听内容变化，自动滚动
watch(() => [props.streamContents, props.messages], scrollToBottom, { deep: true })
</script>

<style lang="scss" scoped>
.tc-stream-output {
  background: var(--bg-primary);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-md);
    border-bottom: 1px solid var(--border-color);
    background: var(--bg-secondary);

    .tc-stream-output__title {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      font-weight: var(--font-weight-semibold);
      color: var(--text-primary);

      .status-icon {
        margin-right: var(--spacing-xs);
      }
    }

    .tc-stream-output__actions {
      display: flex;
      gap: var(--spacing-xs);
    }
  }

  &__content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    padding: var(--spacing-md);
    gap: var(--spacing-md);
  }

  &__progress {
    .progress-info {
      margin-top: var(--spacing-sm);

      .current-stage {
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
        font-size: var(--font-size-sm);
        color: var(--text-primary);
        margin-bottom: var(--spacing-xs);

        .stage-icon {
          color: var(--primary-color);
        }
      }

      .test-cases-count {
        font-size: var(--font-size-xs);
        color: var(--success-color);
      }
    }
  }

  &__streams {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    .streams-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--spacing-sm);
      font-weight: var(--font-weight-medium);
      color: var(--text-primary);
    }

    .streams-content {
      flex: 1;
      overflow-y: auto;
      border: 1px solid var(--border-color);
      border-radius: var(--border-radius-md);
      background: var(--bg-tertiary);
      padding: var(--spacing-sm);

      .stream-containers {
        .stream-source-container {
          margin-bottom: var(--spacing-md);

          &:last-child {
            margin-bottom: 0;
          }

          // Ant Design X Bubble 组件样式覆盖
          :deep(.ant-bubble) {
            max-width: 100%;

            .ant-bubble-content {
              font-family: var(--font-family-mono);
              font-size: var(--font-size-sm);
              line-height: var(--line-height-relaxed);
              white-space: pre-wrap;
              word-wrap: break-word;
            }

            .ant-bubble-header {
              font-weight: var(--font-weight-semibold);
              color: var(--text-primary);
              margin-bottom: var(--spacing-xs);
            }
          }
        }
      }

      .empty-streams {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 200px;
        color: var(--text-secondary);
      }
    }
  }

  &__messages {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    .messages-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--spacing-sm);
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
      color: var(--text-primary);
    }

    .messages-content {
      flex: 1;
      overflow-y: auto;
      border: 1px solid var(--border-color);
      border-radius: var(--border-radius-md);
      padding: var(--spacing-sm);
      background: var(--bg-tertiary);

      .stream-message {
        margin-bottom: var(--spacing-sm);
        padding: var(--spacing-sm);
        border-radius: var(--border-radius-sm);
        background: var(--bg-primary);
        border-left: 3px solid var(--primary-color);

        &:last-child {
          margin-bottom: 0;
        }

        &.message-error {
          border-left-color: var(--error-color);
        }

        &.message-complete,
        &.message-completion,
        &.message-final_result {
          border-left-color: var(--success-color);
        }

        &.message-cancelled {
          border-left-color: var(--warning-color);
        }

        .message-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--spacing-xs);

          .message-time {
            font-size: var(--font-size-xs);
            color: var(--text-secondary);
            font-family: var(--font-family-mono);
          }
        }

        .message-content {
          font-size: var(--font-size-sm);
          color: var(--text-primary);
          line-height: var(--line-height-normal);
          word-break: break-word;
        }

        .message-result {
          margin-top: var(--spacing-xs);

          pre {
            font-size: var(--font-size-xs);
            color: var(--text-secondary);
            background: var(--bg-tertiary);
            padding: var(--spacing-xs);
            border-radius: var(--border-radius-sm);
            overflow-x: auto;
            max-height: 200px;
            overflow-y: auto;
          }
        }
      }

      .empty-messages {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 200px;
      }
    }
  }
}
</style>
