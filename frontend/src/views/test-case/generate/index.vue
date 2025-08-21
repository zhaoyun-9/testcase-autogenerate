<template>
  <div class="test-case-generate">
    <div class="page-container" :class="{ 'with-stream-panel': showStreamOutput }">
      <div class="content-wrapper">
        <div class="main-content">
        <!-- 左侧主要内容区域 -->
        <div class="left-content">
        <!-- 智能生成配置 -->
        <TcCard class="generation-card">
          <template #header>
            <div class="generation-header">
              <div class="header-left">
                <div class="header-info">
                  <h3>
                    <el-icon><MagicStick /></el-icon>
                    智能测试用例生成
                  </h3>
                  <p>配置AI参数并选择输入方式，一键生成专业测试用例</p>
                </div>
              </div>

              <div class="header-center">
                <!-- 快速统计 -->
                <div class="quick-stats">
                  <div class="stat-item">
                    <el-icon class="stat-icon"><Document /></el-icon>
                    <div class="stat-content">
                      <span class="stat-value">{{ generatedTestCases.length }}</span>
                      <span class="stat-label">已生成</span>
                    </div>
                  </div>
                  <div class="stat-divider"></div>
                  <div class="stat-item">
                    <el-icon class="stat-icon"><Clock /></el-icon>
                    <div class="stat-content">
                      <span class="stat-value">{{ sessionDuration }}</span>
                      <span class="stat-label">耗时</span>
                    </div>
                  </div>
                  <div class="stat-divider"></div>
                  <div class="stat-item">
                    <el-icon class="stat-icon" :class="{ 'status-active': streamConnected }"><Monitor /></el-icon>
                    <div class="stat-content">
                      <span class="stat-value">{{ streamConnected ? '连接' : '断开' }}</span>
                      <span class="stat-label">状态</span>
                    </div>
                  </div>
                </div>
              </div>

              <div class="header-right">
                <!-- AI驱动标签和快速操作 -->
                <div class="header-actions">
                  <el-tag type="primary" effect="light" size="small">
                    <el-icon><Setting /></el-icon>
                    AI驱动
                  </el-tag>

                  <div class="quick-actions">
                    <el-tooltip content="切换流式输出面板" placement="bottom">
                      <el-button
                        :type="showStreamOutput ? 'primary' : 'default'"
                        :icon="Monitor"
                        circle
                        size="small"
                        @click="showStreamOutput = !showStreamOutput"
                      />
                    </el-tooltip>
                    <el-tooltip content="导出Excel" placement="bottom">
                      <el-button
                        :icon="Download"
                        circle
                        size="small"
                        :disabled="generatedTestCases.length === 0"
                        @click="exportToExcel"
                      />
                    </el-tooltip>
                    <el-tooltip content="查看思维导图" placement="bottom">
                      <el-button
                        :icon="Share"
                        circle
                        size="small"
                        :disabled="!currentSession"
                        @click="viewMindmap"
                      />
                    </el-tooltip>
                  </div>
                </div>
              </div>
            </div>
          </template>

          <div class="generation-content">
            <!-- 配置区域 -->
            <div class="config-section">
              <div class="section-title">
                <el-icon><Setting /></el-icon>
                生成配置
              </div>
              <el-form
                ref="configFormRef"
                :model="generateConfig"
                :rules="configRules"
                :inline="true"
                class="config-form"
              >
                <el-form-item label="目标项目" prop="projectId">
                  <el-select
                    v-model="generateConfig.projectId"
                    placeholder="请选择项目"
                    style="width: 200px"
                    :loading="loadingProjects"
                    clearable
                    filterable
                  >
                    <el-option
                      v-for="project in projects"
                      :key="project.id"
                      :label="project.name"
                      :value="project.id"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item label="输入类型" prop="inputType">
                  <el-select v-model="generateConfig.inputType" placeholder="请选择输入类型" style="width: 140px">
                    <el-option label="文件上传" value="file" />
                    <el-option label="文本输入" value="text" />
                  </el-select>
                </el-form-item>

                <el-form-item label="生成模式" prop="mode">
                  <el-select v-model="generateConfig.mode" placeholder="请选择生成模式" style="width: 140px">
                    <el-option label="标准模式" value="standard" />
                    <el-option label="详细模式" value="detailed" />
                    <el-option label="简洁模式" value="simple" />
                  </el-select>
                </el-form-item>

                <el-form-item label="测试类型" prop="testType">
                  <el-select v-model="generateConfig.testType" placeholder="请选择测试类型" style="width: 140px">
                    <el-option label="功能测试" value="functional" />
                    <el-option label="接口测试" value="api" />
                    <el-option label="性能测试" value="performance" />
                  </el-select>
                </el-form-item>
              </el-form>
            </div>

            <!-- 分隔线 -->
            <el-divider />

            <!-- 输入区域 -->
            <div class="input-section">
              <div class="section-title">
                <el-icon>
                  <component :is="generateConfig.inputType === 'file' ? 'Upload' : 'EditPen'" />
                </el-icon>
                {{ generateConfig.inputType === 'file' ? '智能文件解析' : '需求文本分析' }}
                <el-tag
                  :type="generateConfig.inputType === 'file' ? 'primary' : 'success'"
                  effect="light"
                  size="small"
                >
                  {{ generateConfig.inputType === 'file' ? 'AI识别' : '语义理解' }}
                </el-tag>
              </div>

              <!-- 文件上传模式 -->
              <div v-if="generateConfig.inputType === 'file'" class="file-input-section">
                <FileUpload
                  ref="fileUploadRef"
                  :multiple="true"
                  :max-size="500"
                  :max-count="10"
                  accepted-types=".pdf,.doc,.docx,.txt,.md,.png,.jpg,.jpeg,.json,.yaml,.yml,.mp4,.avi,.mov,.wmv,.flv,.webm"
                  @change="handleFileChange"
                  @upload-success="handleFileUploadSuccess"
                  @upload-error="handleFileUploadError"
                />
              </div>

              <!-- 文本输入模式 -->
              <div v-else class="text-input-section">
                <el-input
                  v-model="generateConfig.requirementText"
                  type="textarea"
                  :rows="6"
                  placeholder="请输入详细的需求描述，包括功能说明、业务流程、预期行为等..."
                  show-word-limit
                  :maxlength="5000"
                  class="requirement-input"
                />
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="action-section">
              <div class="action-buttons">
                <TcButton
                  type="primary"
                  size="large"
                  :loading="generating"
                  :disabled="!canGenerate"
                  gradient
                  shadow
                  class="generate-btn"
                  @click="startGeneration"
                >
                  <template #icon>
                    <el-icon><MagicStick /></el-icon>
                  </template>
                  {{ generating ? 'AI正在分析...' : '开始智能生成' }}
                </TcButton>

                <TcButton
                  v-if="currentSession"
                  size="large"
                  class="reset-btn"
                  @click="resetGeneration"
                >
                  <template #icon>
                    <el-icon><Refresh /></el-icon>
                  </template>
                  重新开始
                </TcButton>
              </div>

              <div v-if="!canGenerate" class="action-hint">
                <el-icon><InfoFilled /></el-icon>
                <span>
                  请先
                  <template v-if="!generateConfig.projectId">选择项目</template>
                  <template v-else-if="generateConfig.inputType === 'file'">上传文件</template>
                  <template v-else>输入需求描述</template>
                  后开始生成
                </span>
              </div>
            </div>
          </div>
        </TcCard>



        <!-- 进度监控 -->
        <div v-if="currentSession" class="progress-section">
          <ProgressMonitor
            :key="currentSession.sessionId"
            :session-id="currentSession.sessionId"
            :progress="sessionProgress"
            :connected="streamConnected"
            :auto-connect="true"
            @connected="handleProgressConnected"
            @progress="handleProgressUpdate"
            @completed="handleGenerationCompleted"
            @failed="handleGenerationFailed"
            @cancel="handleCancelGeneration"
            @retry="handleRetryGeneration"
            @message="handleStreamMessage"
          />
        </div>

        <!-- 生成结果 -->
        <div v-if="generatedTestCases.length > 0" class="results-section">
          <TcCard class="results-card">
            <template #header>
              <div class="results-header">
                <div class="header-info">
                  <h3>生成结果</h3>
                  <p>共生成 {{ generatedTestCases.length }} 个测试用例</p>
                </div>
                <div class="header-actions">
                  <TcButton
                    type="primary"
                    size="small"
                    :loading="exporting"
                    @click="exportToExcel"
                  >
                    <template #icon>
                      <el-icon><Download /></el-icon>
                    </template>
                    导出Excel
                  </TcButton>

                  <TcButton
                    v-if="generateConfig.generateMindMap"
                    type="success"
                    size="small"
                    @click="viewMindmap"
                  >
                    <template #icon>
                      <el-icon><Share /></el-icon>
                    </template>
                    查看思维导图
                  </TcButton>
                </div>
              </div>
            </template>

            <el-card
              v-for="testCase in generatedTestCases"
              :key="testCase.id"
              class="test-case-card"
              shadow="hover"
            >
              <template #header>
                <div class="card-header">
                  <span>{{ testCase.title || testCase.name }}</span>
                  <div class="card-actions">
                    <el-button size="small" @click="handleViewTestCase(testCase)">查看</el-button>
                    <el-button size="small" @click="handleEditTestCase(testCase)">编辑</el-button>
                    <el-button size="small" @click="handleCopyTestCase(testCase)">复制</el-button>
                    <el-button size="small" type="danger" @click="handleDeleteTestCase(testCase)">删除</el-button>
                  </div>
                </div>
              </template>
              <div class="test-case-content">
                <p><strong>描述:</strong> {{ testCase.description }}</p>
                <p><strong>优先级:</strong> {{ testCase.priority }}</p>
                <p><strong>状态:</strong> {{ testCase.status }}</p>
              </div>
            </el-card>
          </TcCard>
        </div>
        <!-- 左侧内容区域结束 -->
      </div>
      <!-- left-content 结束 -->


    </div>
    <!-- main-content 结束 -->

    <!-- 右侧智能体日志面板 -->
    <div v-if="showStreamOutput" class="stream-panel">
      <!-- 智能体日志主面板 -->
      <div class="agent-logs-main-panel">
        <div class="panel-header">
          <div class="panel-title">
            <el-icon><Document /></el-icon>
            <span>智能体处理日志</span>
            <el-badge v-if="agentLogsSummary" :value="agentLogsSummary.total_messages" :max="99" type="primary" />
          </div>
          <div class="panel-actions">
            <el-tooltip content="刷新日志和状态" placement="bottom">
              <el-button
                :icon="Refresh"
                text
                size="small"
                :loading="loadingAgentLogs"
                @click="refreshCurrentSession"
              />
            </el-tooltip>
            <el-tooltip content="关闭面板" placement="bottom">
              <el-button
                :icon="Close"
                text
                size="small"
                @click="closeAgentLogs"
              />
            </el-tooltip>
          </div>
        </div>

        <!-- 会话选择器 -->
        <div class="session-selector">
          <el-select
            v-model="selectedSessionId"
            placeholder="选择会话查看智能体日志"
            style="width: 100%"
            @change="handleSessionChange"
            clearable
          >
            <el-option
              v-for="session in activeSessions"
              :key="session.sessionId"
              :label="getSessionDisplayName(session)"
              :value="session.sessionId"
            >
              <div class="session-option">
                <div class="session-info">
                  <span class="session-name">{{ getSessionDisplayName(session) }}</span>
                  <el-tag
                    :type="getSessionStatusType(session.status)"
                    size="small"
                    effect="plain"
                  >
                    {{ getSessionStatusText(session.status) }}
                  </el-tag>
                </div>
                <div class="session-time">{{ formatSessionTime(session.createdAt) }}</div>
              </div>
            </el-option>
          </el-select>
        </div>

        <!-- 日志摘要统计 -->
        <div v-if="agentLogsSummary" class="logs-summary">
          <div class="summary-stats-horizontal">
            <span class="stat-text">总消息数：{{ agentLogsSummary.total_messages }}</span>
            <span class="stat-divider">|</span>
            <span class="stat-text">智能体数：{{ Object.keys(agentLogsSummary.agents).length }}</span>
            <span class="stat-divider">|</span>
            <span class="stat-text">错误数：{{ agentLogsSummary.errors.length }}</span>
          </div>
        </div>

        <!-- 智能体日志列表区域 -->
        <div class="agent-logs-content" v-if="selectedSessionId">
          <!-- 日志列表 -->
          <div class="logs-container" v-loading="loadingAgentLogs">
            <div v-if="agentLogs.length === 0 && !loadingAgentLogs" class="empty-logs">
              <el-empty
                description="暂无智能体日志"
                :image-size="60"
              >
                <template #image>
                  <el-icon size="60" color="#c0c4cc">
                    <Document />
                  </el-icon>
                </template>
              </el-empty>
            </div>

            <div v-else-if="agentLogs.length > 0" class="logs-list">
              <!-- 调试信息 -->
              <div class="debug-info" style="margin-bottom: 10px; padding: 10px; background: #f0f9ff; border-radius: 4px; font-size: 12px; color: #666;">
                📊 共 {{ agentLogs.length }} 条日志 | 会话ID: {{ selectedSessionId }}
              </div>

              <div
                v-for="(log, index) in agentLogs"
                :key="log.id || index"
                class="log-item"
                :class="`log-${log.message_type}`"
              >
                <div class="log-header">
                  <div class="log-meta">
                    <el-tag
                      :type="getLogTypeColor(log.message_type)"
                      size="small"
                      effect="light"
                    >
                      {{ log.agent_name || '未知智能体' }}
                    </el-tag>
                    <el-tag
                      :type="getMessageTypeColor(log.message_type)"
                      size="small"
                      effect="plain"
                    >
                      {{ getMessageTypeLabel(log.message_type) }}
                    </el-tag>
                    <span class="log-time">{{ formatLogTime(log.timestamp) }}</span>
                  </div>
                  <div class="log-stage" v-if="log.processing_stage">
                    <el-tag size="small" type="info" effect="plain">
                      {{ log.processing_stage }}
                    </el-tag>
                  </div>
                </div>

                <div class="log-content">
                  <div class="content-text">{{ log.content || '无内容' }}</div>

                  <!-- 结果数据 -->
                  <div v-if="log.result_data" class="result-data">
                    <el-collapse>
                      <el-collapse-item title="结果数据" name="result">
                        <pre>{{ JSON.stringify(log.result_data, null, 2) }}</pre>
                      </el-collapse-item>
                    </el-collapse>
                  </div>

                  <!-- 错误信息 -->
                  <div v-if="log.error_info" class="error-info">
                    <el-alert
                      :title="log.error_info.message || '处理错误'"
                      type="error"
                      :closable="false"
                      show-icon
                    >
                      <template v-if="log.error_info.details">
                        <pre>{{ log.error_info.details }}</pre>
                      </template>
                    </el-alert>
                  </div>

                  <!-- 性能指标 -->
                  <div v-if="log.metrics_data" class="metrics-data">
                    <el-descriptions :column="3" size="small" border>
                      <el-descriptions-item
                        v-for="(value, key) in log.metrics_data"
                        :key="key"
                        :label="key"
                      >
                        {{ value }}
                      </el-descriptions-item>
                    </el-descriptions>
                  </div>
                </div>
              </div>
            </div>

            <!-- 加载状态但有数据的情况 -->
            <div v-else-if="loadingAgentLogs" class="loading-logs">
              <div style="text-align: center; padding: 20px; color: #909399;">
                <el-icon class="is-loading"><Loading /></el-icon>
                正在加载智能体日志...
              </div>
            </div>
          </div>
        </div>
        <!-- agent-logs-content 结束 -->

        <!-- 默认提示区域 -->
        <div v-else class="default-hint">
          <el-empty
            description="请点击上方文件名查看对应的智能体日志"
            :image-size="80"
          >
            <template #image>
              <el-icon size="80" color="#c0c4cc">
                <Document />
              </el-icon>
            </template>
          </el-empty>
        </div>
      </div>
      <!-- agent-logs-main-panel 结束 -->
    </div>
    <!-- stream-panel 结束 -->

    </div>
    <!-- content-wrapper 结束 -->

    <!-- 会话详情弹窗 -->
    <el-dialog
      v-model="showSessionDetail"
      title="会话详情"
      width="80%"
      :before-close="handleCloseSessionDetail"
      destroy-on-close
    >
      <SessionDetail
        v-if="selectedSessionForDetail"
        :session-id="selectedSessionForDetail"
        @close="handleCloseSessionDetail"
      />
    </el-dialog>
    </div>
    <!-- page-container 结束 -->
  </div>
  <!-- test-case-generate 结束 -->
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Setting,
  Upload,
  EditPen,
  MagicStick,
  Refresh,
  InfoFilled,
  Download,
  Share,
  Document,
  Clock,
  Monitor,
  Delete,
  Close,
  View,
  FolderOpened,
  Picture,
  VideoPlay
} from '@element-plus/icons-vue'

import {
  TcPageHeader,
  TcCard,
  TcButton,
  TcStreamOutput
} from '@/components/ui'

import { useTestCaseStore } from '@/stores/testCase'
import { testCaseGenerateApi, exportApi } from '@/api/testCase'
import { projectApi } from '@/api/project'
import FileUpload from '@/components/FileUpload/index.vue'
import ProgressMonitor from '@/components/ProgressMonitor/index.vue'
import TestCaseList from '@/components/TestCaseList/index.vue'
import SessionDetail from '@/components/SessionDetail/index.vue'
import {
  TestCaseGenerationFlow,
  FileTypeDetector,
  GenerationConfigValidator
} from '@/utils/testFlow'
import type {
  GenerateRequest,
  TestCaseSession,
  TestCase,
  GenerationProgress,
  SSEMessage
} from '@/types/testCase'
import type { Project } from '@/api/project'
import dayjs from 'dayjs'

const router = useRouter()
const testCaseStore = useTestCaseStore()

const configFormRef = ref()
const fileUploadRef = ref()
const streamMessagesRef = ref<HTMLElement>()
const streamTextRef = ref<HTMLElement>()
const generating = ref(false)
const exporting = ref(false)
const currentSession = ref<TestCaseSession | null>(null)
const generatedTestCases = ref<TestCase[]>([])
const selectedTestCases = ref<string[]>([])

// 生成流程管理器
const generationFlow = ref<TestCaseGenerationFlow | null>(null)

// 会话管理相关状态
const activeSessions = ref<TestCaseSession[]>([])
const selectedSessionId = ref<string>('')
const showSessionDetail = ref(false)
const selectedSessionForDetail = ref<string>('')

// 流式输出相关状态
const showStreamOutput = ref(false)
const streamMessages = ref<SSEMessage[]>([])
const sessionProgress = ref<GenerationProgress>({
  sessionId: '',
  status: 'idle',
  progress: 0,
  currentStage: '',
  testCasesCount: 0
})
const streamConnected = ref(false)
const sessionStartTime = ref<Date | null>(null)

// 智能体日志相关状态
const agentLogs = ref<any[]>([])
const agentLogsSummary = ref<any>(null)
const loadingAgentLogs = ref(false)

// 流式文本累积显示状态 - 按source分组
const streamContents = ref<Record<string, {
  text: string
  typing: boolean | { step?: number, interval?: number }
  status: 'loading' | 'success' | 'error'
}>>({})

// 生成配置
const generateConfig = reactive<GenerateRequest & { inputType: 'file' | 'text' }>({
  inputType: 'file',
  requirementText: '',
  analysisTarget: '生成测试用例',
  generateMindMap: true,
  exportExcel: false,
  maxTestCases: undefined,
  tags: [],
  projectId: undefined
})

// 项目相关数据
const projects = ref<Project[]>([])
const loadingProjects = ref(false)

// 常用标签
const commonTags = [
  '功能测试', '接口测试', '性能测试', '安全测试',
  '兼容性测试', '易用性测试', '回归测试', '冒烟测试'
]

// 计算属性
const sessionDuration = computed(() => {
  if (!sessionStartTime.value) return '0s'
  const now = new Date()
  const diff = Math.floor((now.getTime() - sessionStartTime.value.getTime()) / 1000)
  if (diff < 60) return `${diff}s`
  const minutes = Math.floor(diff / 60)
  const seconds = diff % 60
  return `${minutes}m ${seconds}s`
})

// 页面头部操作配置
const headerActions = computed(() => [
  {
    type: 'button' as const,
    label: showStreamOutput.value ? '隐藏流式输出' : '显示流式输出',
    buttonType: 'primary' as const,
    icon: showStreamOutput.value ? 'Hide' : 'View',
    handler: toggleStreamOutput
  },
  {
    type: 'dropdown' as const,
    label: '更多操作',
    items: [
      {
        label: '重置配置',
        command: 'reset-config',
        icon: 'Refresh'
      },
      {
        label: '保存配置',
        command: 'save-config',
        icon: 'Document'
      }
    ],
    handler: handleMoreAction
  }
])

// 配置表单项
const configFormItems = computed(() => [
  {
    prop: 'projectId',
    label: '目标项目',
    type: 'select' as const,
    placeholder: '请选择项目',
    options: projects.value.map(project => ({
      label: project.name,
      value: project.id
    })),
    span: 12,
    componentProps: {
      loading: loadingProjects.value,
      clearable: true,
      filterable: true
    }
  },
  {
    prop: 'inputType',
    label: '输入方式',
    type: 'radio' as const,
    options: [
      { label: '文件上传', value: 'file' },
      { label: '文本输入', value: 'text' }
    ],
    span: 12
  },
  {
    prop: 'analysisTarget',
    label: '分析目标',
    type: 'input' as const,
    placeholder: '请输入分析目标，如：生成功能测试用例',
    span: 12
  },
  {
    prop: 'maxTestCases',
    label: '最大用例数',
    type: 'number' as const,
    placeholder: '不限制',
    span: 12,
    componentProps: {
      min: 1,
      max: 100
    }
  },
  {
    prop: 'tags',
    label: '标签',
    type: 'select' as const,
    multiple: true,
    filterable: true,
    options: commonTags.map(tag => ({ label: tag, value: tag })),
    placeholder: '选择或输入标签',
    span: 12
  },
  {
    prop: 'generateMindMap',
    label: '生成思维导图',
    type: 'checkbox' as const,
    span: 12
  },
  {
    prop: 'exportExcel',
    label: '自动导出Excel',
    type: 'checkbox' as const,
    span: 12
  }
])

const handleMoreAction = (command: string) => {
  switch (command) {
    case 'reset-config':
      resetConfig()
      break
    case 'save-config':
      saveConfig()
      break
  }
}

const resetConfig = () => {
  Object.assign(generateConfig, {
    inputType: 'file',
    requirementText: '',
    analysisTarget: '生成测试用例',
    generateMindMap: true,
    exportExcel: false,
    maxTestCases: undefined,
    tags: []
  })
  ElMessage.success('配置已重置')
}

const saveConfig = () => {
  // TODO: 实现配置保存
  ElMessage.success('配置已保存')
}

const handleFileUploadSuccess = (response: any) => {
  ElMessage.success('文件上传成功')
}

const handleFileUploadError = (error: any) => {
  ElMessage.error('文件上传失败')
}

const handleClearStreamOutput = () => {
  streamMessages.value = []
  streamContents.value = {}
}

const handleClearStreams = () => {
  streamContents.value = {}
}

const handleStreamFinish = (source: string) => {
  if (streamContents.value[source]) {
    streamContents.value[source].typing = false
    streamContents.value[source].status = 'success'
  }
}

const handleToggleStreamPanel = (visible: boolean) => {
  showStreamOutput.value = visible
}

const handleViewTestCase = (testCase: TestCase) => {
  // TODO: 实现测试用例查看
}

const handleCopyTestCase = (testCase: TestCase) => {
  // TODO: 实现测试用例复制
}

// 表单验证规则
const configRules = {
  projectId: [
    { required: true, message: '请选择目标项目', trigger: 'change' }
  ],
  analysisTarget: [
    { required: true, message: '请输入分析目标', trigger: 'blur' }
  ],
  requirementText: [
    {
      required: true,
      message: '请输入需求描述',
      trigger: 'blur',
      validator: (rule: any, value: string, callback: Function) => {
        if (generateConfig.inputType === 'text' && !value?.trim()) {
          callback(new Error('请输入需求描述'))
        } else {
          callback()
        }
      }
    }
  ]
}

// 是否可以开始生成
const canGenerate = computed(() => {
  if (generating.value) return false

  // 必须选择项目
  if (!generateConfig.projectId) return false

  if (generateConfig.inputType === 'file') {
    return fileUploadRef.value?.getFiles()?.length > 0
  } else {
    return generateConfig.requirementText?.trim().length > 0
  }
})

// 加载项目列表
const loadProjects = async () => {
  loadingProjects.value = true
  try {
    const response = await projectApi.getProjects({
      page: 1,
      page_size: 100,
      status: 'active'
    })
    projects.value = response.items

    // 如果只有一个项目，自动选择
    if (projects.value.length === 1) {
      generateConfig.projectId = projects.value[0].id
    }
  } catch (error) {
    console.error('加载项目列表失败:', error)
    ElMessage.error('加载项目列表失败')
  } finally {
    loadingProjects.value = false
  }
}

// 处理文件变化
const handleFileChange = (files: any[], description?: string) => {
  console.log('文件变化:', files, description)

  // 更新文件信息到配置中
  if (files.length > 0) {
    // 使用文件类型检测器分析文件
    const firstFile = files[0]
    const fileAnalysis = FileTypeDetector.detectFileType(firstFile.file)

    // 自动设置分析目标
    if (!generateConfig.analysisTarget || generateConfig.analysisTarget === '生成测试用例') {
      switch (fileAnalysis.category) {
        case 'image':
          generateConfig.analysisTarget = '分析界面截图，生成UI测试用例'
          break
        case 'document':
          generateConfig.analysisTarget = '分析需求文档，生成功能测试用例'
          break
        case 'api_spec':
          generateConfig.analysisTarget = '分析API接口规范，生成接口测试用例'
          break
        case 'database':
          generateConfig.analysisTarget = '分析数据库结构，生成数据测试用例'
          break
        case 'video':
          generateConfig.analysisTarget = '分析操作录屏，生成操作流程测试用例'
          break
        default:
          generateConfig.analysisTarget = '智能分析文件内容，生成测试用例'
      }
    }

    // 根据文件类型自动设置标签
    const autoTags = []
    switch (fileAnalysis.category) {
      case 'image':
        autoTags.push('UI测试', '界面测试')
        break
      case 'document':
        autoTags.push('功能测试', '需求测试')
        break
      case 'api_spec':
        autoTags.push('接口测试', 'API测试')
        break
      case 'database':
        autoTags.push('数据测试', '数据库测试')
        break
      case 'video':
        autoTags.push('流程测试', '操作测试')
        break
    }

    // 合并自动标签和用户选择的标签
    generateConfig.tags = [...new Set([...generateConfig.tags, ...autoTags])]

    console.log('文件分析结果:', fileAnalysis)
  }
}

// 开始生成
const startGeneration = async () => {
  try {
    // 表单验证
    await configFormRef.value?.validate()

    // 获取文件列表
    const files = generateConfig.inputType === 'file'
      ? fileUploadRef.value?.getFiles()?.map((f: any) => f.file) || []
      : []

    // 验证配置
    const validation = GenerationConfigValidator.validate(generateConfig, files)
    if (!validation.isValid) {
      ElMessage.error(validation.errors[0])
      return
    }

    generating.value = true

    // 创建生成流程管理器
    generationFlow.value = new TestCaseGenerationFlow({
      onProgress: (progress) => {
        console.log('生成进度:', progress)
        // 这里可以更新UI进度显示
      },
      onComplete: (result) => {
        console.log('生成完成:', result)
        handleGenerationCompleted(result)
      },
      onError: (error) => {
        console.error('生成失败:', error)
        ElMessage.error(error)
        generating.value = false
      }
    })

    // 清空之前的流式输出内容
    clearAllStreams()
    clearStreamLogs()

    // 启动生成流程
    const session = await generationFlow.value.startGeneration(generateConfig, files)

    // 使用nextTick确保状态更新的安全性
    await nextTick()

    currentSession.value = session
    testCaseStore.setCurrentSession(currentSession.value)

    // 将新会话添加到活动会话列表
    const existingSessionIndex = activeSessions.value.findIndex(s => s.sessionId === session.sessionId)
    if (existingSessionIndex >= 0) {
      // 更新现有会话
      activeSessions.value[existingSessionIndex] = session
    } else {
      // 添加新会话到列表开头
      activeSessions.value.unshift(session)
    }

    // 选择当前会话
    selectedSessionId.value = session.sessionId

    // 自动显示流式输出面板
    await nextTick()
    if (!showStreamOutput.value) {
      showStreamOutput.value = true
      console.log('自动显示流式输出面板')
    }

    // 注意：不在这里立即加载智能体日志，因为SSE连接会在TestCaseGenerationFlow内部处理
    // 等待一段时间后再加载智能体日志，确保后端已经开始处理
    setTimeout(async () => {
      try {
        await loadSessionAgentLogs(session.sessionId)
        console.log('延迟加载智能体日志成功:', session.sessionId)
      } catch (error) {
        console.log('延迟加载智能体日志失败，这是正常的，会话可能还在启动中')
      }
    }, 3000) // 3秒后尝试加载

    console.log('生成流程启动完成，SSE连接将在内部处理')

  } catch (error: any) {
    console.error('启动生成失败:', error)
    ElMessage.error(error.message || '启动生成失败')

    // 重置状态
    if (currentSession.value) {
      currentSession.value.status = 'failed'
    }
  } finally {
    generating.value = false
  }
}

// 上传文件
const uploadFiles = async () => {
  if (!currentSession.value) return

  const files = fileUploadRef.value?.getFiles() || []
  const description = fileUploadRef.value?.getDescription()

  if (files.length === 0) {
    throw new Error('请先选择要上传的文件')
  }

  try {
    // 更新会话状态
    currentSession.value.status = 'uploading'

    // 逐个上传文件
    for (let i = 0; i < files.length; i++) {
      const fileItem = files[i]

      ElMessage.info(`正在上传文件 ${i + 1}/${files.length}: ${fileItem.name}`)

      const uploadResult = await testCaseGenerateApi.uploadFile(
        currentSession.value.sessionId,
        fileItem.file,
        description
      )

      console.log(`文件上传成功:`, uploadResult)
    }

    // 所有文件上传完成
    currentSession.value.status = 'processing'
    ElMessage.success(`所有文件上传完成，开始智能分析...`)

  } catch (error: any) {
    console.error('文件上传失败:', error)
    currentSession.value.status = 'failed'
    throw new Error(error.message || '文件上传失败')
  }
}

// 重置生成
const resetGeneration = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重新开始吗？当前进度将会丢失。',
      '确认重置',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    currentSession.value = null
    generatedTestCases.value = []
    selectedTestCases.value = []
    testCaseStore.reset()
    
  } catch {
    // 用户取消
  }
}

// 流式输出相关函数
const toggleStreamOutput = () => {
  showStreamOutput.value = !showStreamOutput.value
  console.log('切换流式输出面板:', showStreamOutput.value)
  console.log('当前会话:', currentSession.value)

  // 强制触发DOM更新
  nextTick(() => {
    console.log('DOM更新完成，面板状态:', showStreamOutput.value)
    const panel = document.querySelector('.stream-output-panel')
    console.log('面板元素:', panel)

    if (showStreamOutput.value && currentSession.value) {
      // 显示时自动滚动到底部
      scrollStreamToBottom()
    }
  })
}

const clearStreamLogs = () => {
  streamMessages.value = []
}

const clearAllStreams = () => {
  streamContents.value = {}
}

const clearStreamBySource = (source: string) => {
  delete streamContents.value[source]
}

const onStreamFinish = (source: string) => {
  if (streamContents.value[source]) {
    streamContents.value[source].status = 'success'
  }
}

const scrollStreamToBottom = () => {
  if (streamMessagesRef.value) {
    streamMessagesRef.value.scrollTop = streamMessagesRef.value.scrollHeight
  }
}

const scrollStreamTextToBottom = () => {
  if (streamTextRef.value) {
    streamTextRef.value.scrollTop = streamTextRef.value.scrollHeight
  }
}

const formatStreamTime = (timestamp: string) => {
  return dayjs(timestamp).format('HH:mm:ss.SSS')
}

const getStreamMessageTagType = (type: string) => {
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

const getStreamMessageTypeLabel = (type: string) => {
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

// 处理进度连接
const handleProgressConnected = () => {
  console.log('进度监控已连接')
  streamConnected.value = true
}

// 处理进度更新
const handleProgressUpdate = (progress: GenerationProgress) => {
  console.log('进度更新:', progress)
  testCaseStore.updateGenerationProgress(progress)

  // 更新流式输出区域的进度
  streamProgress.value = { ...progress }

  // 如果显示流式输出，自动滚动到底部
  if (showStreamOutput.value) {
    nextTick(() => {
      scrollStreamToBottom()
    })
  }
}

// 处理流式消息
const handleStreamMessage = (message: SSEMessage) => {
  console.log('=== handleStreamMessage 被调用 ===')
  console.log('收到流式消息:', message)
  console.log('消息类型:', message.type)
  console.log('消息内容:', message.content)
  console.log('消息源:', message.source)

  // 使用 nextTick 确保 DOM 更新不会阻塞界面
  nextTick(() => {
    try {
      // 处理包含content的消息用于流式显示
      if (message.content) {
        const source = message.source || '未知来源'
        console.log(`处理流式消息 - 类型: ${message.type}, 来源: ${source}, 内容: "${message.content.substring(0, 100)}..."`)

        // 自动显示流式输出面板
        if (!showStreamOutput.value) {
          showStreamOutput.value = true
          console.log('自动显示流式输出面板')
        }

        // 如果是该source的第一条消息，初始化
        if (!streamContents.value[source]) {
          streamContents.value[source] = {
            text: message.content,
            typing: { step: 3, interval: 30 }, // 每30ms显示3个字符，提高显示速度
            status: 'loading'
          }
          console.log(`✅ 初始化源[${source}]的流式内容`)
        } else {
          // 追加内容到现有文本
          streamContents.value[source].text += message.content
          console.log(`✅ 追加到源[${source}]的内容`)
        }

        // 如果是最终消息，标记为完成并停止打字效果
        if (message.is_final || message.type === 'completion' || message.type === 'complete') {
          streamContents.value[source].status = 'success'
          streamContents.value[source].typing = false
          console.log(`✅ 源[${source}]流式输出完成`)
        }
      }

      // 添加到流式消息列表（保留原有的消息日志功能）
      const messageToAdd = {
        ...message,
        timestamp: message.timestamp || new Date().toISOString()
      }
      streamMessages.value.push(messageToAdd)

      // 限制消息数量，避免内存占用过多
      if (streamMessages.value.length > 1000) {
        streamMessages.value = streamMessages.value.slice(-500)
      }

      // 自动滚动到底部
      if (showStreamOutput.value) {
        setTimeout(() => {
          scrollStreamToBottom()
        }, 100)
      }

    } catch (error) {
      console.error('处理流式消息时出错:', error)
    }
  })
}

// 处理生成完成
const handleGenerationCompleted = async (result: any) => {
  try {
    streamConnected.value = false

    // 获取生成的测试用例
    if (currentSession.value) {
      // 这里应该调用API获取生成的测试用例
      // const testCases = await testCaseManagementApi.getTestCases({
      //   sessionId: currentSession.value.sessionId
      // })
      // generatedTestCases.value = testCases.data

      // 临时模拟数据
      generatedTestCases.value = []

      // 自动刷新右侧智能体日志信息
      if (selectedSessionId.value) {
        console.log('生成完成，自动刷新智能体日志')
        await loadSessionAgentLogs(selectedSessionId.value)
      }
    }

    // 如果配置了自动导出Excel
    if (generateConfig.exportExcel) {
      await exportToExcel()
    }

  } catch (error) {
    console.error('获取生成结果失败:', error)
  }
}

// 处理生成失败
const handleGenerationFailed = (error: string) => {
  ElMessage.error(`生成失败: ${error}`)
}

// 处理取消生成
const handleCancelGeneration = async () => {
  if (!currentSession.value) return
  
  try {
    await testCaseGenerateApi.cancelGeneration(currentSession.value.sessionId)
    ElMessage.info('已取消生成任务')
    resetGeneration()
  } catch (error) {
    console.error('取消生成失败:', error)
  }
}

// 处理重试生成
const handleRetryGeneration = () => {
  startGeneration()
}

// 处理查看结果
const handleViewResults = () => {
  if (currentSession.value) {
    router.push(`/test-case/management?sessionId=${currentSession.value.sessionId}`)
  }
}

// 导出Excel
const exportToExcel = async () => {
  try {
    exporting.value = true
    
    const exportData = {
      sessionId: currentSession.value?.sessionId,
      testCaseIds: selectedTestCases.value.length > 0 ? selectedTestCases.value : undefined,
      exportConfig: {},
      templateType: 'standard'
    }
    
    const response = await exportApi.exportToExcel(exportData)
    
    // 轮询检查导出状态
    const checkStatus = async () => {
      try {
        const status = await exportApi.getExportStatus(response.exportId)
        
        if (status.status === 'completed') {
          // 下载文件
          const fileResponse = await exportApi.downloadExportFile(response.exportId)
          
          // 创建下载链接
          const blob = new Blob([fileResponse.data])
          const url = window.URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.download = status.fileName || 'test-cases.xlsx'
          link.click()
          window.URL.revokeObjectURL(url)
          
          ElMessage.success('Excel导出成功！')
        } else if (status.status === 'processing') {
          // 继续轮询
          setTimeout(checkStatus, 2000)
        } else {
          throw new Error(status.message || '导出失败')
        }
      } catch (error: any) {
        ElMessage.error(error.message || '导出失败')
      }
    }
    
    setTimeout(checkStatus, 1000)
    
  } catch (error: any) {
    console.error('导出Excel失败:', error)
    ElMessage.error(error.message || '导出Excel失败')
  } finally {
    exporting.value = false
  }
}

// 查看思维导图
const viewMindmap = () => {
  if (currentSession.value) {
    router.push(`/test-case/mindmap/${currentSession.value.sessionId}`)
  }
}

// 处理编辑测试用例
const handleEditTestCase = (testCase: TestCase) => {
  // 打开编辑对话框或跳转到编辑页面
  console.log('编辑测试用例:', testCase)
}

// 处理删除测试用例
const handleDeleteTestCase = async (testCase: TestCase) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除测试用例"${testCase.title}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 从列表中移除
    const index = generatedTestCases.value.findIndex(tc => tc.id === testCase.id)
    if (index > -1) {
      generatedTestCases.value.splice(index, 1)
    }
    
    ElMessage.success('删除成功')
    
  } catch {
    // 用户取消
  }
}

// 处理选择变化
const handleSelectionChange = (selectedIds: string[]) => {
  selectedTestCases.value = selectedIds
}

// 会话管理相关方法
const refreshSessions = async () => {
  try {
    const response = await testCaseGenerateApi.getSessions()
    console.log('API响应原始数据:', response)

    activeSessions.value = response.sessions.map((session: any) => ({
      sessionId: session.sessionId || session.session_id, // 兼容两种格式
      status: session.status,
      inputType: session.inputType || session.input_type, // 兼容两种格式
      fileName: session.fileName || session.file_name, // 兼容两种格式
      selectedAgent: session.selectedAgent || session.selected_agent, // 兼容两种格式
      progress: session.progress,
      createdAt: session.createdAt || session.created_at, // 兼容两种格式
      completedAt: session.completedAt || session.completed_at // 兼容两种格式
    }))

    console.log('刷新会话列表完成:', activeSessions.value.length, '个会话')
    console.log('会话列表数据:', activeSessions.value)

    // 如果当前有选中的会话，更新currentSession
    if (selectedSessionId.value) {
      const updatedSession = activeSessions.value.find(s => s.sessionId === selectedSessionId.value)
      if (updatedSession) {
        currentSession.value = updatedSession
        console.log('更新当前会话状态:', updatedSession.status)
      }
    }

    // 如果当前没有选中的会话，选择最新的一个并加载其日志
    if (!selectedSessionId.value && activeSessions.value.length > 0) {
      const firstSession = activeSessions.value[0]
      selectedSessionId.value = firstSession.sessionId
      currentSession.value = firstSession
      console.log('自动选择第一个会话:', firstSession.sessionId)

      // 自动加载第一个会话的智能体日志
      await loadSessionAgentLogs(firstSession.sessionId)
    }
  } catch (error) {
    console.error('刷新会话列表失败:', error)
    ElMessage.error('刷新会话列表失败')
  }
}

// 获取会话智能体日志
const loadSessionAgentLogs = async (sessionId: string) => {
  if (!sessionId) {
    console.warn('loadSessionAgentLogs: sessionId为空')
    return
  }

  try {
    loadingAgentLogs.value = true
    console.log('🔍 正在加载会话智能体日志:', sessionId)

    // 清空之前的数据
    agentLogs.value = []
    agentLogsSummary.value = null

    // 获取智能体日志
    console.log('📡 调用API: getSessionAgentLogs')
    const logsResponse = await testCaseGenerateApi.getSessionAgentLogs(sessionId, {
      limit: 200
    })

    console.log('📊 API响应数据:', logsResponse)
    console.log('📊 响应数据类型:', typeof logsResponse)
    console.log('📊 items字段:', logsResponse.items)
    console.log('📊 items长度:', logsResponse.items?.length)

    agentLogs.value = logsResponse.items || []
    console.log('✅ 智能体日志加载完成:', agentLogs.value.length, '条')

    // 打印第一条日志的详细信息用于调试
    if (agentLogs.value.length > 0) {
      console.log('📝 第一条日志详情:', agentLogs.value[0])
    }

    // 获取日志摘要
    try {
      console.log('📡 调用API: getSessionLogsSummary')
      const summaryResponse = await testCaseGenerateApi.getSessionLogsSummary(sessionId)
      agentLogsSummary.value = summaryResponse
      console.log('📈 智能体日志摘要加载完成:', summaryResponse)
    } catch (summaryError) {
      console.warn('⚠️ 获取日志摘要失败:', summaryError)
      agentLogsSummary.value = null
    }

    // 如果没有日志数据，显示提示
    if (agentLogs.value.length === 0) {
      console.log('ℹ️ 该会话暂无智能体日志数据')
      ElMessage.info('该会话暂无智能体日志数据')
    }

  } catch (error) {
    console.error('❌ 加载智能体日志失败:', error)
    console.error('❌ 错误详情:', error.response?.data || error.message)
    agentLogs.value = []
    agentLogsSummary.value = null
    ElMessage.error(`加载智能体日志失败: ${error.response?.data?.detail || error.message}`)
  } finally {
    loadingAgentLogs.value = false
  }
}

// 启动SSE连接监听会话流式输出
const startSSEConnection = async (sessionId: string) => {
  try {
    // 如果已经有生成流程在运行，不重复创建
    if (generationFlow.value && currentSession.value?.sessionId === sessionId) {
      console.log('会话已有SSE连接，无需重复创建')
      return
    }

    console.log('为会话启动SSE连接:', sessionId)

    // 创建生成流程管理器来监听SSE
    generationFlow.value = new TestCaseGenerationFlow({
      onProgress: (progress) => {
        console.log('会话进度更新:', progress)
        // 更新会话状态
        const session = activeSessions.value.find(s => s.sessionId === sessionId)
        if (session) {
          session.status = progress.status
          session.progress = progress.progress
        }
      },
      onComplete: (result) => {
        console.log('会话生成完成:', result)
        // 更新会话状态为完成
        const session = activeSessions.value.find(s => s.sessionId === sessionId)
        if (session) {
          session.status = 'completed'
          session.progress = 100
        }
        // 自动刷新智能体日志信息
        if (selectedSessionId.value === sessionId) {
          loadSessionAgentLogs(sessionId)
        }
      },
      onError: (error) => {
        console.error('会话处理失败:', error)
        // 更新会话状态为失败
        const session = activeSessions.value.find(s => s.sessionId === sessionId)
        if (session) {
          session.status = 'failed'
        }
        ElMessage.error(`会话处理失败: ${error}`)
      }
    })

    // 连接到现有会话的SSE流
    const streamUrl = `/api/v1/test-case/generate/stream/${sessionId}`
    await generationFlow.value.connectToExistingSession(sessionId, streamUrl)

    // 显示流式输出面板
    showStreamOutput.value = true

  } catch (error: any) {
    console.error('启动SSE连接失败:', error)
    ElMessage.error(error.message || '启动SSE连接失败')
  }
}

// 选择会话文件（点击文件名）
const selectSessionFile = async (sessionId: string) => {
  selectedSessionId.value = sessionId
  const session = activeSessions.value.find(s => s.sessionId === sessionId)
  if (session) {
    currentSession.value = session

    // 加载该会话的智能体日志
    await loadSessionAgentLogs(sessionId)

    // 如果是正在执行的会话，启动SSE监听
    if (session.status === 'processing') {
      await startSSEConnection(sessionId)
    }

    console.log('选择会话文件:', sessionId, getSessionFileName(session))
  }
}

// 查看会话日志（点击日志按钮）
const viewSessionLogs = async (sessionId: string) => {
  await selectSessionFile(sessionId)
}

// 处理会话选择变化
const handleSessionChange = async (sessionId: string) => {
  if (sessionId) {
    await selectSessionFile(sessionId)
  } else {
    // 清空选择
    selectedSessionId.value = ''
    currentSession.value = null
    agentLogs.value = []
    agentLogsSummary.value = null
  }
}

// 刷新当前会话的日志和状态
const refreshCurrentSession = async () => {
  if (!selectedSessionId.value) {
    ElMessage.warning('请先选择一个会话')
    return
  }

  try {
    console.log('🔄 开始刷新当前会话的日志和状态...')

    // 1. 刷新会话列表（更新会话状态）
    await refreshSessions()
    console.log('✅ 会话列表刷新完成')

    // 2. 更新 testCaseStore 中的当前会话
    if (currentSession.value) {
      testCaseStore.setCurrentSession(currentSession.value)
      console.log('✅ testCaseStore 中的当前会话已更新')
    }

    // 3. 刷新当前会话的智能体日志
    await loadSessionAgentLogs(selectedSessionId.value)
    console.log('✅ 智能体日志刷新完成')

    ElMessage.success('刷新完成')
  } catch (error) {
    console.error('❌ 刷新失败:', error)
    ElMessage.error('刷新失败')
  }
}

// 关闭智能体日志
const closeAgentLogs = () => {
  // 关闭SSE连接
  if (generationFlow.value) {
    generationFlow.value.closeSSEConnection()
    generationFlow.value = null
  }

  selectedSessionId.value = ''
  currentSession.value = null
  agentLogs.value = []
  agentLogsSummary.value = null
  showStreamOutput.value = false
}

// 兼容旧的选择会话函数
const selectSession = async (sessionId: string) => {
  await selectSessionFile(sessionId)
}

const clearAllSessions = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有会话吗？这将删除所有会话数据。',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 清空本地会话数据
    activeSessions.value = []
    selectedSessionId.value = ''
    currentSession.value = null
    streamMessages.value = []
    streamContents.value = {}

    ElMessage.success('所有会话已清空')
  } catch {
    // 用户取消
  }
}

const getSessionIcon = (session: TestCaseSession) => {
  if (session.inputType === 'file') {
    return 'Document'
  } else {
    return 'EditPen'
  }
}

const getSessionDisplayName = (session: TestCaseSession) => {
  if (!session) {
    return '未知会话'
  }

  // 优先使用文件名
  if (session.fileName) {
    return session.fileName
  }

  // 使用创建时间生成显示名称
  if (session.createdAt) {
    const createdTime = dayjs(session.createdAt).format('YYYY-MM-DD HH:mm:ss')
    if (session.inputType === 'text') {
      return `文本输入_${createdTime}`
    } else if (session.inputType === 'file') {
      return `文件上传_${createdTime}`
    } else {
      return `会话_${createdTime}`
    }
  }

  // 兜底方案：使用会话ID
  if (session.sessionId) {
    return `会话_${session.sessionId.substring(0, 8)}`
  }

  return '未知会话'
}

// 获取会话文件名
const getSessionFileName = (session: TestCaseSession) => {
  if (!session) {
    return '未知文件'
  }

  if (session.fileName) {
    return session.fileName
  } else if (session.inputType === 'text') {
    return '文本输入会话'
  } else if (session.inputType === 'file') {
    return `文件上传会话_${session.sessionId ? session.sessionId.substring(0, 8) : 'unknown'}`
  } else {
    return `会话_${session.sessionId ? session.sessionId.substring(0, 8) : 'unknown'}`
  }
}

// 获取文件图标
const getFileIcon = (session: TestCaseSession) => {
  if (!session) {
    return 'Document'
  }

  if (session.fileName) {
    const ext = session.fileName.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'pdf':
        return 'Document'
      case 'doc':
      case 'docx':
        return 'Document'
      case 'xls':
      case 'xlsx':
        return 'Document'
      case 'ppt':
      case 'pptx':
        return 'Document'
      case 'txt':
        return 'Document'
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
        return 'Picture'
      case 'mp4':
      case 'avi':
      case 'mov':
        return 'VideoPlay'
      default:
        return 'Document'
    }
  } else if (session.inputType === 'text') {
    return 'EditPen'
  } else {
    return 'Document'
  }
}

const getSessionStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    'created': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'cancelled': 'info'
  }
  return statusMap[status] || 'info'
}

const getSessionStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'created': '已创建',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

const getProgressStatus = (status: string) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  if (status === 'processing') return undefined
  return undefined
}

const formatSessionTime = (timestamp: string) => {
  return dayjs(timestamp).format('MM-DD HH:mm')
}

const getSelectedSessionTitle = () => {
  if (!selectedSessionId.value) return '智能体日志输出'
  const session = activeSessions.value.find(s => s.sessionId === selectedSessionId.value)
  if (session) {
    return `${getSessionDisplayName(session)} - 智能体日志`
  }
  return '智能体日志输出'
}

// 智能体日志相关辅助函数
const handleClearAgentLogs = () => {
  agentLogs.value = []
  agentLogsSummary.value = null
}

const getLogTypeColor = (messageType: string) => {
  const colorMap: Record<string, string> = {
    'info': 'info',
    'success': 'success',
    'warning': 'warning',
    'error': 'danger',
    'debug': 'info',
    'progress': 'primary',
    'completion': 'success',
    'stage': 'info'
  }
  return colorMap[messageType] || 'info'
}

const getMessageTypeColor = (messageType: string) => {
  const colorMap: Record<string, string> = {
    'info': 'info',
    'success': 'success',
    'warning': 'warning',
    'error': 'danger',
    'debug': '',
    'progress': 'primary',
    'completion': 'success',
    'stage': 'info'
  }
  return colorMap[messageType] || ''
}

const getMessageTypeLabel = (messageType: string) => {
  const labelMap: Record<string, string> = {
    'info': '信息',
    'success': '成功',
    'warning': '警告',
    'error': '错误',
    'debug': '调试',
    'progress': '进度',
    'completion': '完成',
    'stage': '阶段'
  }
  return labelMap[messageType] || messageType
}

const formatLogTime = (timestamp: string) => {
  return dayjs(timestamp).format('HH:mm:ss.SSS')
}

// 查看会话详情
const viewSessionDetail = (sessionId: string) => {
  selectedSessionForDetail.value = sessionId
  showSessionDetail.value = true
}

// 关闭会话详情弹窗
const handleCloseSessionDetail = () => {
  showSessionDetail.value = false
  selectedSessionForDetail.value = ''
}

// 删除会话
const deleteSession = async (sessionId: string) => {
  try {
    const session = activeSessions.value.find(s => s.sessionId === sessionId)
    const sessionName = session ? getSessionDisplayName(session) : (sessionId ? sessionId.substring(0, 8) : '未知会话')

    await ElMessageBox.confirm(
      `确定要删除会话"${sessionName}"吗？这将删除该会话的所有数据。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 调用API删除会话
    await testCaseGenerateApi.deleteSession(sessionId)

    // 从本地列表中移除
    const index = activeSessions.value.findIndex(s => s.sessionId === sessionId)
    if (index >= 0) {
      activeSessions.value.splice(index, 1)
    }

    // 如果删除的是当前选中的会话，清空选择
    if (selectedSessionId.value === sessionId) {
      selectedSessionId.value = ''
      currentSession.value = null
      streamMessages.value = []
      streamContents.value = {}
    }

    ElMessage.success('会话删除成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除会话失败:', error)
      ElMessage.error('删除会话失败')
    }
  }
}

// 重置生成状态
const resetGenerationState = () => {
  generating.value = false
  showStreamOutput.value = false
  streamMessages.value = []
  streamContents.value = {}
  currentSession.value = null
  generatedTestCases.value = []
  selectedTestCases.value = []
  sessionProgress.value = {
    sessionId: '',
    status: 'idle',
    progress: 0,
    currentStage: '',
    testCasesCount: 0
  }
  streamConnected.value = false
  sessionStartTime.value = null
}

// 测试API连接
const testApiConnection = async () => {
  try {
    console.log('🔧 测试API连接...')

    // 测试会话列表API
    const sessionsResponse = await testCaseGenerateApi.getSessions()
    console.log('✅ 会话列表API正常:', sessionsResponse)
    ElMessage.success(`API连接正常，找到 ${sessionsResponse.sessions.length} 个会话`)

    // 如果有会话，测试智能体日志API
    if (sessionsResponse.sessions.length > 0) {
      const firstSessionId = sessionsResponse.sessions[0].sessionId || sessionsResponse.sessions[0].session_id
      console.log('🔍 测试智能体日志API，会话ID:', firstSessionId)

      const logsResponse = await testCaseGenerateApi.getSessionAgentLogs(firstSessionId, { limit: 5 })
      console.log('✅ 智能体日志API正常:', logsResponse)
      ElMessage.success(`智能体日志API正常，找到 ${logsResponse.items.length} 条日志`)
    }

  } catch (error) {
    console.error('❌ API连接测试失败:', error)
    ElMessage.error(`API连接失败: ${error.response?.data?.detail || error.message}`)
  }
}

onMounted(async () => {
  // 页面加载时的初始化逻辑
  console.log('🚀 页面加载，开始初始化...')

  try {
    await loadProjects()
    console.log('✅ 项目加载完成')
  } catch (error) {
    console.error('❌ 项目加载失败:', error)
  }

  try {
    await refreshSessions()
    console.log('✅ 会话刷新完成')
  } catch (error) {
    console.error('❌ 会话刷新失败:', error)
  }

  console.log('🎯 初始化完成')
})
</script>

<style lang="scss" scoped>
.test-case-generate {
  min-height: 100vh;
  padding: var(--spacing-lg);
  background: var(--bg-tertiary);

  .page-container {
    max-width: 1400px;
    margin: 0 auto;

    &.with-stream-panel {
      max-width: 1800px;
    }
  }

  .content-wrapper {
    display: flex;
    gap: var(--spacing-lg);
    align-items: flex-start;
    min-height: calc(100vh - 120px);
  }

  .main-content {
    flex: 1;
    min-width: 0;
  }

  .left-content {
    width: 100%;
  }

  .stream-panel {
    width: 400px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    height: calc(100vh - 140px);
  }

  .right-content {
    width: 400px;
    flex-shrink: 0;

    &.stream-output-panel {
      display: flex;
      flex-direction: column;
      height: calc(100vh - 140px);
    }
  }

  .page-header {
    margin-bottom: var(--spacing-2xl);
    padding: var(--spacing-xl);
    background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
    border-radius: var(--border-radius-lg);
    box-shadow: var(--shadow-lg);
    position: relative;
    overflow: hidden;
    display: flex;
    justify-content: space-between;
    align-items: center;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      right: 0;
      width: 200px;
      height: 200px;
      background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
      border-radius: 50%;
      opacity: 0.1;
      transform: translate(50%, -50%);
    }

    .header-content {
      position: relative;
      z-index: 2;

      .page-title {
        font-size: 32px;
        font-weight: 700;
        margin-bottom: var(--spacing-md);
        line-height: 1.2;
      }

      .page-subtitle {
        font-size: 16px;
        color: var(--text-secondary);
        line-height: 1.5;
        max-width: 600px;
      }
    }

    .header-decoration {
      position: absolute;
      top: var(--spacing-lg);
      right: var(--spacing-lg);
      display: flex;
      gap: var(--spacing-sm);

      .decoration-circle {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
        animation: pulse 2s ease-in-out infinite;

        &:nth-child(2) {
          animation-delay: 0.5s;
        }

        &:nth-child(3) {
          animation-delay: 1s;
        }
      }
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      z-index: 2;
      position: relative;
    }
  }
  
  .generation-card {
    margin-bottom: var(--spacing-xl);
    border: 1px solid var(--border-color);
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-lg);
    }

    .generation-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: var(--spacing-lg);

      .header-left {
        flex: 0 0 auto;

        .header-info {
          h3 {
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
            margin: 0 0 var(--spacing-xs) 0;

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
      }

      .header-center {
        flex: 1;
        display: flex;
        justify-content: center;

        .quick-stats {
          display: flex;
          align-items: center;
          gap: var(--spacing-md);
          padding: var(--spacing-sm) var(--spacing-md);
          background: var(--bg-tertiary);
          border-radius: var(--border-radius-lg);
          border: 1px solid var(--border-color-light);

          .stat-item {
            display: flex;
            align-items: center;
            gap: var(--spacing-xs);

            .stat-icon {
              color: var(--primary-color);
              font-size: 16px;

              &.status-active {
                color: var(--color-success);
              }
            }

            .stat-content {
              display: flex;
              flex-direction: column;
              align-items: center;

              .stat-value {
                font-size: 14px;
                font-weight: 600;
                color: var(--text-primary);
                line-height: 1;
              }

              .stat-label {
                font-size: 11px;
                color: var(--text-secondary);
                line-height: 1;
                margin-top: 2px;
              }
            }
          }

          .stat-divider {
            width: 1px;
            height: 24px;
            background: var(--border-color);
          }
        }
      }

      .header-right {
        flex: 0 0 auto;

        .header-actions {
          display: flex;
          align-items: center;
          gap: var(--spacing-md);

          .quick-actions {
            display: flex;
            gap: var(--spacing-xs);

            .el-button {
              transition: all 0.3s ease;

              &:hover {
                transform: translateY(-1px);
              }
            }
          }
        }
      }
    }

    .generation-content {
      .section-title {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        font-size: 16px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: var(--spacing-md);

        .el-icon {
          color: var(--primary-color);
        }

        .el-tag {
          margin-left: auto;
        }
      }

      .config-section {
        .config-form {
          .el-form-item {
            margin-bottom: var(--spacing-md);
            margin-right: var(--spacing-lg);

            .el-form-item__label {
              font-weight: 500;
              color: var(--text-primary);
              width: 80px !important;
            }
          }
        }
      }

      .input-section {
        .file-input-section,
        .text-input-section {
          margin-top: var(--spacing-md);
        }
      }

      .action-section {
        margin-top: var(--spacing-xl);
        padding-top: var(--spacing-lg);
        border-top: 1px solid var(--border-color-light);

        .action-buttons {
          display: flex;
          justify-content: center;
          gap: var(--spacing-lg);
          margin-bottom: var(--spacing-md);

          .generate-btn {
            padding: var(--spacing-md) var(--spacing-xl);
            font-size: 16px;
            font-weight: 600;
            border-radius: var(--border-radius-lg);
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-light) 100%);
            border: none;
            box-shadow: var(--shadow-lg);
            transition: all 0.3s ease;

            &:hover:not(:disabled) {
              transform: translateY(-2px);
              box-shadow: var(--shadow-xl);
            }

            &:disabled {
              opacity: 0.6;
              cursor: not-allowed;
            }

            span {
              margin-left: var(--spacing-sm);
            }
          }

          .reset-btn {
            padding: var(--spacing-md) var(--spacing-lg);
            font-weight: 500;
            border-radius: var(--border-radius-lg);
            transition: all 0.3s ease;

            &:hover {
              transform: translateY(-1px);
              box-shadow: var(--shadow-md);
            }
          }
        }

        .action-hint {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--spacing-sm);
          color: var(--text-secondary);
          font-size: 14px;

          .el-icon {
            color: var(--warning-color);
          }
        }
      }
    }
  }



  .text-input-section {
    .el-form-item {
      margin-bottom: 0;
    }

    .el-textarea {
      .el-textarea__inner {
        border-radius: var(--border-radius-lg);
        border: 2px solid var(--border-color);
        transition: all 0.3s ease;

        &:focus {
          border-color: var(--primary-color);
          box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
      }
    }
  }


  
  .progress-section,
  .results-section {
    margin-bottom: var(--spacing-xl);

    .el-card {
      border: 1px solid var(--border-color);
      transition: all 0.3s ease;

      &:hover {
        box-shadow: var(--shadow-lg);
      }

      .card-header {
        background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
        border-bottom: 1px solid var(--border-color-light);

        .el-tag {
          font-weight: 500;
          border-radius: var(--border-radius);
        }
      }
    }
  }

  .results-section {
    .header-actions {
      display: flex;
      gap: var(--spacing-md);

      .el-button {
        border-radius: var(--border-radius);
        font-weight: 500;
        transition: all 0.3s ease;

        &:hover {
          transform: translateY(-1px);
          box-shadow: var(--shadow-md);
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .test-case-generate {
    .page-header {
      padding: var(--spacing-lg);

      .header-content {
        .page-title {
          font-size: 24px;
        }

        .page-subtitle {
          font-size: 14px;
        }
      }
    }

    .generation-card {
      .generation-header {
        flex-direction: column;
        gap: var(--spacing-md);
        align-items: stretch;

        .header-left {
          text-align: center;
        }

        .header-center {
          .quick-stats {
            justify-content: center;
            flex-wrap: wrap;
            gap: var(--spacing-sm);

            .stat-divider {
              display: none;
            }
          }
        }

        .header-right {
          .header-actions {
            justify-content: center;
            flex-wrap: wrap;
          }
        }
      }

      .generation-content {
        .config-section {
          .config-form {
            .el-form-item {
              margin-right: 0;
              margin-bottom: var(--spacing-lg);

              .el-form-item__label {
                width: 100px !important;
              }
            }
          }
        }

        .action-section {
          .action-buttons {
            flex-direction: column;
            align-items: center;

            .generate-btn,
            .reset-btn {
              width: 100%;
              max-width: 300px;
            }
          }
        }
      }
    }
  }

  // 流式输出面板样式
  .stream-output-panel {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    height: calc(100vh - 140px);

    // 会话文件管理面板
    .session-files-panel {
      background: var(--bg-primary);
      border-radius: var(--border-radius-lg);
      box-shadow: var(--shadow-md);
      border: 1px solid var(--border-color);
      overflow: hidden;
      flex-shrink: 0;
      max-height: 350px;
      display: flex;
      flex-direction: column;

      .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: var(--spacing-md) var(--spacing-lg);
        background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
        border-bottom: 1px solid var(--border-color-light);

        .panel-title {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
          font-weight: 600;
          color: var(--text-primary);
          font-size: 15px;

          .el-icon {
            color: var(--primary-color);
            font-size: 16px;
          }

          .el-badge {
            margin-left: var(--spacing-xs);
          }
        }

        .panel-actions {
          display: flex;
          gap: var(--spacing-xs);

          .el-button {
            &:hover {
              background: var(--primary-light);
            }
          }
        }
      }

      .session-files-list {
        flex: 1;
        overflow-y: auto;
        padding: var(--spacing-sm);

        .file-item {
          padding: var(--spacing-md);
          margin-bottom: var(--spacing-sm);
          border-radius: var(--border-radius-lg);
          border: 1px solid var(--border-color-light);
          background: var(--bg-primary);
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;

          &:hover {
            background: var(--bg-secondary);
            border-color: var(--primary-color);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);

            .session-actions {
              opacity: 1;
            }
          }

          &.active {
            background: linear-gradient(135deg, var(--primary-light) 0%, rgba(64, 158, 255, 0.1) 100%);
            border-color: var(--primary-color);
            box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);

            .file-header .file-info .file-name {
              color: var(--primary-color);
              font-weight: 600;
            }
          }

          &:last-child {
            margin-bottom: 0;
          }

          .file-header {
            display: flex;
            align-items: center;
            gap: var(--spacing-md);

            .file-icon {
              display: flex;
              align-items: center;
              justify-content: center;
              width: 32px;
              height: 32px;
              border-radius: var(--border-radius-md);
              background: var(--bg-secondary);
              flex-shrink: 0;

              .el-icon {
                color: var(--primary-color);
                font-size: 16px;
              }
            }

            .file-info {
              flex: 1;
              min-width: 0;

              .file-name {
                font-size: 14px;
                font-weight: 500;
                color: var(--text-primary);
                cursor: pointer;
                margin-bottom: 2px;
                transition: color 0.3s ease;

                &:hover {
                  color: var(--primary-color);
                  text-decoration: underline;
                }
              }

              .file-meta {
                display: flex;
                align-items: center;
                gap: var(--spacing-sm);

                .file-time {
                  font-size: 12px;
                  color: var(--text-secondary);
                }

                .el-tag {
                  flex-shrink: 0;
                }
              }
            }

            .file-actions {
              display: flex;
              gap: var(--spacing-xs);
              opacity: 0;
              transition: opacity 0.3s ease;

              .el-button {
                &:hover {
                  background: var(--primary-light);
                }
              }
            }
          }

          .session-progress {
            margin-top: var(--spacing-md);
            padding-left: 44px; // 对齐图标位置
          }
        }

        .empty-files {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 120px;
          color: var(--text-secondary);
        }
      }
    }

    // 流式输出内容区域
    .stream-output-content {
      flex: 1;
      min-height: 0;
      display: flex;
      flex-direction: column;
    }

    .stream-panel {
      background: var(--bg-primary);
      border-radius: var(--border-radius-lg);
      box-shadow: var(--shadow-lg);
      height: calc(100vh - 140px);
      display: flex;
      flex-direction: column;
      overflow: hidden;

      .stream-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: var(--spacing-md);
        border-bottom: 1px solid var(--border-color);
        background: var(--bg-secondary);

        .stream-title {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
          font-weight: 600;
          color: var(--text-primary);
        }

        .stream-actions {
          display: flex;
          gap: var(--spacing-xs);
        }
      }

      .stream-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        padding: var(--spacing-md);

        .connection-status {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--spacing-md);

          .session-info {
            font-size: 12px;
            color: var(--text-secondary);
          }
        }

        .stream-progress {
          margin-bottom: var(--spacing-md);

          .progress-info {
            margin-top: var(--spacing-sm);

            .current-stage {
              display: flex;
              align-items: center;
              gap: var(--spacing-xs);
              font-size: 14px;
              color: var(--text-primary);
              margin-bottom: var(--spacing-xs);

              .stage-icon {
                color: var(--color-primary);
              }
            }

            .test-cases-count {
              font-size: 13px;
              color: var(--color-success);
            }
          }
        }

        .stream-text-output {
          margin-bottom: var(--spacing-md);
          display: flex;
          flex-direction: column;
          height: 400px;

          .text-output-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--spacing-sm);
            font-weight: 600;
            color: var(--text-primary);
          }

          .text-output-content {
            flex: 1;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius-md);
            background: var(--bg-tertiary);
            position: relative;

            .stream-containers {
              padding: var(--spacing-sm);

              .debug-sources {
                background: #f0f8ff;
                padding: var(--spacing-xs);
                margin-bottom: var(--spacing-sm);
                border-radius: var(--border-radius-sm);
                font-size: 12px;
                color: #333;
              }

              .stream-source-container {
                margin-bottom: var(--spacing-md);
                border: 2px solid #e6f7ff;
                border-radius: var(--border-radius-md);
                padding: var(--spacing-sm);

                &:last-child {
                  margin-bottom: 0;
                }

                .debug-content {
                  background: #fff7e6;
                  padding: var(--spacing-xs);
                  margin-bottom: var(--spacing-sm);
                  border-radius: var(--border-radius-sm);
                  font-size: 12px;

                  p {
                    margin: 2px 0;
                    word-break: break-all;
                  }
                }

                // Bubble组件样式覆盖
                :deep(.ant-bubble) {
                  max-width: 100%;

                  .ant-bubble-content {
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    font-size: 13px;
                    line-height: 1.6;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                  }

                  .ant-bubble-header {
                    font-weight: 600;
                    color: var(--text-primary);
                    margin-bottom: var(--spacing-xs);
                  }
                }
              }
            }

            .empty-text {
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              height: 100%;
              color: var(--text-secondary);

              .debug-info {
                margin-top: var(--spacing-md);
                padding: var(--spacing-sm);
                background: var(--bg-secondary);
                border-radius: var(--border-radius-sm);
                font-size: 12px;
                max-width: 100%;
                overflow: auto;

                p {
                  margin: var(--spacing-xs) 0;
                  white-space: pre-wrap;
                  word-break: break-all;
                }
              }
            }
          }
        }

        .stream-messages {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;

          .messages-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--spacing-sm);
            font-size: 14px;
            font-weight: 500;
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
              border-left: 3px solid var(--color-primary);

              &:last-child {
                margin-bottom: 0;
              }

              &.message-error {
                border-left-color: var(--color-danger);
              }

              &.message-complete,
              &.message-completion,
              &.message-final_result {
                border-left-color: var(--color-success);
              }

              &.message-cancelled {
                border-left-color: var(--color-warning);
              }

              .message-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: var(--spacing-xs);

                .message-time {
                  font-size: 11px;
                  color: var(--text-secondary);
                  font-family: 'Courier New', monospace;
                }
              }

              .message-content {
                font-size: 13px;
                color: var(--text-primary);
                line-height: 1.4;
                word-break: break-word;
              }

              .message-result {
                margin-top: var(--spacing-xs);

                pre {
                  font-size: 11px;
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
    }
  }

  // 默认提示区域样式
  .default-hint {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-primary);
    border-radius: var(--border-radius-lg);
    box-shadow: var(--shadow-md);
    border: 1px solid var(--border-color);
    min-height: 300px;
  }

  // 智能体日志主面板样式
  .agent-logs-main-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: var(--bg-primary);
    border-radius: var(--border-radius-lg);
    border: 1px solid var(--border-color);
    overflow: hidden;

    .panel-header {
      padding: var(--spacing-md);
      border-bottom: 1px solid var(--border-color);
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      display: flex;
      justify-content: space-between;
      align-items: center;

      .panel-title {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        font-size: 16px;
        font-weight: 600;

        .el-icon {
          font-size: 18px;
        }
      }

      .panel-actions {
        display: flex;
        gap: var(--spacing-xs);

        .el-button {
          color: white;
          border-color: rgba(255, 255, 255, 0.3);

          &:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.5);
          }
        }
      }
    }

    // 会话选择器样式
    .session-selector {
      padding: var(--spacing-md);
      border-bottom: 1px solid var(--border-color-light);
      background: var(--bg-secondary);

      :deep(.el-select) {
        .el-input__wrapper {
          border-radius: var(--border-radius-md);
        }
      }

      .session-option {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;

        .session-info {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
          flex: 1;

          .session-name {
            font-weight: 500;
            color: var(--text-primary);
          }
        }

        .session-time {
          font-size: 12px;
          color: var(--text-secondary);
        }
      }
    }

    // 日志摘要统计样式
    .logs-summary {
      padding: var(--spacing-md);
      border-bottom: 1px solid var(--border-color-light);
      background: var(--bg-tertiary);

      .summary-stats {
        display: flex;
        gap: var(--spacing-md);

        .stat-item {
          flex: 1;
          text-align: center;
          padding: var(--spacing-sm);
          background: var(--bg-primary);
          border-radius: var(--border-radius-md);
          border: 1px solid var(--border-color-light);
          transition: all 0.3s ease;

          &:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-sm);
          }

          .stat-number {
            font-size: 20px;
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: var(--spacing-xs);
          }

          .stat-label {
            font-size: 12px;
            color: var(--text-secondary);
          }
        }
      }

      // 新的横向显示样式
      .summary-stats-horizontal {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        padding: var(--spacing-sm);
        background: var(--bg-primary);
        border-radius: var(--border-radius-md);
        border: 1px solid var(--border-color-light);

        .stat-text {
          font-size: 14px;
          color: var(--text-primary);
          font-weight: 500;
        }

        .stat-divider {
          color: var(--text-tertiary);
          font-size: 12px;
        }
      }
    }
  }

  // 智能体日志内容区域
  .agent-logs-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  // 原有的智能体日志样式（保持兼容）
  .agent-logs-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: var(--bg-primary);
    border-radius: var(--border-radius-lg);
    box-shadow: var(--shadow-md);
    border: 1px solid var(--border-color);
    overflow: hidden;

    .logs-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--spacing-md) var(--spacing-lg);
      background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
      border-bottom: 1px solid var(--border-color-light);

      .header-info {
        h4 {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
          margin: 0 0 var(--spacing-xs) 0;
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary);

          .el-icon {
            color: var(--primary-color);
          }
        }

        .logs-stats {
          display: flex;
          gap: var(--spacing-xs);
        }
      }

      .header-actions {
        display: flex;
        gap: var(--spacing-xs);
      }
    }

    .logs-container {
      flex: 1;
      overflow-y: auto;
      padding: var(--spacing-sm);

      .empty-logs {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 200px;
      }

      .logs-list {
        .log-item {
          margin-bottom: var(--spacing-sm);
          padding: var(--spacing-md);
          background: var(--bg-tertiary);
          border-radius: var(--border-radius-md);
          border: 1px solid var(--border-color-light);
          transition: all 0.3s ease;

          &:hover {
            background: var(--bg-secondary);
            border-color: var(--primary-color);
            box-shadow: var(--shadow-sm);
          }

          &:last-child {
            margin-bottom: 0;
          }

          &.log-error {
            border-left: 4px solid var(--danger-color);
          }

          &.log-success {
            border-left: 4px solid var(--success-color);
          }

          &.log-warning {
            border-left: 4px solid var(--warning-color);
          }

          &.log-info {
            border-left: 4px solid var(--info-color);
          }

          .log-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--spacing-sm);

            .log-meta {
              display: flex;
              align-items: center;
              gap: var(--spacing-sm);

              .log-time {
                font-size: 12px;
                color: var(--text-secondary);
                font-family: 'Courier New', monospace;
              }
            }

            .log-stage {
              flex-shrink: 0;
            }
          }

          .log-content {
            .content-text {
              color: var(--text-primary);
              line-height: 1.6;
              white-space: pre-wrap;
              word-wrap: break-word;
              margin-bottom: var(--spacing-sm);
            }

            .result-data,
            .error-info,
            .metrics-data {
              margin-top: var(--spacing-sm);

              pre {
                background: var(--bg-secondary);
                padding: var(--spacing-sm);
                border-radius: var(--border-radius-sm);
                font-size: 12px;
                line-height: 1.4;
                overflow-x: auto;
                max-height: 200px;
              }
            }
          }
        }
      }
    }
  }

  // 响应式适配
  @media (max-width: 1400px) {
    .content-wrapper {
      flex-direction: column;
      gap: var(--spacing-md);
    }

    .stream-panel {
      width: 100%;
      height: 500px;
    }

    .right-content {
      width: 100%;

      &.stream-output-panel {
        height: 500px;
      }
    }

    .stream-output-panel {
      .session-management-panel {
        max-height: 200px;
      }

      .stream-output-content {
        height: 280px;
      }
    }
  }

  @media (max-width: 768px) {
    .test-case-generate {
      padding: var(--spacing-md);

      .content-wrapper {
        gap: var(--spacing-sm);
      }

      .stream-panel {
        height: 400px;
      }

      .right-content.stream-output-panel {
        height: 400px;
      }
    }
  }
}
</style>
