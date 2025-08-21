<template>
  <div class="test-case-management">
    <!-- 页面头部 -->
    <TcPageHeader
      title="测试用例管理"
      subtitle="管理和维护测试用例，支持批量操作、分类筛选和导出功能"
      :actions="headerActions"
    >
      <template #extra>
        <!-- 统计卡片 -->
        <div class="stats-cards">
          <div class="stat-card">
            <div class="stat-icon">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总用例数</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon passed">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.passed }}</div>
              <div class="stat-label">通过</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon failed">
              <el-icon><CircleClose /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.failed }}</div>
              <div class="stat-label">失败</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon pending">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.pending }}</div>
              <div class="stat-label">待执行</div>
            </div>
          </div>
        </div>
      </template>
    </TcPageHeader>

    <!-- 搜索和筛选 -->
    <TcCard class="search-card">
      <TcSearchBar
        :fields="searchFields"
        v-model="searchForm"
        :loading="loading"
        :show-expand="true"
        :default-expanded="false"
        @search="handleSearch"
        @reset="handleReset"
      />
    </TcCard>

    <!-- 测试用例列表 -->
    <TcCard class="list-card">
      <template #header>
        <div class="list-header">
          <div class="header-info">
            <h3>测试用例列表</h3>
            <p>共 {{ pagination.total }} 个测试用例</p>
          </div>
          <div class="header-actions">
            <el-button-group>
              <el-button
                :type="viewMode === 'table' ? 'primary' : 'default'"
                :icon="Grid"
                @click="viewMode = 'table'"
              >
                表格视图
              </el-button>
              <el-button
                :type="viewMode === 'card' ? 'primary' : 'default'"
                :icon="List"
                @click="viewMode = 'card'"
              >
                卡片视图
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>

      <!-- 表格视图 -->
      <div v-if="viewMode === 'table'" class="table-view">
        <el-table
          :data="testCases"
          :loading="loading"
          stripe
          border
          style="width: 100%"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="55" />

          <el-table-column
            prop="title"
            label="测试用例标题"
            min-width="300"
            show-overflow-tooltip
          />

          <el-table-column
            prop="testType"
            label="测试类型"
            width="120"
          >
            <template #default="{ row }">
              <el-tag :type="getTestTypeTagType(row.testType)" size="small">
                {{ getTestTypeLabel(row.testType) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column
            prop="priority"
            label="优先级"
            width="100"
          >
            <template #default="{ row }">
              <el-tag :type="getPriorityTagType(row.priority)" size="small">
                {{ row.priority }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column
            prop="status"
            label="状态"
            width="100"
          >
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)" size="small">
                {{ getStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column
            prop="testSteps"
            label="测试步骤"
            min-width="300"
          >
            <template #default="{ row }">
              <div v-if="row.testSteps && row.testSteps.length > 0" class="test-steps-summary">
                <div class="steps-count">共 {{ row.testSteps.length }} 个步骤</div>
                <div class="steps-preview">
                  <div
                    v-for="(step, index) in row.testSteps.slice(0, 2)"
                    :key="index"
                    class="step-preview-item"
                  >
                    <div class="step-number">{{ step.step }}</div>
                    <div class="step-content">
                      <div class="step-action">{{ step.action }}</div>
                      <div v-if="step.expectedResult" class="step-expected">
                        预期: {{ step.expectedResult }}
                      </div>
                    </div>
                  </div>
                  <div v-if="row.testSteps.length > 2" class="more-steps">
                    还有 {{ row.testSteps.length - 2 }} 个步骤...
                  </div>
                </div>
              </div>
              <span v-else class="text-gray-400">无测试步骤</span>
            </template>
          </el-table-column>

          <el-table-column
            prop="createdAt"
            label="创建时间"
            width="180"
          >
            <template #default="{ row }">
              {{ formatTime(row.createdAt) }}
            </template>
          </el-table-column>

          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="handleViewTestCase(row)">查看</el-button>
              <el-button size="small" @click="handleEditTestCase(row)">编辑</el-button>
              <el-button size="small" @click="handleCopyTestCase(row)">复制</el-button>
              <el-button size="small" type="danger" @click="handleDeleteTestCase(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>

      <!-- 卡片视图 -->
      <div v-else class="test-case-cards">
        <el-card
          v-for="testCase in testCases"
          :key="testCase.id"
          class="test-case-card"
          shadow="hover"
        >
          <template #header>
            <div class="card-header">
              <span>{{ testCase.title }}</span>
              <div class="card-actions">
                <el-button size="small" @click="handleViewTestCase(testCase)">查看</el-button>
                <el-button size="small" @click="handleEditTestCase(testCase)">编辑</el-button>
                <el-button size="small" @click="handleCopyTestCase(testCase)">复制</el-button>
                <el-button size="small" type="danger" @click="handleDeleteTestCase(testCase)">删除</el-button>
              </div>
            </div>
          </template>
          <div class="test-case-content">
            <p><strong>描述:</strong> {{ testCase.description || '无' }}</p>
            <p><strong>类型:</strong> {{ testCase.testType }}</p>
            <p><strong>级别:</strong> {{ testCase.testLevel }}</p>
            <p><strong>优先级:</strong> {{ testCase.priority }}</p>
            <p><strong>状态:</strong> {{ testCase.status }}</p>

            <!-- 测试步骤预览 -->
            <div v-if="testCase.testSteps && testCase.testSteps.length > 0" class="test-steps-preview">
              <p><strong>测试步骤 ({{ testCase.testSteps.length }}):</strong></p>
              <div class="steps-list">
                <div
                  v-for="(step, index) in testCase.testSteps.slice(0, 3)"
                  :key="index"
                  class="step-item"
                >
                  <div class="step-header">
                    <span class="step-number">步骤{{ step.step }}</span>
                  </div>
                  <div class="step-action">
                    <strong>操作:</strong> {{ step.action }}
                  </div>
                  <div v-if="step.expectedResult" class="step-expected">
                    <strong>预期:</strong> {{ step.expectedResult }}
                  </div>
                </div>
                <div v-if="testCase.testSteps.length > 3" class="more-steps">
                  还有 {{ testCase.testSteps.length - 3 }} 个步骤...
                </div>
              </div>
            </div>

            <!-- 最终期望结果 -->
            <div v-if="testCase.expectedResults" class="final-expected-results">
              <p><strong>最终期望结果:</strong></p>
              <div class="expected-content">{{ testCase.expectedResults }}</div>
            </div>
          </div>
        </el-card>

        <!-- 空状态 -->
        <el-empty
          v-if="testCases.length === 0 && !loading"
          description="暂无测试用例数据"
        >
          <el-button type="primary" @click="goToGenerate">
            <el-icon><Plus /></el-icon>
            生成测试用例
          </el-button>
        </el-empty>
      </div>

      <!-- 分页 -->
      <div v-if="pagination.total > 0" class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </TcCard>

    <!-- 测试用例详情对话框 -->
    <TestCaseDetailDialog
      v-model="detailDialogVisible"
      :test-case="currentTestCase"
      @save="handleSaveTestCase"
    />

    <!-- 批量编辑对话框 -->
    <BatchEditDialog
      v-model="batchEditDialogVisible"
      :selected-ids="selectedTestCases"
      @save="handleBatchSave"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onActivated, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { debounce } from 'lodash-es'
import {
  Plus,
  Search,
  Download,
  Upload,
  Edit,
  Delete,
  View,
  Copy,
  Document,
  CircleCheck,
  CircleClose,
  Clock,
  Grid,
  List,
  Filter,
  Refresh
} from '@element-plus/icons-vue'

import {
  TcPageHeader,
  TcCard,
  TcButton
} from '@/components/ui'

import { testCaseManagementApi, exportApi } from '@/api/testCase'
import TestCaseList from '@/components/TestCaseList/index.vue'
import TestCaseDetailDialog from '@/components/TestCaseDetailDialog/index.vue'
import BatchEditDialog from '@/components/BatchEditDialog/index.vue'
import type { TestCase, TestCaseFilters } from '@/types/testCase'
import {
  TEST_TYPE_OPTIONS,
  PRIORITY_OPTIONS,
  STATUS_OPTIONS
} from '@/types/testCase'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const testCases = ref<TestCase[]>([])
const selectedTestCases = ref<string[]>([])
const currentTestCase = ref<TestCase | null>(null)
const detailDialogVisible = ref(false)
const batchEditDialogVisible = ref(false)
const viewMode = ref<'table' | 'card'>('table')

// 搜索表单
const searchForm = ref({
  search: '',
  testType: [],
  testLevel: [],
  priority: [],
  status: [],
  tags: [],
  sessionId: route.query.sessionId as string || undefined
})

// 分页信息
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 统计数据
const stats = reactive({
  total: 0,
  passed: 0,
  failed: 0,
  pending: 0
})

// 选项数据
const testTypeOptions = TEST_TYPE_OPTIONS
const priorityOptions = PRIORITY_OPTIONS
const statusOptions = STATUS_OPTIONS

// headerActions moved after function definitions to avoid hoisting issues

// 搜索字段配置
const searchFields = computed(() => [
  {
    prop: 'search',
    label: '搜索',
    type: 'input' as const,
    placeholder: '搜索测试用例标题或描述',
    span: 8
  },
  {
    prop: 'testType',
    label: '测试类型',
    type: 'select' as const,
    multiple: true,
    options: testTypeOptions,
    placeholder: '选择测试类型',
    span: 6
  },
  {
    prop: 'priority',
    label: '优先级',
    type: 'select' as const,
    multiple: true,
    options: priorityOptions,
    placeholder: '选择优先级',
    span: 5
  },
  {
    prop: 'status',
    label: '状态',
    type: 'select' as const,
    multiple: true,
    options: statusOptions,
    placeholder: '选择状态',
    span: 5
  }
])

// 表格列配置
const tableColumns = computed(() => [
  {
    prop: 'title',
    label: '测试用例标题',
    minWidth: 300,
    showOverflowTooltip: true
  },
  {
    prop: 'testType',
    label: '测试类型',
    width: 120,
    render: (row: TestCase) => {
      const option = testTypeOptions.find(opt => opt.value === row.testType)
      return option ? option.label : row.testType
    }
  },
  {
    prop: 'priority',
    label: '优先级',
    width: 100,
    render: (row: TestCase) => {
      const option = priorityOptions.find(opt => opt.value === row.priority)
      return `<el-tag type="${getPriorityTagType(row.priority)}" size="small">${option?.label || row.priority}</el-tag>`
    }
  },
  {
    prop: 'status',
    label: '状态',
    width: 100,
    render: (row: TestCase) => {
      const option = statusOptions.find(opt => opt.value === row.status)
      return `<el-tag type="${getStatusTagType(row.status)}" size="small">${option?.label || row.status}</el-tag>`
    }
  },
  {
    prop: 'createdAt',
    label: '创建时间',
    width: 180,
    formatter: (row: TestCase) => formatTime(row.createdAt)
  }
])

// tableActions moved after function definitions to avoid hoisting issues

// 批量操作方法定义
function handleBatchEdit() {
  if (selectedTestCases.value.length === 0) {
    ElMessage.warning('请先选择要编辑的测试用例')
    return
  }
  batchEditDialogVisible.value = true
}

async function handleBatchDelete() {
  if (selectedTestCases.value.length === 0) {
    ElMessage.warning('请先选择要删除的测试用例')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedTestCases.value.length} 个测试用例吗？此操作不可撤销。`,
      '确认批量删除',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )

    const ids = selectedTestCases.value
    await testCaseManagementApi.batchDeleteTestCases(ids)
    ElMessage.success('批量删除成功')
    loadTestCases()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

// batchActions moved to end of script

// 工具函数已移动到文件末尾

// 搜索和筛选
const handleSearch = () => {
  pagination.page = 1
  loadTestCases()
}

const handleReset = () => {
  Object.assign(searchForm.value, {
    search: '',
    testType: [],
    testLevel: [],
    priority: [],
    status: [],
    tags: [],
    sessionId: searchForm.value.sessionId // 保留sessionId
  })
  pagination.page = 1
  loadTestCases()
}

// 批量操作
function handleBatchAction(command: string) {
  switch (command) {
    case 'batch-export':
      handleBatchExport()
      break
    case 'batch-delete':
      handleBatchDelete()
      break
  }
}

const handleBatchExport = async () => {
  if (selectedTestCases.value.length === 0) {
    ElMessage.warning('请先选择要导出的测试用例')
    return
  }

  try {
    const blob = await exportApi.exportTestCases({
      ids: selectedTestCases.value,
      format: 'excel'
    })

    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `测试用例_${new Date().toISOString().slice(0, 10)}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// 加载测试用例列表
const loadTestCases = async () => {
  try {
    loading.value = true

    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      search: searchForm.value.search || undefined,
      test_type: searchForm.value.testType.length > 0 ? searchForm.value.testType : undefined,
      test_level: searchForm.value.testLevel.length > 0 ? searchForm.value.testLevel : undefined,
      priority: searchForm.value.priority.length > 0 ? searchForm.value.priority : undefined,
      status: searchForm.value.status.length > 0 ? searchForm.value.status : undefined,
      tags: searchForm.value.tags.length > 0 ? searchForm.value.tags : undefined,
      session_id: searchForm.value.sessionId
    }

    const response = await testCaseManagementApi.getTestCases(params)

    // 转换后端数据格式到前端格式
    testCases.value = response.data.map(item => ({
      ...item,
      testType: item.test_type,
      testLevel: item.test_level,
      testSteps: (item.test_steps || []).map((step: any) => ({
        step: step.step_number || step.step,
        action: step.action,
        expectedResult: step.expected || step.expectedResult,
        data: step.data
      })),
      expectedResults: item.expected_results,
      createdAt: item.created_at,
      updatedAt: item.updated_at,
      sessionId: item.session_id
    }))
    pagination.total = response.total

  } catch (error) {
    console.error('加载测试用例失败:', error)
    ElMessage.error('加载测试用例失败')
  } finally {
    loading.value = false
  }
}

// 加载统计数据
const loadStats = async () => {
  try {
    const response = await testCaseManagementApi.getTestCaseStats()
    Object.assign(stats, response)
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 处理选择变化
const handleSelectionChange = (selection: TestCase[]) => {
  selectedTestCases.value = selection.map(item => item.id)
}

// 查看测试用例
function handleViewTestCase(testCase: TestCase) {
  currentTestCase.value = testCase
  detailDialogVisible.value = true
}

// 编辑测试用例
function handleEditTestCase(testCase: TestCase) {
  router.push({
    name: 'TestCaseEdit',
    params: { id: testCase.id }
  })
}

// 执行测试用例
const handleExecuteTestCase = async (testCase: TestCase) => {
  try {
    await testCaseManagementApi.executeTestCase(testCase.id)
    ElMessage.success('测试用例执行成功')
    loadTestCases()
    loadStats()
  } catch (error) {
    ElMessage.error('测试用例执行失败')
  }
}

// 复制测试用例
async function handleCopyTestCase(testCase: TestCase) {
  try {
    const newTestCase = {
      ...testCase,
      title: `${testCase.title} (副本)`,
      status: 'draft'
    }
    delete newTestCase.id
    delete newTestCase.createdAt
    delete newTestCase.updatedAt

    await testCaseManagementApi.createTestCase(newTestCase)
    ElMessage.success('复制成功')
    loadTestCases()
  } catch (error) {
    console.error('复制测试用例失败:', error)
    ElMessage.error('复制失败')
  }
}

// 删除测试用例
async function handleDeleteTestCase(testCase: TestCase) {
  try {
    await ElMessageBox.confirm(
      `确定要删除测试用例"${testCase.title}"吗？此操作不可撤销。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )

    await testCaseManagementApi.deleteTestCase(testCase.id)
    ElMessage.success('删除成功')
    loadTestCases()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除测试用例失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 保存测试用例
const handleSaveTestCase = async (testCase: TestCase) => {
  try {
    if (testCase.id) {
      await testCaseManagementApi.updateTestCase(testCase.id, testCase)
      ElMessage.success('更新成功')
    } else {
      await testCaseManagementApi.createTestCase(testCase)
      ElMessage.success('创建成功')
    }
    
    detailDialogVisible.value = false
    loadTestCases()
  } catch (error) {
    console.error('保存测试用例失败:', error)
    ElMessage.error('保存失败')
  }
}

// 批量保存
const handleBatchSave = async (updates: any) => {
  try {
    // 这里应该调用批量更新API
    // await testCaseManagementApi.batchUpdateTestCases(selectedTestCases.value, updates)
    
    ElMessage.success('批量更新成功')
    batchEditDialogVisible.value = false
    selectedTestCases.value = []
    loadTestCases()
  } catch (error) {
    console.error('批量更新失败:', error)
    ElMessage.error('批量更新失败')
  }
}

// 分页处理
const handlePageChange = (page: number) => {
  pagination.page = page
  loadTestCases()
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadTestCases()
}

// 跳转到生成页面
function goToGenerate() {
  router.push('/test-case/generate')
}

// 页面头部操作配置 (using function references to avoid hoisting issues)
const headerActions = computed(() => [
  {
    type: 'button' as const,
    label: '生成测试用例',
    buttonType: 'primary' as const,
    icon: Plus,
    handler: () => goToGenerate()
  },
  {
    type: 'button' as const,
    label: '思维导图',
    buttonType: 'default' as const,
    icon: 'Share',
    handler: () => router.push('/test-case/mindmap')
  },
  {
    type: 'dropdown' as const,
    label: '批量操作',
    items: [
      {
        label: '批量导出',
        command: 'batch-export',
        icon: Download,
        disabled: selectedTestCases.value.length === 0
      },
      {
        label: '批量删除',
        command: 'batch-delete',
        icon: Delete,
        disabled: selectedTestCases.value.length === 0
      }
    ],
    handler: (command: string) => handleBatchAction(command)
  }
])

// 表格操作配置 (using function references to avoid hoisting issues)
const tableActions = [
  {
    label: '查看',
    type: 'primary' as const,
    size: 'small' as const,
    icon: 'View',
    handler: (row: TestCase) => handleViewTestCase(row)
  },
  {
    label: '编辑',
    type: 'default' as const,
    size: 'small' as const,
    icon: 'Edit',
    handler: (row: TestCase) => handleEditTestCase(row)
  },
  {
    label: '复制',
    type: 'default' as const,
    size: 'small' as const,
    icon: 'Copy',
    handler: (row: TestCase) => handleCopyTestCase(row)
  },
  {
    label: '删除',
    type: 'danger' as const,
    size: 'small' as const,
    icon: 'Delete',
    handler: (row: TestCase) => handleDeleteTestCase(row)
  }
]

// 批量操作配置 (using function references to avoid hoisting issues)
const batchActions = [
  {
    label: '批量编辑',
    type: 'primary' as const,
    icon: 'Edit',
    disabled: computed(() => selectedTestCases.value.length === 0),
    handler: () => handleBatchEdit()
  },
  {
    label: '批量删除',
    type: 'danger' as const,
    icon: 'Delete',
    disabled: computed(() => selectedTestCases.value.length === 0),
    handler: () => handleBatchDelete()
  }
]

// 监听路由变化
watch(() => route.query.sessionId, (sessionId) => {
  searchForm.value.sessionId = sessionId as string
  loadTestCases()
})

onMounted(() => {
  loadTestCases()
  loadStats()
})

// 当组件被keep-alive激活时重新加载数据
onActivated(() => {
  loadTestCases()
  loadStats()
})

// 辅助函数
const getTestTypeTagType = (testType: string) => {
  const typeMap: Record<string, string> = {
    'functional': 'primary',
    'interface': 'success',
    'performance': 'warning',
    'security': 'danger',
    'compatibility': 'info',
    'usability': ''
  }
  return typeMap[testType] || ''
}

const getTestTypeLabel = (testType: string) => {
  const option = testTypeOptions.find(opt => opt.value === testType)
  return option?.label || testType
}

const getPriorityTagType = (priority: string) => {
  const typeMap: Record<string, string> = {
    'P0': 'danger',
    'P1': 'warning',
    'P2': 'primary',
    'P3': 'info',
    'P4': ''
  }
  return typeMap[priority] || ''
}

const getStatusTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    'draft': 'info',
    'review': 'warning',
    'approved': 'success',
    'deprecated': 'danger'
  }
  return typeMap[status] || ''
}

const getStatusLabel = (status: string) => {
  const option = statusOptions.find(opt => opt.value === status)
  return option?.label || status
}

const formatTime = (time: string) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style lang="scss" scoped>
.test-case-management {
  .stats-cards {
    display: flex;
    gap: var(--spacing-lg);
    margin-top: var(--spacing-lg);

    .stat-card {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-lg);
      background: var(--bg-primary);
      border-radius: var(--border-radius-lg);
      box-shadow: var(--shadow-sm);
      min-width: 140px;

      .stat-icon {
        width: 40px;
        height: 40px;
        border-radius: var(--border-radius-lg);
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--primary-100);
        color: var(--primary-color);
        font-size: 20px;

        &.passed {
          background: var(--success-100);
          color: var(--success-color);
        }

        &.failed {
          background: var(--error-100);
          color: var(--error-color);
        }

        &.pending {
          background: var(--warning-100);
          color: var(--warning-color);
        }
      }

      .stat-content {
        .stat-value {
          font-size: var(--font-size-xl);
          font-weight: var(--font-weight-bold);
          color: var(--text-primary);
          line-height: 1;
        }

        .stat-label {
          font-size: var(--font-size-sm);
          color: var(--text-secondary);
          margin-top: var(--spacing-xs);
        }
      }
    }
  }

  .search-card {
    margin: var(--spacing-xl) 0;
  }

  .table-view {
    .pagination-wrapper {
      display: flex;
      justify-content: center;
      margin-top: var(--spacing-lg);
      padding: var(--spacing-lg) 0;
    }

    .test-steps-summary {
      .steps-count {
        font-size: 12px;
        color: var(--el-color-primary);
        margin-bottom: 8px;
        font-weight: 500;
      }

      .steps-preview {
        .step-preview-item {
          display: flex;
          gap: 8px;
          margin-bottom: 6px;
          font-size: 12px;

          .step-number {
            background: var(--el-color-primary-light-8);
            color: var(--el-color-primary);
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 500;
            flex-shrink: 0;
            min-width: 20px;
            text-align: center;
          }

          .step-content {
            flex: 1;

            .step-action {
              color: var(--el-text-color-primary);
              line-height: 1.4;
              margin-bottom: 2px;
            }

            .step-expected {
              color: var(--el-text-color-secondary);
              font-size: 11px;
              line-height: 1.3;
            }
          }
        }

        .more-steps {
          font-size: 11px;
          color: var(--el-text-color-placeholder);
          font-style: italic;
          text-align: center;
          margin-top: 4px;
        }
      }
    }
  }

  .list-card {
    .list-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-info {
        h3 {
          font-size: var(--font-size-lg);
          font-weight: var(--font-weight-semibold);
          color: var(--text-primary);
          margin: 0 0 var(--spacing-xs) 0;
        }

        p {
          font-size: var(--font-size-sm);
          color: var(--text-secondary);
          margin: 0;
        }
      }
    }

    .test-case-cards {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
      gap: var(--spacing-lg);
      padding: var(--spacing-lg) 0;

      .test-steps-preview {
        margin-top: 16px;
        padding-top: 12px;
        border-top: 1px solid var(--el-border-color-lighter);

        .steps-list {
          margin: 8px 0;

          .step-item {
            margin-bottom: 12px;
            padding: 8px;
            background: var(--el-fill-color-lighter);
            border-radius: 6px;
            border-left: 3px solid var(--el-color-primary);

            .step-header {
              margin-bottom: 6px;

              .step-number {
                background: var(--el-color-primary);
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 500;
              }
            }

            .step-action {
              font-size: 13px;
              color: var(--el-text-color-primary);
              line-height: 1.4;
              margin-bottom: 4px;
            }

            .step-expected {
              font-size: 12px;
              color: var(--el-text-color-secondary);
              line-height: 1.3;
            }
          }

          .more-steps {
            font-size: 12px;
            color: var(--el-text-color-placeholder);
            font-style: italic;
            text-align: center;
            margin-top: 8px;
          }
        }
      }

      .final-expected-results {
        margin-top: 16px;
        padding-top: 12px;
        border-top: 1px solid var(--el-border-color-lighter);

        .expected-content {
          margin-top: 8px;
          padding: 12px;
          background: var(--el-color-success-light-9);
          border: 1px solid var(--el-color-success-light-7);
          border-radius: 6px;
          font-size: 13px;
          color: var(--el-text-color-primary);
          line-height: 1.5;
          white-space: pre-wrap;
        }
      }
    }

    .pagination-container {
      display: flex;
      justify-content: center;
      padding: var(--spacing-lg) 0;
      border-top: 1px solid var(--border-color-light);
      margin-top: var(--spacing-lg);
    }
  }

  .list-card {
    .pagination-container {
      display: flex;
      justify-content: center;
      margin-top: 24px;
    }
  }
}
</style>
