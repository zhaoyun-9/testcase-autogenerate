<template>
  <div class="dashboard">
    <div class="page-container">
      <!-- 页面标题 -->
      <div class="page-header animate-slide-up">
        <div class="header-content">
          <h1 class="page-title gradient-text">智能仪表盘</h1>
          <p class="page-subtitle">
            实时监控测试用例生成状态，掌握平台使用情况
          </p>
        </div>
        <div class="header-stats">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.totalCount }}</div>
              <div class="stat-label">总用例数</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 统计卡片 -->
      <el-row :gutter="24" class="stats-row">
        <el-col :span="6">
          <el-card class="stats-card animate-fade-scale" shadow="hover">
            <div class="stats-content">
              <div class="stats-icon primary">
                <el-icon size="28">
                  <Document />
                </el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.totalCount }}</div>
                <div class="stats-label">总测试用例</div>
                <div class="stats-trend">
                  <el-icon><CaretTop /></el-icon>
                  <span>+12%</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stats-card animate-fade-scale" shadow="hover" style="animation-delay: 0.1s">
            <div class="stats-content">
              <div class="stats-icon success">
                <el-icon size="28">
                  <CircleCheck />
                </el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.byStatus?.approved || 0 }}</div>
                <div class="stats-label">已通过用例</div>
                <div class="stats-trend positive">
                  <el-icon><CaretTop /></el-icon>
                  <span>+8%</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="stats-card animate-fade-scale" shadow="hover" style="animation-delay: 0.2s">
            <div class="stats-content">
              <div class="stats-icon warning">
                <el-icon size="28">
                  <Clock />
                </el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.byStatus?.review || 0 }}</div>
                <div class="stats-label">待审核用例</div>
                <div class="stats-trend">
                  <el-icon><Minus /></el-icon>
                  <span>0%</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="stats-card animate-fade-scale" shadow="hover" style="animation-delay: 0.3s">
            <div class="stats-content">
              <div class="stats-icon danger">
                <el-icon size="28">
                  <EditPen />
                </el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-number">{{ stats.byStatus?.draft || 0 }}</div>
                <div class="stats-label">草稿用例</div>
                <div class="stats-trend negative">
                  <el-icon><CaretBottom /></el-icon>
                  <span>-5%</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 图表区域 -->
      <el-row :gutter="24" class="charts-row">
        <el-col :span="12">
          <el-card class="chart-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span>测试类型分布</span>
              </div>
            </template>
            <div class="chart-container">
              <v-chart
                class="chart"
                :option="testTypeChartOption"
                autoresize
              />
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <el-card class="chart-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span>优先级分布</span>
              </div>
            </template>
            <div class="chart-container">
              <v-chart
                class="chart"
                :option="priorityChartOption"
                autoresize
              />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 快速操作 -->
      <el-row :gutter="24" class="actions-row">
        <el-col :span="24">
          <el-card class="actions-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span>快速操作</span>
              </div>
            </template>
            
            <div class="quick-actions">
              <div class="action-item" @click="goToGenerate">
                <div class="action-icon">
                  <el-icon size="24" color="#409EFF">
                    <Plus />
                  </el-icon>
                </div>
                <div class="action-content">
                  <div class="action-title">生成测试用例</div>
                  <div class="action-desc">上传文件或输入需求，智能生成测试用例</div>
                </div>
              </div>
              
              <div class="action-item" @click="goToManagement">
                <div class="action-icon">
                  <el-icon size="24" color="#67C23A">
                    <List />
                  </el-icon>
                </div>
                <div class="action-content">
                  <div class="action-title">管理测试用例</div>
                  <div class="action-desc">查看、编辑和管理已有的测试用例</div>
                </div>
              </div>
              
              <div class="action-item" @click="goToMindmap">
                <div class="action-icon">
                  <el-icon size="24" color="#E6A23C">
                    <Share />
                  </el-icon>
                </div>
                <div class="action-content">
                  <div class="action-title">思维导图</div>
                  <div class="action-desc">以思维导图形式查看测试用例结构</div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { testCaseManagementApi } from '@/api/testCase'
import type { TestCaseStats } from '@/types/testCase'

// 注册ECharts组件
use([
  CanvasRenderer,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent
])

const router = useRouter()

const stats = ref<TestCaseStats>({
  totalCount: 0,
  byType: {},
  byPriority: {},
  byStatus: {},
  byLevel: {},
  recentActivity: {}
})

// 测试类型图表配置
const testTypeChartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{a} <br/>{b}: {c} ({d}%)'
  },
  legend: {
    orient: 'vertical',
    left: 'left'
  },
  series: [
    {
      name: '测试类型',
      type: 'pie',
      radius: '50%',
      data: Object.entries(stats.value.byType || {}).map(([key, value]) => ({
        name: getTestTypeLabel(key),
        value
      })),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }
  ]
}))

// 优先级图表配置
const priorityChartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{a} <br/>{b}: {c} ({d}%)'
  },
  legend: {
    orient: 'vertical',
    left: 'left'
  },
  series: [
    {
      name: '优先级',
      type: 'pie',
      radius: '50%',
      data: Object.entries(stats.value.byPriority || {}).map(([key, value]) => ({
        name: key,
        value
      })),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }
  ]
}))

// 获取测试类型标签
const getTestTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    'functional': '功能测试',
    'interface': '接口测试',
    'performance': '性能测试',
    'security': '安全测试',
    'compatibility': '兼容性测试',
    'usability': '易用性测试'
  }
  return labelMap[type] || type
}

// 快速操作
const goToGenerate = () => {
  router.push('/test-case/generate')
}

const goToManagement = () => {
  router.push('/test-case/management')
}

const goToMindmap = () => {
  router.push('/test-case/mindmap')
}

// 加载统计数据
const loadStats = async () => {
  try {
    const data = await testCaseManagementApi.getStats()
    stats.value = data
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style lang="scss" scoped>
.dashboard {
  .page-header {
    margin-bottom: var(--spacing-2xl);
    padding: var(--spacing-xl);
    background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
    border-radius: var(--border-radius-lg);
    box-shadow: var(--shadow-lg);
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      right: 0;
      width: 300px;
      height: 200px;
      background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
      border-radius: 50%;
      opacity: 0.1;
      transform: translate(30%, -30%);
    }

    .header-content {
      position: relative;
      z-index: 2;

      .page-title {
        font-size: 32px;
        font-weight: 700;
        margin-bottom: var(--spacing-sm);
        line-height: 1.2;
      }

      .page-subtitle {
        font-size: 16px;
        color: var(--text-secondary);
        line-height: 1.5;
        max-width: 500px;
      }
    }

    .header-stats {
      position: relative;
      z-index: 2;

      .stat-item {
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
        padding: var(--spacing-lg);
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: var(--border-radius-lg);
        border: 1px solid rgba(255, 255, 255, 0.2);

        .stat-icon {
          width: 48px;
          height: 48px;
          background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
          border-radius: var(--border-radius);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
        }

        .stat-info {
          .stat-number {
            font-size: 24px;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1;
          }

          .stat-label {
            font-size: 14px;
            color: var(--text-secondary);
            margin-top: 2px;
          }
        }
      }
    }
  }
  
  .stats-row {
    margin-bottom: var(--spacing-2xl);

    .stats-card {
      border: 1px solid var(--border-color);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      overflow: hidden;

      &::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, transparent 0%, rgba(37, 99, 235, 0.02) 100%);
        transition: opacity 0.3s ease;
        opacity: 0;
      }

      &:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-xl);

        &::before {
          opacity: 1;
        }
      }

      .stats-content {
        display: flex;
        align-items: center;
        gap: var(--spacing-lg);
        padding: var(--spacing-lg);
        position: relative;
        z-index: 2;

        .stats-icon {
          width: 56px;
          height: 56px;
          border-radius: var(--border-radius-lg);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          flex-shrink: 0;
          box-shadow: var(--shadow-md);

          &.primary {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-light) 100%);
          }

          &.success {
            background: linear-gradient(135deg, var(--success-color) 0%, #34d399 100%);
          }

          &.warning {
            background: linear-gradient(135deg, var(--warning-color) 0%, #fbbf24 100%);
          }

          &.danger {
            background: linear-gradient(135deg, var(--error-color) 0%, #f87171 100%);
          }
        }

        .stats-info {
          flex: 1;

          .stats-number {
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 4px;
            line-height: 1;
          }

          .stats-label {
            font-size: 14px;
            color: var(--text-secondary);
            font-weight: 500;
            margin-bottom: 6px;
          }

          .stats-trend {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 12px;
            font-weight: 600;

            &.positive {
              color: var(--success-color);
            }

            &.negative {
              color: var(--error-color);
            }

            &:not(.positive):not(.negative) {
              color: var(--text-tertiary);
            }
          }
        }
      }
    }
  }
  
  .charts-row {
    margin-bottom: 24px;
    
    .chart-card {
      .chart-container {
        height: 300px;
        
        .chart {
          width: 100%;
          height: 100%;
        }
      }
    }
  }
  
  .actions-row {
    .actions-card {
      .quick-actions {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 16px;
        
        .action-item {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 16px;
          border: 1px solid var(--el-border-color-light);
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.3s ease;
          
          &:hover {
            border-color: var(--el-color-primary);
            background-color: var(--el-color-primary-light-9);
          }
          
          .action-icon {
            flex-shrink: 0;
          }
          
          .action-content {
            .action-title {
              font-size: 16px;
              font-weight: 500;
              color: var(--el-text-color-primary);
              margin-bottom: 4px;
            }
            
            .action-desc {
              font-size: 14px;
              color: var(--el-text-color-regular);
            }
          }
        }
      }
    }
  }
}
</style>
