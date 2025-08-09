<template>
  <el-dialog
    v-model="visible"
    title="项目详情"
    width="800px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div v-if="project" class="project-detail">
      <!-- 项目基本信息 -->
      <div class="detail-section">
        <div class="section-header">
          <h3>基本信息</h3>
          <el-button type="primary" size="small" @click="handleEdit">
            <el-icon><Edit /></el-icon>
            编辑项目
          </el-button>
        </div>
        
        <div class="project-info-card">
          <div class="project-avatar-large" :style="{ backgroundColor: projectUtils.generateProjectColor(project.name) }">
            {{ project.name.charAt(0).toUpperCase() }}
          </div>
          <div class="project-details">
            <h2 class="project-name">{{ project.name }}</h2>
            <el-tag
              :type="projectUtils.getStatusTagType(project.status)"
              size="large"
            >
              {{ projectUtils.getStatusText(project.status) }}
            </el-tag>
            <p class="project-description">
              {{ project.description || '暂无描述' }}
            </p>
            <div class="project-meta">
              <div class="meta-item">
                <span class="meta-label">创建时间：</span>
                <span class="meta-value">{{ formatTime(project.created_at) }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">更新时间：</span>
                <span class="meta-value">{{ formatTime(project.updated_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 统计信息 -->
      <div class="detail-section">
        <div class="section-header">
          <h3>统计信息</h3>
        </div>
        
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-icon test-cases">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ project.test_case_count }}</div>
              <div class="stat-label">测试用例</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon categories">
              <el-icon><Folder /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ project.category_count }}</div>
              <div class="stat-label">分类</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon tags">
              <el-icon><PriceTag /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ project.tag_count }}</div>
              <div class="stat-label">标签</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 最近活动 -->
      <div class="detail-section">
        <div class="section-header">
          <h3>最近活动</h3>
          <el-button type="text" size="small" @click="loadActivity">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
        
        <div class="activity-list" v-loading="activityLoading">
          <div
            v-for="activity in activities"
            :key="activity.id"
            class="activity-item"
          >
            <div class="activity-icon">
              <el-icon>
                <component :is="getActivityIcon(activity.type)" />
              </el-icon>
            </div>
            <div class="activity-content">
              <div class="activity-description">{{ activity.description }}</div>
              <div class="activity-meta">
                <span class="activity-user">{{ activity.user }}</span>
                <span class="activity-time">{{ formatTime(activity.created_at) }}</span>
              </div>
            </div>
          </div>
          
          <el-empty
            v-if="activities.length === 0 && !activityLoading"
            description="暂无活动记录"
            :image-size="60"
          />
        </div>
      </div>

      <!-- 快速操作 -->
      <div class="detail-section">
        <div class="section-header">
          <h3>快速操作</h3>
        </div>
        
        <div class="quick-actions">
          <el-button type="primary" @click="handleGoToTestCases">
            <el-icon><Document /></el-icon>
            查看测试用例
          </el-button>
          <el-button @click="handleGoToGenerate">
            <el-icon><Plus /></el-icon>
            生成测试用例
          </el-button>
          <el-button @click="handleExport">
            <el-icon><Download /></el-icon>
            导出项目数据
          </el-button>
          <el-button @click="handleDuplicate">
            <el-icon><CopyDocument /></el-icon>
            复制项目
          </el-button>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button type="primary" @click="handleEdit">编辑项目</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Edit,
  Document,
  Folder,
  PriceTag,
  Refresh,
  Plus,
  Download,
  CopyDocument,
  User,
  Setting,
  Delete,
  Upload
} from '@element-plus/icons-vue'

// import { TcDialog, TcEmptyState } from '@/components/ui' // These components don't exist
import { projectApi, projectUtils, type Project } from '@/api/project'
import { formatTime } from '@/utils'

interface ProjectDetailDialogProps {
  modelValue: boolean
  project: Project | null
}

interface ProjectDetailDialogEmits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'edit', project: Project): void
}

const props = defineProps<ProjectDetailDialogProps>()
const emit = defineEmits<ProjectDetailDialogEmits>()

const router = useRouter()

// 响应式数据
const activityLoading = ref(false)
const activities = ref<any[]>([])

// 计算属性
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 监听项目变化，加载活动数据
watch(() => props.project, (newProject) => {
  if (newProject && props.modelValue) {
    loadActivity()
  }
}, { immediate: true })

// 方法
const loadActivity = async () => {
  if (!props.project) return
  
  activityLoading.value = true
  try {
    const response = await projectApi.getProjectActivity(props.project.id, {
      page: 1,
      page_size: 10
    })
    activities.value = response.items
  } catch (error) {
    console.error('加载活动记录失败:', error)
  } finally {
    activityLoading.value = false
  }
}

const getActivityIcon = (type: string) => {
  const iconMap: Record<string, any> = {
    'create': Plus,
    'update': Edit,
    'delete': Delete,
    'upload': Upload,
    'export': Download,
    'user': User,
    'setting': Setting
  }
  return iconMap[type] || Document
}

const handleClose = () => {
  visible.value = false
}

const handleEdit = () => {
  if (props.project) {
    emit('edit', props.project)
    handleClose()
  }
}

const handleGoToTestCases = () => {
  if (props.project) {
    router.push({
      name: 'TestCaseManagement',
      query: { projectId: props.project.id }
    })
    handleClose()
  }
}

const handleGoToGenerate = () => {
  if (props.project) {
    router.push({
      name: 'TestCaseGenerate',
      query: { projectId: props.project.id }
    })
    handleClose()
  }
}

const handleExport = async () => {
  if (!props.project) return
  
  try {
    const blob = await projectApi.exportProject(props.project.id, 'excel')
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${props.project.name}_项目数据.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('项目数据导出成功')
  } catch (error) {
    ElMessage.error('项目数据导出失败')
  }
}

const handleDuplicate = async () => {
  if (!props.project) return
  
  try {
    const newName = `${props.project.name} - 副本`
    await projectApi.duplicateProject(props.project.id, newName)
    ElMessage.success('项目复制成功')
    handleClose()
  } catch (error) {
    ElMessage.error('项目复制失败')
  }
}
</script>

<style lang="scss" scoped>
.project-detail {
  .detail-section {
    margin-bottom: var(--spacing-2xl);
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--spacing-lg);
      
      h3 {
        font-size: var(--font-size-lg);
        font-weight: var(--font-weight-semibold);
        color: var(--text-primary);
        margin: 0;
      }
    }
  }
  
  .project-info-card {
    display: flex;
    gap: var(--spacing-lg);
    padding: var(--spacing-lg);
    background: var(--bg-secondary);
    border-radius: var(--border-radius-lg);
    
    .project-avatar-large {
      width: 80px;
      height: 80px;
      border-radius: var(--border-radius-lg);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: var(--font-weight-bold);
      font-size: var(--font-size-2xl);
      flex-shrink: 0;
    }
    
    .project-details {
      flex: 1;
      
      .project-name {
        font-size: var(--font-size-2xl);
        font-weight: var(--font-weight-bold);
        color: var(--text-primary);
        margin: 0 0 var(--spacing-sm) 0;
      }
      
      .project-description {
        color: var(--text-secondary);
        line-height: var(--line-height-relaxed);
        margin: var(--spacing-md) 0;
      }
      
      .project-meta {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-xs);
        
        .meta-item {
          display: flex;
          
          .meta-label {
            color: var(--text-secondary);
            min-width: 80px;
          }
          
          .meta-value {
            color: var(--text-primary);
          }
        }
      }
    }
  }
  
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--spacing-lg);
    
    .stat-item {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-lg);
      background: var(--bg-secondary);
      border-radius: var(--border-radius-lg);
      
      .stat-icon {
        width: 48px;
        height: 48px;
        border-radius: var(--border-radius-lg);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        
        &.test-cases {
          background: var(--primary-100);
          color: var(--primary-color);
        }
        
        &.categories {
          background: var(--success-100);
          color: var(--success-color);
        }
        
        &.tags {
          background: var(--warning-100);
          color: var(--warning-color);
        }
      }
      
      .stat-content {
        .stat-number {
          font-size: var(--font-size-2xl);
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
  
  .activity-list {
    max-height: 300px;
    overflow-y: auto;
    
    .activity-item {
      display: flex;
      gap: var(--spacing-md);
      padding: var(--spacing-md);
      border-bottom: 1px solid var(--border-color-light);
      
      &:last-child {
        border-bottom: none;
      }
      
      .activity-icon {
        width: 32px;
        height: 32px;
        border-radius: var(--border-radius);
        background: var(--primary-100);
        color: var(--primary-color);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
      }
      
      .activity-content {
        flex: 1;
        
        .activity-description {
          color: var(--text-primary);
          margin-bottom: var(--spacing-xs);
        }
        
        .activity-meta {
          display: flex;
          gap: var(--spacing-md);
          font-size: var(--font-size-sm);
          color: var(--text-secondary);
          
          .activity-user {
            font-weight: var(--font-weight-medium);
          }
        }
      }
    }
  }
  
  .quick-actions {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-md);
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
}

// 响应式设计
@media (max-width: 768px) {
  .project-detail {
    .project-info-card {
      flex-direction: column;
      text-align: center;
    }
    
    .stats-grid {
      grid-template-columns: 1fr;
    }
    
    .quick-actions {
      flex-direction: column;
      
      .el-button {
        width: 100%;
      }
    }
  }
}
</style>
