<template>
  <div class="requirement-coverage-stats">
    <el-row :gutter="16">
      <!-- 覆盖率概览 -->
      <el-col :span="12">
        <el-card class="stats-card" shadow="never">
          <template #header>
            <div class="card-header">
              <el-icon><PieChart /></el-icon>
              <span>需求覆盖率</span>
            </div>
          </template>
          
          <div class="coverage-overview">
            <div class="coverage-chart">
              <div class="progress-circle">
                <el-progress
                  type="circle"
                  :percentage="coverageStats.coverage_rate"
                  :width="120"
                  :stroke-width="8"
                  :color="getCoverageColor(coverageStats.coverage_rate)"
                >
                  <template #default="{ percentage }">
                    <span class="percentage-text">{{ percentage }}%</span>
                  </template>
                </el-progress>
              </div>
            </div>
            
            <div class="coverage-details">
              <div class="detail-item">
                <div class="detail-label">总需求数</div>
                <div class="detail-value total">{{ coverageStats.total_requirements }}</div>
              </div>
              <div class="detail-item">
                <div class="detail-label">已覆盖</div>
                <div class="detail-value covered">{{ coverageStats.covered_requirements }}</div>
              </div>
              <div class="detail-item">
                <div class="detail-label">未覆盖</div>
                <div class="detail-value uncovered">{{ coverageStats.uncovered_requirements }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- 按类型统计 -->
      <el-col :span="12">
        <el-card class="stats-card" shadow="never">
          <template #header>
            <div class="card-header">
              <el-icon><BarChart /></el-icon>
              <span>按类型统计</span>
            </div>
          </template>
          
          <div class="type-stats">
            <div
              v-for="(count, type) in coverageStats.requirements_by_type"
              :key="type"
              class="type-item"
            >
              <div class="type-info">
                <el-tag
                  :color="RequirementTypeColors[type]"
                  style="color: white;"
                  size="small"
                >
                  {{ RequirementTypeLabels[type] }}
                </el-tag>
                <span class="type-count">{{ count }}</span>
              </div>
              <div class="type-bar">
                <div
                  class="type-progress"
                  :style="{
                    width: `${(count / Math.max(...Object.values(coverageStats.requirements_by_type))) * 100}%`,
                    backgroundColor: RequirementTypeColors[type]
                  }"
                ></div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="16" style="margin-top: 16px;">
      <!-- 按优先级统计 -->
      <el-col :span="12">
        <el-card class="stats-card" shadow="never">
          <template #header>
            <div class="card-header">
              <el-icon><TrendCharts /></el-icon>
              <span>按优先级统计</span>
            </div>
          </template>
          
          <div class="priority-stats">
            <div
              v-for="(count, priority) in coverageStats.requirements_by_priority"
              :key="priority"
              class="priority-item"
            >
              <div class="priority-info">
                <el-tag
                  :color="RequirementPriorityColors[priority]"
                  style="color: white;"
                  size="small"
                >
                  {{ RequirementPriorityLabels[priority] }}优先级
                </el-tag>
                <span class="priority-count">{{ count }}</span>
              </div>
              <div class="priority-bar">
                <div
                  class="priority-progress"
                  :style="{
                    width: `${(count / Math.max(...Object.values(coverageStats.requirements_by_priority))) * 100}%`,
                    backgroundColor: RequirementPriorityColors[priority]
                  }"
                ></div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- 覆盖率趋势 -->
      <el-col :span="12">
        <el-card class="stats-card" shadow="never">
          <template #header>
            <div class="card-header">
              <el-icon><DataLine /></el-icon>
              <span>覆盖率评估</span>
            </div>
          </template>
          
          <div class="coverage-assessment">
            <div class="assessment-item">
              <div class="assessment-label">覆盖率等级</div>
              <div class="assessment-value">
                <el-tag
                  :type="getCoverageLevel(coverageStats.coverage_rate).type"
                  size="large"
                >
                  {{ getCoverageLevel(coverageStats.coverage_rate).label }}
                </el-tag>
              </div>
            </div>
            
            <div class="assessment-item">
              <div class="assessment-label">建议</div>
              <div class="assessment-suggestion">
                {{ getCoverageSuggestion(coverageStats.coverage_rate) }}
              </div>
            </div>
            
            <div class="assessment-item">
              <div class="assessment-label">高优先级需求</div>
              <div class="assessment-value">
                {{ coverageStats.requirements_by_priority.high || 0 }} 个
              </div>
            </div>
            
            <div class="assessment-item">
              <div class="assessment-label">安全需求</div>
              <div class="assessment-value">
                {{ coverageStats.requirements_by_type.security || 0 }} 个
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  PieChart,
  BarChart,
  TrendCharts,
  DataLine
} from '@element-plus/icons-vue'

import {
  RequirementTypeLabels,
  RequirementPriorityLabels,
  RequirementTypeColors,
  RequirementPriorityColors
} from '@/types/requirement'
import type { RequirementCoverageStats } from '@/types/requirement'

// Props
interface Props {
  coverageStats: RequirementCoverageStats
}

const props = defineProps<Props>()

// 方法
const getCoverageColor = (percentage: number) => {
  if (percentage >= 80) return '#52c41a'
  if (percentage >= 60) return '#faad14'
  if (percentage >= 40) return '#fa8c16'
  return '#f5222d'
}

const getCoverageLevel = (percentage: number) => {
  if (percentage >= 90) return { label: '优秀', type: 'success' }
  if (percentage >= 80) return { label: '良好', type: 'success' }
  if (percentage >= 60) return { label: '一般', type: 'warning' }
  if (percentage >= 40) return { label: '较差', type: 'warning' }
  return { label: '很差', type: 'danger' }
}

const getCoverageSuggestion = (percentage: number) => {
  if (percentage >= 90) return '覆盖率很高，继续保持！'
  if (percentage >= 80) return '覆盖率良好，可以适当优化未覆盖的需求。'
  if (percentage >= 60) return '覆盖率一般，建议增加测试用例覆盖更多需求。'
  if (percentage >= 40) return '覆盖率较低，需要重点关注未覆盖的需求。'
  return '覆盖率很低，建议尽快补充测试用例。'
}
</script>

<style scoped>
.requirement-coverage-stats {
  padding: 0;
}

.stats-card {
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

.coverage-overview {
  display: flex;
  align-items: center;
  gap: 32px;
}

.coverage-chart {
  flex-shrink: 0;
}

.percentage-text {
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.coverage-details {
  flex: 1;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-size: 14px;
  color: #666;
}

.detail-value {
  font-size: 18px;
  font-weight: 600;
}

.detail-value.total {
  color: #1890ff;
}

.detail-value.covered {
  color: #52c41a;
}

.detail-value.uncovered {
  color: #faad14;
}

.type-stats,
.priority-stats {
  space-y: 16px;
}

.type-item,
.priority-item {
  margin-bottom: 16px;
}

.type-item:last-child,
.priority-item:last-child {
  margin-bottom: 0;
}

.type-info,
.priority-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.type-count,
.priority-count {
  font-weight: 600;
  color: #262626;
}

.type-bar,
.priority-bar {
  height: 8px;
  background-color: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.type-progress,
.priority-progress {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.coverage-assessment {
  space-y: 16px;
}

.assessment-item {
  margin-bottom: 16px;
}

.assessment-item:last-child {
  margin-bottom: 0;
}

.assessment-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.assessment-value {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.assessment-suggestion {
  font-size: 14px;
  color: #595959;
  line-height: 1.5;
  background-color: #f6f8fa;
  padding: 12px;
  border-radius: 6px;
  border-left: 3px solid #1890ff;
}

:deep(.el-card__header) {
  padding: 16px 20px;
  background-color: #fafafa;
  border-bottom: 1px solid #e8e8e8;
}

:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-progress-circle) {
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.el-tag) {
  border: none;
  font-weight: 500;
}
</style>
