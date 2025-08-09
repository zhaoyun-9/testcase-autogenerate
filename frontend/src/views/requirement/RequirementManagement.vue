<template>
  <div class="requirement-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">需求管理</h1>
        <p class="page-description">管理项目需求，查看需求覆盖情况和测试用例关联</p>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon total">
                <el-icon><Document /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ coverageStats.total_requirements }}</div>
                <div class="stats-label">总需求数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon covered">
                <el-icon><Check /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ coverageStats.covered_requirements }}</div>
                <div class="stats-label">已覆盖</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon uncovered">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ coverageStats.uncovered_requirements }}</div>
                <div class="stats-label">未覆盖</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon rate">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ coverageStats.coverage_rate }}%</div>
                <div class="stats-label">覆盖率</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="filter-card">
      <div class="filter-content">
        <el-row :gutter="16" align="middle">
          <el-col :span="8">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索需求标题、描述或编号"
              clearable
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="4">
            <el-select
              v-model="filterType"
              placeholder="需求类型"
              clearable
              @change="handleFilter"
            >
              <el-option
                v-for="(label, value) in RequirementTypeLabels"
                :key="value"
                :label="label"
                :value="value"
              />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-select
              v-model="filterPriority"
              placeholder="优先级"
              clearable
              @change="handleFilter"
            >
              <el-option
                v-for="(label, value) in RequirementPriorityLabels"
                :key="value"
                :label="label"
                :value="value"
              />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-select
              v-model="filterStatus"
              placeholder="状态"
              clearable
              @change="handleFilter"
            >
              <el-option
                v-for="(label, value) in RequirementStatusLabels"
                :key="value"
                :label="label"
                :value="value"
              />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 需求列表 -->
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>需求列表</span>
          <el-button type="text" @click="refreshData">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="requirements"
        stripe
        @row-click="handleRowClick"
        style="cursor: pointer;"
      >
        <el-table-column prop="requirement_id" label="需求编号" width="150" />
        <el-table-column prop="title" label="需求标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="requirement_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag
              :color="RequirementTypeColors[row.requirement_type]"
              style="color: white;"
            >
              {{ RequirementTypeLabels[row.requirement_type] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag
              :color="RequirementPriorityColors[row.priority]"
              style="color: white;"
            >
              {{ RequirementPriorityLabels[row.priority] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :color="RequirementStatusColors[row.status]">
              {{ RequirementStatusLabels[row.status] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ai_confidence" label="AI置信度" width="120">
          <template #default="{ row }">
            <span v-if="row.ai_confidence">{{ (row.ai_confidence * 100).toFixed(1) }}%</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="text" size="small" @click.stop="viewRequirement(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 需求详情抽屉 -->
    <RequirementDetail
      v-model:visible="detailVisible"
      :requirement-id="selectedRequirementId"
      @refresh="refreshData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Document,
  Check,
  Warning,
  TrendCharts,
  Search,
  Refresh
} from '@element-plus/icons-vue'

import { getRequirements, getRequirementCoverageStats } from '@/api/requirement'
import RequirementDetail from './components/RequirementDetail.vue'
import {
  RequirementTypeLabels,
  RequirementPriorityLabels,
  RequirementStatusLabels,
  RequirementTypeColors,
  RequirementPriorityColors,
  RequirementStatusColors
} from '@/types/requirement'
import type {
  Requirement,
  RequirementQuery,
  RequirementCoverageStats
} from '@/types/requirement'

// 响应式数据
const loading = ref(false)
const requirements = ref<Requirement[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 搜索和筛选
const searchKeyword = ref('')
const filterType = ref('')
const filterPriority = ref('')
const filterStatus = ref('')

// 统计数据
const coverageStats = ref<RequirementCoverageStats>({
  total_requirements: 0,
  covered_requirements: 0,
  uncovered_requirements: 0,
  coverage_rate: 0,
  requirements_by_type: {},
  requirements_by_priority: {}
})

// 详情抽屉
const detailVisible = ref(false)
const selectedRequirementId = ref('')

// 方法
const loadRequirements = async () => {
  loading.value = true
  try {
    const query: RequirementQuery = {
      page: currentPage.value,
      page_size: pageSize.value
    }

    if (searchKeyword.value) {
      query.keyword = searchKeyword.value
    }
    if (filterType.value) {
      query.requirement_type = filterType.value as any
    }
    if (filterPriority.value) {
      query.priority = filterPriority.value as any
    }
    if (filterStatus.value) {
      query.status = filterStatus.value as any
    }

    const response = await getRequirements(query)
    requirements.value = response.items
    total.value = response.total
  } catch (error) {
    console.error('加载需求列表失败:', error)
    ElMessage.error('加载需求列表失败')
  } finally {
    loading.value = false
  }
}

const loadCoverageStats = async () => {
  try {
    const stats = await getRequirementCoverageStats()
    coverageStats.value = stats
  } catch (error) {
    console.error('加载覆盖统计失败:', error)
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadRequirements()
}

const handleFilter = () => {
  currentPage.value = 1
  loadRequirements()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  loadRequirements()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadRequirements()
}

const handleRowClick = (row: Requirement) => {
  viewRequirement(row)
}

const viewRequirement = (requirement: Requirement) => {
  selectedRequirementId.value = requirement.id
  detailVisible.value = true
}

const refreshData = () => {
  loadRequirements()
  loadCoverageStats()
}

const formatDateTime = (dateTime: string) => {
  return new Date(dateTime).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadRequirements()
  loadCoverageStats()
})
</script>

<style scoped>
.requirement-management {
  padding: 24px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.header-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 32px;
  border-radius: 12px;
  color: white;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.page-description {
  font-size: 16px;
  opacity: 0.9;
  margin: 0;
}

.stats-cards {
  margin-bottom: 24px;
}

.stats-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.stats-content {
  display: flex;
  align-items: center;
  padding: 8px 0;
}

.stats-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
  color: white;
}

.stats-icon.total {
  background: linear-gradient(135deg, #1890ff, #36cfc9);
}

.stats-icon.covered {
  background: linear-gradient(135deg, #52c41a, #73d13d);
}

.stats-icon.uncovered {
  background: linear-gradient(135deg, #faad14, #ffc53d);
}

.stats-icon.rate {
  background: linear-gradient(135deg, #722ed1, #b37feb);
}

.stats-info {
  flex: 1;
}

.stats-number {
  font-size: 24px;
  font-weight: 600;
  color: #262626;
  line-height: 1;
}

.stats-label {
  font-size: 14px;
  color: #8c8c8c;
  margin-top: 4px;
}

.filter-card {
  margin-bottom: 24px;
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.filter-content {
  padding: 8px 0;
}

.table-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

:deep(.el-table) {
  border-radius: 8px;
}

:deep(.el-table th) {
  background-color: #fafafa;
  font-weight: 600;
}

:deep(.el-table tr:hover > td) {
  background-color: #f0f9ff;
}

:deep(.el-tag) {
  border: none;
  font-weight: 500;
}
</style>
