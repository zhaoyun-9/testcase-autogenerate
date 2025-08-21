<template>
  <div class="test-case-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" :icon="ArrowLeft">返回</el-button>
        <h1>测试用例详情</h1>
      </div>
      <div class="header-right">
        <el-button @click="editTestCase" type="primary" :icon="Edit">编辑</el-button>
        <el-button @click="exportTestCase" :icon="Download">导出</el-button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <!-- 测试用例内容 -->
    <div v-else-if="testCase" class="test-case-content">
      <!-- 基本信息 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
          </div>
        </template>
        
        <el-descriptions :column="2" border>
          <el-descriptions-item label="标题">
            {{ testCase.title }}
          </el-descriptions-item>
          <el-descriptions-item label="ID">
            {{ testCase.id }}
          </el-descriptions-item>
          <el-descriptions-item label="测试类型">
            <el-tag>{{ getTestTypeLabel(testCase.testType) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="测试级别">
            <el-tag>{{ getTestLevelLabel(testCase.testLevel) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="优先级">
            <el-tag :type="getPriorityType(testCase.priority)">
              {{ testCase.priority }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(testCase.status)">
              {{ getStatusLabel(testCase.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatTime(testCase.createdAt) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatTime(testCase.updatedAt) }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 描述 -->
      <el-card v-if="testCase.description" class="info-card">
        <template #header>
          <div class="card-header">
            <span>描述</span>
          </div>
        </template>
        <div class="description-content">
          {{ testCase.description }}
        </div>
      </el-card>

      <!-- 前置条件 -->
      <el-card v-if="testCase.preconditions" class="info-card">
        <template #header>
          <div class="card-header">
            <span>前置条件</span>
          </div>
        </template>
        <div class="preconditions-content">
          {{ testCase.preconditions }}
        </div>
      </el-card>

      <!-- 测试步骤 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>测试步骤</span>
          </div>
        </template>
        <div class="test-steps">
          <div v-if="testCase.testSteps && testCase.testSteps.length > 0">
            <div
              v-for="(step, index) in testCase.testSteps"
              :key="index"
              class="step-item"
            >
              <div class="step-number">{{ step.step }}</div>
              <div class="step-content">
                <div class="step-action">
                  <strong>操作：</strong>{{ step.action }}
                </div>
                <div v-if="step.expectedResult" class="step-expected">
                  <strong>预期结果：</strong>{{ step.expectedResult }}
                </div>
                <div v-if="step.data" class="step-data">
                  <strong>测试数据：</strong>{{ step.data }}
                </div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无测试步骤" :image-size="80" />
        </div>
      </el-card>

      <!-- 预期结果 -->
      <el-card v-if="testCase.expectedResults" class="info-card">
        <template #header>
          <div class="card-header">
            <span>预期结果</span>
          </div>
        </template>
        <div class="expected-results-content">
          {{ testCase.expectedResults }}
        </div>
      </el-card>

      <!-- 标签 -->
      <el-card v-if="testCase.tags && testCase.tags.length > 0" class="info-card">
        <template #header>
          <div class="card-header">
            <span>标签</span>
          </div>
        </template>
        <div class="tags-content">
          <el-tag
            v-for="tag in testCase.tags"
            :key="tag"
            class="tag-item"
          >
            {{ tag }}
          </el-tag>
        </div>
      </el-card>
    </div>

    <!-- 错误状态 -->
    <div v-else class="error-container">
      <el-result
        icon="error"
        title="加载失败"
        sub-title="无法获取测试用例详情，请稍后重试"
      >
        <template #extra>
          <el-button type="primary" @click="loadTestCase">重新加载</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Edit, Download } from '@element-plus/icons-vue'
import { testCaseManagementApi } from '@/api'
import type { TestCase } from '@/types/testCase'
import { 
  TEST_TYPE_OPTIONS, 
  TEST_LEVEL_OPTIONS, 
  STATUS_OPTIONS 
} from '@/types/testCase'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const testCase = ref<TestCase | null>(null)

// 计算属性
const testCaseId = computed(() => route.params.id as string)

// 生命周期
onMounted(() => {
  loadTestCase()
})

// 方法
const loadTestCase = async () => {
  loading.value = true
  try {
    const response = await testCaseManagementApi.getTestCase(testCaseId.value)
    
    // 转换数据格式
    testCase.value = {
      ...response,
      testType: response.test_type,
      testLevel: response.test_level,
      testSteps: (response.test_steps || []).map((step: any) => ({
        step: step.step_number || step.step,
        action: step.action,
        expectedResult: step.expected || step.expectedResult,
        data: step.data
      })),
      expectedResults: response.expected_results,
      createdAt: response.created_at,
      updatedAt: response.updated_at,
      sessionId: response.session_id
    }
  } catch (error) {
    console.error('加载测试用例失败:', error)
    ElMessage.error('加载测试用例失败')
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.back()
}

const editTestCase = () => {
  router.push(`/test-case/edit/${testCaseId.value}`)
}

const exportTestCase = () => {
  ElMessage.info('导出功能开发中')
}

// 工具方法
const formatTime = (time: string) => {
  return new Date(time).toLocaleString()
}

const getTestTypeLabel = (type: string) => {
  const option = TEST_TYPE_OPTIONS.find(opt => opt.value === type)
  return option?.label || type
}

const getTestLevelLabel = (level: string) => {
  const option = TEST_LEVEL_OPTIONS.find(opt => opt.value === level)
  return option?.label || level
}

const getStatusLabel = (status: string) => {
  const option = STATUS_OPTIONS.find(opt => opt.value === status)
  return option?.label || status
}

const getPriorityType = (priority: string) => {
  const typeMap: Record<string, string> = {
    'P0': 'danger',
    'P1': 'warning',
    'P2': 'primary',
    'P3': 'info',
    'P4': 'info'
  }
  return typeMap[priority] || 'info'
}

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    'draft': 'info',
    'review': 'warning',
    'approved': 'success',
    'deprecated': 'danger'
  }
  return typeMap[status] || 'info'
}
</script>

<style scoped>
.test-case-detail {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.header-right {
  display: flex;
  gap: 12px;
}

.loading-container {
  padding: 20px;
}

.test-case-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-card {
  border-radius: 8px;
}

.card-header {
  font-weight: 600;
  font-size: 16px;
}

.description-content,
.preconditions-content,
.expected-results-content {
  line-height: 1.6;
  color: #606266;
  white-space: pre-wrap;
}

.test-steps {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.step-item {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.step-number {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #409eff;
  color: white;
  border-radius: 50%;
  font-weight: 600;
  font-size: 14px;
}

.step-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-action,
.step-expected,
.step-data {
  line-height: 1.5;
}

.tags-content {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  margin: 0;
}

.error-container {
  padding: 40px;
  text-align: center;
}
</style>
