<template>
  <el-drawer
    v-model="visible"
    title="需求详情"
    size="60%"
    :before-close="handleClose"
  >
    <div v-loading="loading" class="requirement-detail">
      <template v-if="requirement">
        <!-- 基本信息 -->
        <el-card class="info-card" shadow="never">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>基本信息</span>
            </div>
          </template>
          
          <div class="info-content">
            <el-row :gutter="24">
              <el-col :span="12">
                <div class="info-item">
                  <label>需求编号：</label>
                  <span class="requirement-id">{{ requirement.requirement_id }}</span>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="info-item">
                  <label>创建时间：</label>
                  <span>{{ formatDateTime(requirement.created_at) }}</span>
                </div>
              </el-col>
            </el-row>
            
            <div class="info-item">
              <label>需求标题：</label>
              <span class="requirement-title">{{ requirement.title }}</span>
            </div>
            
            <div class="info-item">
              <label>需求描述：</label>
              <div class="requirement-description">
                {{ requirement.description || '暂无描述' }}
              </div>
            </div>
            
            <el-row :gutter="24">
              <el-col :span="8">
                <div class="info-item">
                  <label>需求类型：</label>
                  <el-tag
                    :color="RequirementTypeColors[requirement.requirement_type]"
                    style="color: white;"
                  >
                    {{ RequirementTypeLabels[requirement.requirement_type] }}
                  </el-tag>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="info-item">
                  <label>优先级：</label>
                  <el-tag
                    :color="RequirementPriorityColors[requirement.priority]"
                    style="color: white;"
                  >
                    {{ RequirementPriorityLabels[requirement.priority] }}
                  </el-tag>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="info-item">
                  <label>状态：</label>
                  <el-tag :color="RequirementStatusColors[requirement.status]">
                    {{ RequirementStatusLabels[requirement.status] }}
                  </el-tag>
                </div>
              </el-col>
            </el-row>
            
            <el-row :gutter="24" v-if="requirement.ai_generated">
              <el-col :span="12">
                <div class="info-item">
                  <label>AI生成：</label>
                  <el-tag type="info">是</el-tag>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="info-item">
                  <label>AI置信度：</label>
                  <span v-if="requirement.ai_confidence">
                    {{ (requirement.ai_confidence * 100).toFixed(1) }}%
                  </span>
                  <span v-else>-</span>
                </div>
              </el-col>
            </el-row>
            
            <div class="info-item" v-if="requirement.source_file_path">
              <label>源文件：</label>
              <span>{{ getFileName(requirement.source_file_path) }}</span>
            </div>
          </div>
        </el-card>

        <!-- 关联的测试用例 -->
        <el-card class="test-cases-card" shadow="never">
          <template #header>
            <div class="card-header">
              <el-icon><List /></el-icon>
              <span>关联的测试用例 ({{ testCases.length }})</span>
              <el-button type="text" @click="loadTestCases">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          
          <div v-if="testCasesLoading" class="loading-wrapper">
            <el-skeleton :rows="3" animated />
          </div>
          
          <div v-else-if="testCases.length === 0" class="empty-wrapper">
            <el-empty description="暂无关联的测试用例" />
          </div>
          
          <div v-else class="test-cases-list">
            <div
              v-for="testCase in testCases"
              :key="testCase.id"
              class="test-case-item"
            >
              <div class="test-case-header">
                <div class="test-case-info">
                  <div class="test-case-title-row">
                    <span class="test-case-title">
                      {{ testCase.test_case?.title || `测试用例 ${testCase.test_case_id}` }}
                    </span>
                    <el-tag
                      :type="testCase.coverage_type === 'full' ? 'success' : 'warning'"
                      size="small"
                    >
                      {{ testCase.coverage_type === 'full' ? '完全覆盖' : '部分覆盖' }}
                    </el-tag>
                  </div>

                  <div v-if="testCase.test_case" class="test-case-tags">
                    <el-tag
                      :color="TestCaseTypeColors[testCase.test_case.test_type]"
                      style="color: white;"
                      size="small"
                    >
                      {{ TestCaseTypeLabels[testCase.test_case.test_type] || testCase.test_case.test_type }}
                    </el-tag>
                    <el-tag
                      :color="TestCasePriorityColors[testCase.test_case.priority]"
                      style="color: white;"
                      size="small"
                    >
                      {{ TestCasePriorityLabels[testCase.test_case.priority] || testCase.test_case.priority }}
                    </el-tag>
                    <el-tag
                      :color="TestCaseStatusColors[testCase.test_case.status]"
                      size="small"
                    >
                      {{ TestCaseStatusLabels[testCase.test_case.status] || testCase.test_case.status }}
                    </el-tag>
                  </div>
                </div>
                <div class="test-case-time">
                  关联时间: {{ formatDateTime(testCase.created_at) }}
                </div>
              </div>

              <div v-if="testCase.test_case?.description" class="test-case-description">
                <strong>测试用例描述:</strong> {{ testCase.test_case.description }}
              </div>

              <div v-if="testCase.coverage_description" class="coverage-description">
                <strong>覆盖说明:</strong> {{ testCase.coverage_description }}
              </div>
            </div>
          </div>
        </el-card>

        <!-- AI模型信息 -->
        <el-card
          v-if="requirement.ai_model_info"
          class="ai-info-card"
          shadow="never"
        >
          <template #header>
            <div class="card-header">
              <el-icon><Setting /></el-icon>
              <span>AI模型信息</span>
            </div>
          </template>
          
          <div class="ai-info-content">
            <pre>{{ JSON.stringify(requirement.ai_model_info, null, 2) }}</pre>
          </div>
        </el-card>
      </template>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Document,
  List,
  Refresh,
  Setting
} from '@element-plus/icons-vue'

import { getRequirement, getRequirementTestCases } from '@/api/requirement'
import {
  RequirementTypeLabels,
  RequirementPriorityLabels,
  RequirementStatusLabels,
  RequirementTypeColors,
  RequirementPriorityColors,
  RequirementStatusColors,
  TestCaseTypeLabels,
  TestCaseLevelLabels,
  TestCasePriorityLabels,
  TestCaseStatusLabels,
  TestCaseTypeColors,
  TestCasePriorityColors,
  TestCaseStatusColors
} from '@/types/requirement'
import type { Requirement, TestCaseRequirement } from '@/types/requirement'

// Props
interface Props {
  visible: boolean
  requirementId: string
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:visible': [value: boolean]
  refresh: []
}>()

// 响应式数据
const loading = ref(false)
const testCasesLoading = ref(false)
const requirement = ref<Requirement | null>(null)
const testCases = ref<TestCaseRequirement[]>([])

// 计算属性
const visible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// 方法
const loadRequirement = async () => {
  if (!props.requirementId) return
  
  loading.value = true
  try {
    requirement.value = await getRequirement(props.requirementId)
  } catch (error) {
    console.error('加载需求详情失败:', error)
    ElMessage.error('加载需求详情失败')
  } finally {
    loading.value = false
  }
}

const loadTestCases = async () => {
  if (!props.requirementId) return
  
  testCasesLoading.value = true
  try {
    testCases.value = await getRequirementTestCases(props.requirementId)
  } catch (error) {
    console.error('加载关联测试用例失败:', error)
    ElMessage.error('加载关联测试用例失败')
  } finally {
    testCasesLoading.value = false
  }
}

const handleClose = () => {
  visible.value = false
}

const formatDateTime = (dateTime: string) => {
  return new Date(dateTime).toLocaleString('zh-CN')
}

const getFileName = (filePath: string) => {
  return filePath.split(/[/\\]/).pop() || filePath
}

// 监听器
watch(
  () => props.requirementId,
  (newId) => {
    if (newId && props.visible) {
      loadRequirement()
      loadTestCases()
    }
  },
  { immediate: true }
)

watch(
  () => props.visible,
  (newVisible) => {
    if (newVisible && props.requirementId) {
      loadRequirement()
      loadTestCases()
    }
  }
)
</script>

<style scoped>
.requirement-detail {
  padding: 0 8px;
}

.info-card,
.test-cases-card,
.ai-info-card {
  margin-bottom: 16px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #262626;
}

.card-header .el-button {
  margin-left: auto;
}

.info-content {
  padding: 8px 0;
}

.info-item {
  margin-bottom: 16px;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-item label {
  display: inline-block;
  width: 100px;
  font-weight: 500;
  color: #666;
  margin-right: 8px;
}

.requirement-id {
  font-family: 'Monaco', 'Menlo', monospace;
  background-color: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.requirement-title {
  font-weight: 500;
  color: #262626;
}

.requirement-description {
  background-color: #fafafa;
  padding: 12px;
  border-radius: 6px;
  line-height: 1.6;
  color: #595959;
  white-space: pre-wrap;
  margin-top: 4px;
}

.loading-wrapper,
.empty-wrapper {
  padding: 24px;
  text-align: center;
}

.test-cases-list {
  max-height: 400px;
  overflow-y: auto;
}

.test-case-item {
  padding: 16px;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  margin-bottom: 12px;
  background-color: #fafafa;
}

.test-case-item:last-child {
  margin-bottom: 0;
}

.test-case-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.test-case-info {
  flex: 1;
}

.test-case-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.test-case-title {
  font-weight: 500;
  color: #262626;
  flex: 1;
}

.test-case-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.test-case-time {
  font-size: 12px;
  color: #8c8c8c;
}

.test-case-description,
.coverage-description {
  color: #595959;
  line-height: 1.5;
  font-size: 14px;
  margin-top: 8px;
  padding: 8px 12px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #1890ff;
}

.coverage-description {
  border-left-color: #52c41a;
}

.ai-info-content {
  background-color: #f5f5f5;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
}

.ai-info-content pre {
  margin: 0;
  font-size: 12px;
  color: #262626;
  white-space: pre-wrap;
  word-break: break-all;
}

:deep(.el-drawer__header) {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e8e8e8;
}

:deep(.el-drawer__body) {
  padding: 0 20px 20px;
}

:deep(.el-card__header) {
  padding: 16px 20px;
  background-color: #fafafa;
  border-bottom: 1px solid #e8e8e8;
}

:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-tag) {
  border: none;
  font-weight: 500;
}
</style>
