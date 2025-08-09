<template>
  <div class="session-detail">
    <div class="session-detail-header">
      <div class="header-info">
        <h3>
          <el-icon><Monitor /></el-icon>
          会话详情
        </h3>
        <p>查看会话的详细信息和处理日志</p>
      </div>
      <div class="header-actions">
        <el-button
          :icon="Refresh"
          @click="refreshSessionDetail"
          :loading="loading"
        >
          刷新
        </el-button>
        <el-button
          :icon="Close"
          @click="$emit('close')"
        >
          关闭
        </el-button>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else-if="sessionDetail" class="session-detail-content">
      <!-- 会话基本信息 -->
      <el-card class="session-info-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
            <el-tag
              :type="getStatusType(sessionDetail.status)"
              effect="light"
            >
              {{ getStatusText(sessionDetail.status) }}
            </el-tag>
          </div>
        </template>

        <div class="session-info-grid">
          <div class="info-item">
            <label>会话ID:</label>
            <span>{{ sessionDetail.session_id }}</span>
          </div>
          <div class="info-item">
            <label>输入类型:</label>
            <span>{{ getInputTypeText(sessionDetail.input_type) }}</span>
          </div>
          <div class="info-item">
            <label>当前阶段:</label>
            <span>{{ sessionDetail.current_stage || '未知' }}</span>
          </div>
          <div class="info-item">
            <label>进度:</label>
            <el-progress
              :percentage="sessionDetail.progress"
              :status="getProgressStatus(sessionDetail.status)"
              :stroke-width="6"
            />
          </div>
          <div class="info-item">
            <label>智能体:</label>
            <span>{{ sessionDetail.selected_agent || '未选择' }}</span>
          </div>
          <div class="info-item">
            <label>测试用例数:</label>
            <span>{{ sessionDetail.test_cases_count || 0 }}</span>
          </div>
          <div class="info-item">
            <label>创建时间:</label>
            <span>{{ formatTime(sessionDetail.created_at) }}</span>
          </div>
          <div class="info-item">
            <label>完成时间:</label>
            <span>{{ sessionDetail.completed_at ? formatTime(sessionDetail.completed_at) : '未完成' }}</span>
          </div>
        </div>

        <div v-if="sessionDetail.file_info" class="file-info">
          <h4>文件信息</h4>
          <div class="file-details">
            <div class="file-item">
              <label>文件名:</label>
              <span>{{ sessionDetail.file_info.name }}</span>
            </div>
            <div class="file-item">
              <label>文件大小:</label>
              <span>{{ sessionDetail.file_info.size_mb }}</span>
            </div>
            <div v-if="sessionDetail.file_info.description" class="file-item">
              <label>描述:</label>
              <span>{{ sessionDetail.file_info.description }}</span>
            </div>
          </div>
        </div>

        <div v-if="sessionDetail.error" class="error-info">
          <h4>错误信息</h4>
          <el-alert
            :title="sessionDetail.error"
            type="error"
            :closable="false"
            show-icon
          />
        </div>
      </el-card>

      <!-- 处理日志 -->
      <el-card class="session-logs-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>处理日志</span>
            <el-tag size="small" type="info">{{ sessionLogs.length }} 条日志</el-tag>
          </div>
        </template>

        <div class="logs-container">
          <div
            v-for="(log, index) in sessionLogs"
            :key="index"
            class="log-item"
            :class="`log-${log.type}`"
          >
            <div class="log-header">
              <el-tag
                :type="getLogTagType(log.type)"
                size="small"
              >
                {{ getLogTypeLabel(log.type) }}
              </el-tag>
              <span class="log-source">{{ log.source }}</span>
              <span class="log-time">{{ formatTime(log.timestamp) }}</span>
            </div>
            <div class="log-content">
              {{ log.content }}
            </div>
            <div v-if="log.result" class="log-result">
              <el-collapse>
                <el-collapse-item title="详细数据" name="result">
                  <pre>{{ JSON.stringify(log.result, null, 2) }}</pre>
                </el-collapse-item>
              </el-collapse>
            </div>
          </div>

          <div v-if="sessionLogs.length === 0" class="empty-logs">
            <el-empty description="暂无日志" :image-size="80" />
          </div>
        </div>
      </el-card>
    </div>

    <div v-else class="error-container">
      <el-result
        icon="error"
        title="加载失败"
        sub-title="无法获取会话详情，请稍后重试"
      >
        <template #extra>
          <el-button type="primary" @click="refreshSessionDetail">重新加载</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Monitor,
  Refresh,
  Close
} from '@element-plus/icons-vue'
import { testCaseGenerateApi } from '@/api/testCase'
import dayjs from 'dayjs'

interface Props {
  sessionId: string
}

interface SessionDetail {
  session_id: string
  status: string
  input_type: string
  file_info?: {
    name: string
    size_mb: string
    description?: string
  }
  progress: number
  current_stage: string
  selected_agent?: string
  test_cases_count: number
  created_at: string
  completed_at?: string
  error?: string
}

interface SessionLog {
  type: string
  source: string
  content: string
  timestamp: string
  result?: any
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const loading = ref(false)
const sessionDetail = ref<SessionDetail | null>(null)
const sessionLogs = ref<SessionLog[]>([])

// 获取会话详情
const getSessionDetail = async () => {
  if (!props.sessionId) {
    console.warn('SessionDetail: sessionId is empty')
    return
  }

  try {
    loading.value = true
    console.log('SessionDetail: 正在获取会话详情，sessionId:', props.sessionId)

    const response = await testCaseGenerateApi.getSessionStatus(props.sessionId)
    console.log('SessionDetail: 获取会话详情成功:', response)

    sessionDetail.value = response

    // 模拟一些日志数据，因为后端可能没有实现日志功能
    sessionLogs.value = [
      {
        type: 'stage',
        source: '系统',
        content: '会话已创建',
        timestamp: response.created_at,
        result: null
      },
      {
        type: 'progress',
        source: '处理引擎',
        content: `当前进度: ${response.progress}%`,
        timestamp: new Date().toISOString(),
        result: null
      }
    ]

    if (response.status === 'completed' && response.completed_at) {
      sessionLogs.value.push({
        type: 'complete',
        source: '系统',
        content: '会话处理完成',
        timestamp: response.completed_at,
        result: {
          test_cases_count: response.test_cases_count,
          processing_time: 'N/A'
        }
      })
    }

    if (response.error) {
      sessionLogs.value.push({
        type: 'error',
        source: '系统',
        content: response.error,
        timestamp: new Date().toISOString(),
        result: null
      })
    }

  } catch (error: any) {
    console.error('获取会话详情失败:', error)

    let errorMessage = '获取会话详情失败'
    if (error?.response?.status === 404) {
      errorMessage = '会话不存在或已过期'
    } else if (error?.response?.data?.detail) {
      errorMessage = error.response.data.detail
    } else if (error?.message) {
      errorMessage = error.message
    }

    ElMessage.error(errorMessage)
    sessionDetail.value = null
  } finally {
    loading.value = false
  }
}

// 刷新会话详情
const refreshSessionDetail = () => {
  getSessionDetail()
}

// 格式化时间
const formatTime = (timestamp: string) => {
  return dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss')
}

// 获取状态类型
const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    'created': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'cancelled': 'info'
  }
  return statusMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'created': '已创建',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

// 获取输入类型文本
const getInputTypeText = (inputType: string) => {
  const typeMap: Record<string, string> = {
    'file': '文件上传',
    'text': '文本输入'
  }
  return typeMap[inputType] || inputType
}

// 获取进度状态
const getProgressStatus = (status: string) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return undefined
}

// 获取日志标签类型
const getLogTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    'progress': 'primary',
    'stage': 'info',
    'result': 'success',
    'complete': 'success',
    'completion': 'success',
    'error': 'danger',
    'cancelled': 'warning',
    'message': 'info'
  }
  return typeMap[type] || 'info'
}

// 获取日志类型标签
const getLogTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    'progress': '进度',
    'stage': '阶段',
    'result': '结果',
    'complete': '完成',
    'completion': '完成',
    'error': '错误',
    'cancelled': '取消',
    'message': '消息'
  }
  return labelMap[type] || type
}

// 监听sessionId变化
watch(() => props.sessionId, (newSessionId) => {
  if (newSessionId) {
    getSessionDetail()
  }
}, { immediate: true })

onMounted(() => {
  if (props.sessionId) {
    getSessionDetail()
  }
})
</script>

<style lang="scss" scoped>
.session-detail {
  .session-detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
    padding: var(--spacing-md);
    background: var(--bg-secondary);
    border-radius: var(--border-radius-lg);

    .header-info {
      h3 {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        margin: 0 0 var(--spacing-xs) 0;
        font-size: 18px;
        font-weight: 600;
        color: var(--text-primary);

        .el-icon {
          color: var(--primary-color);
        }
      }

      p {
        margin: 0;
        color: var(--text-secondary);
        font-size: 14px;
      }
    }

    .header-actions {
      display: flex;
      gap: var(--spacing-sm);
    }
  }

  .loading-container {
    padding: var(--spacing-xl);
  }

  .session-detail-content {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);

    .session-info-card,
    .session-logs-card {
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: 600;
        color: var(--text-primary);
      }
    }

    .session-info-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: var(--spacing-md);
      margin-bottom: var(--spacing-lg);

      .info-item {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-xs);

        label {
          font-weight: 500;
          color: var(--text-secondary);
          font-size: 14px;
        }

        span {
          color: var(--text-primary);
          font-size: 14px;
        }
      }
    }

    .file-info,
    .error-info {
      margin-top: var(--spacing-lg);
      padding-top: var(--spacing-lg);
      border-top: 1px solid var(--border-color-light);

      h4 {
        margin: 0 0 var(--spacing-md) 0;
        font-size: 16px;
        font-weight: 600;
        color: var(--text-primary);
      }

      .file-details {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-sm);

        .file-item {
          display: flex;
          gap: var(--spacing-md);

          label {
            font-weight: 500;
            color: var(--text-secondary);
            min-width: 80px;
          }

          span {
            color: var(--text-primary);
          }
        }
      }
    }

    .logs-container {
      max-height: 400px;
      overflow-y: auto;

      .log-item {
        padding: var(--spacing-md);
        margin-bottom: var(--spacing-sm);
        border-radius: var(--border-radius-md);
        border: 1px solid var(--border-color-light);
        background: var(--bg-tertiary);

        &:last-child {
          margin-bottom: 0;
        }

        .log-header {
          display: flex;
          align-items: center;
          gap: var(--spacing-md);
          margin-bottom: var(--spacing-sm);

          .log-source {
            font-weight: 500;
            color: var(--text-primary);
          }

          .log-time {
            margin-left: auto;
            font-size: 12px;
            color: var(--text-secondary);
          }
        }

        .log-content {
          color: var(--text-primary);
          line-height: 1.6;
          white-space: pre-wrap;
          word-wrap: break-word;
        }

        .log-result {
          margin-top: var(--spacing-sm);

          pre {
            background: var(--bg-secondary);
            padding: var(--spacing-sm);
            border-radius: var(--border-radius-sm);
            font-size: 12px;
            line-height: 1.4;
            overflow-x: auto;
          }
        }
      }

      .empty-logs {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 200px;
      }
    }
  }

  .error-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 300px;
  }
}
</style>
