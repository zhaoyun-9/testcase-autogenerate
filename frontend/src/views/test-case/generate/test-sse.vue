<template>
  <div class="test-sse-page">
    <div class="page-container">
      <!-- 页面标题 -->
      <div class="page-header">
        <h1 class="page-title">SSE流式消息测试</h1>
        <p class="page-subtitle">测试智能体SSE流式消息的实时显示功能</p>
      </div>

      <!-- 测试控制区 -->
      <el-card class="control-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>测试控制</span>
          </div>
        </template>

        <div class="control-section">
          <el-form :model="testForm" label-width="120px">
            <el-form-item label="需求描述">
              <el-input
                v-model="testForm.requirementText"
                type="textarea"
                :rows="4"
                placeholder="请输入测试需求描述，例如：用户登录功能测试"
              />
            </el-form-item>
            
            <el-form-item label="分析目标">
              <el-input
                v-model="testForm.analysisTarget"
                placeholder="生成测试用例"
              />
            </el-form-item>
          </el-form>

          <div class="action-buttons">
            <el-button
              type="primary"
              size="large"
              @click="startTest"
              :loading="testing"
              :disabled="!testForm.requirementText"
            >
              <el-icon><Play /></el-icon>
              开始测试
            </el-button>

            <el-button
              v-if="currentSession"
              size="large"
              @click="resetTest"
            >
              <el-icon><Refresh /></el-icon>
              重置测试
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- SSE消息监控 -->
      <div v-if="currentSession" class="monitor-section">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>SSE消息监控</span>
              <el-tag size="small">会话ID: {{ currentSession.sessionId.slice(0, 8) }}</el-tag>
            </div>
          </template>

          <ProgressMonitor
            :session-id="currentSession.sessionId"
            :stream-url="currentSession.streamUrl"
            :show-logs="true"
            :show-actions="true"
            @connected="handleConnected"
            @progress="handleProgress"
            @completed="handleCompleted"
            @failed="handleFailed"
          />
        </el-card>
      </div>

      <!-- 测试结果 -->
      <div v-if="testResults.length > 0" class="results-section">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>测试结果</span>
            </div>
          </template>

          <div class="results-content">
            <div
              v-for="(result, index) in testResults"
              :key="index"
              class="result-item"
            >
              <div class="result-header">
                <el-tag :type="getResultTagType(result.type)" size="small">
                  {{ result.type }}
                </el-tag>
                <span class="result-time">{{ formatTime(result.timestamp) }}</span>
              </div>
              <div class="result-content">
                {{ result.content }}
              </div>
              <div v-if="result.result" class="result-data">
                <pre>{{ JSON.stringify(result.result, null, 2) }}</pre>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { testCaseGenerateApi } from '@/api/testCase'
import ProgressMonitor from '@/components/ProgressMonitor/index.vue'
import type { TestCaseSession, GenerationProgress, SSEMessage } from '@/types/testCase'
import dayjs from 'dayjs'

const testing = ref(false)
const currentSession = ref<TestCaseSession | null>(null)
const testResults = ref<SSEMessage[]>([])

const testForm = reactive({
  requirementText: '用户登录功能测试：\n1. 用户输入正确的用户名和密码\n2. 点击登录按钮\n3. 系统验证用户信息\n4. 登录成功后跳转到主页',
  analysisTarget: '生成测试用例'
})

// 开始测试
const startTest = async () => {
  try {
    testing.value = true
    testResults.value = []

    ElMessage.info('正在创建测试会话...')

    // 创建生成会话
    const response = await testCaseGenerateApi.createSession({
      requirement_text: testForm.requirementText,
      analysis_target: testForm.analysisTarget,
      generate_mind_map: true,
      export_excel: false,
      max_test_cases: 10,
      tags: ['测试']
    })

    currentSession.value = {
      sessionId: response.sessionId,
      inputType: response.inputType as 'text',
      status: 'processing',
      streamUrl: response.streamUrl,
      createdAt: response.createdAt
    }

    ElMessage.success('测试会话创建成功，开始监控SSE消息')

  } catch (error: any) {
    console.error('测试启动失败:', error)
    ElMessage.error(error.message || '测试启动失败')
  } finally {
    testing.value = false
  }
}

// 重置测试
const resetTest = () => {
  currentSession.value = null
  testResults.value = []
  testing.value = false
}

// 处理连接成功
const handleConnected = () => {
  ElMessage.success('SSE连接已建立')
}

// 处理进度更新
const handleProgress = (progress: GenerationProgress) => {
  console.log('进度更新:', progress)
}

// 处理完成
const handleCompleted = (result: any) => {
  ElMessage.success('测试完成')
  testResults.value.push({
    message_id: 'completion',
    type: 'completion',
    source: 'system',
    content: '测试完成',
    region: 'process',
    platform: 'test_case',
    is_final: true,
    timestamp: new Date().toISOString(),
    result
  })
}

// 处理失败
const handleFailed = (error: string) => {
  ElMessage.error(`测试失败: ${error}`)
  testResults.value.push({
    message_id: 'error',
    type: 'error',
    source: 'system',
    content: `测试失败: ${error}`,
    region: 'process',
    platform: 'test_case',
    is_final: true,
    error,
    timestamp: new Date().toISOString()
  })
}

// 获取结果标签类型
const getResultTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    'message': 'info',
    'progress': 'primary',
    'completion': 'success',
    'error': 'danger'
  }
  return typeMap[type] || 'info'
}

// 格式化时间
const formatTime = (timestamp: string) => {
  return dayjs(timestamp).format('HH:mm:ss.SSS')
}
</script>

<style lang="scss" scoped>
.test-sse-page {
  .page-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }

  .page-header {
    text-align: center;
    margin-bottom: 30px;

    .page-title {
      font-size: 28px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin-bottom: 10px;
    }

    .page-subtitle {
      font-size: 16px;
      color: var(--el-text-color-secondary);
    }
  }

  .control-card {
    margin-bottom: 20px;

    .control-section {
      .action-buttons {
        display: flex;
        gap: 12px;
        justify-content: center;
        margin-top: 20px;
      }
    }
  }

  .monitor-section {
    margin-bottom: 20px;
  }

  .results-section {
    .results-content {
      max-height: 400px;
      overflow-y: auto;

      .result-item {
        margin-bottom: 16px;
        padding: 12px;
        border: 1px solid var(--el-border-color-light);
        border-radius: 6px;
        background-color: var(--el-fill-color-extra-light);

        &:last-child {
          margin-bottom: 0;
        }

        .result-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;

          .result-time {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }

        .result-content {
          font-size: 14px;
          color: var(--el-text-color-primary);
          margin-bottom: 8px;
        }

        .result-data {
          background-color: var(--el-bg-color);
          padding: 8px;
          border-radius: 4px;
          font-family: 'Courier New', monospace;
          font-size: 12px;
          color: var(--el-text-color-secondary);
          overflow-x: auto;
        }
      }
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 500;
  }
}
</style>
