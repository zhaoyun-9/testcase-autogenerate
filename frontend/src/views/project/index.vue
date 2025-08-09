<template>
  <div class="project-management">
    <!-- 页面头部 -->
    <TcPageHeader
      title="项目管理"
      subtitle="管理和组织您的测试项目，跟踪项目进度和统计信息"
      :actions="headerActions"
    >
      <template #extra>
        <!-- 统计卡片 -->
        <div class="stats-cards">
          <div class="stat-card">
            <div class="stat-icon">
              <el-icon><Folder /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total_projects }}</div>
              <div class="stat-label">总项目数</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon active">
              <el-icon><FolderOpened /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.active_projects }}</div>
              <div class="stat-label">活跃项目</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total_test_cases }}</div>
              <div class="stat-label">测试用例</div>
            </div>
          </div>
        </div>
      </template>
    </TcPageHeader>

    <!-- 搜索和筛选 -->
    <TcCard class="search-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="搜索">
          <el-input
            v-model="searchForm.search"
            placeholder="请输入项目名称"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="请选择状态" clearable>
            <el-option label="活跃" value="active" />
            <el-option label="已归档" value="archived" />
            <el-option label="已删除" value="deleted" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch" :loading="loading">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </TcCard>

    <!-- 项目列表 -->
    <TcCard>
      <template #header>
        <div class="list-header">
          <span>项目列表</span>
          <div class="header-actions">
            <el-button-group>
              <el-button
                :type="viewMode === 'grid' ? 'primary' : 'default'"
                :icon="Grid"
                @click="viewMode = 'grid'"
              >
                网格视图
              </el-button>
              <el-button
                :type="viewMode === 'list' ? 'primary' : 'default'"
                :icon="List"
                @click="viewMode = 'list'"
              >
                列表视图
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>

      <!-- 网格视图 -->
      <div v-if="viewMode === 'grid'" class="project-grid">
        <div
          v-for="project in projects"
          :key="project.id"
          class="project-card"
          @click="handleViewProject(project)"
        >
          <div class="project-header">
            <div class="project-avatar" :style="{ backgroundColor: projectUtils.generateProjectColor(project.name) }">
              {{ project.name.charAt(0).toUpperCase() }}
            </div>
            <div class="project-info">
              <h3 class="project-name">{{ project.name }}</h3>
              <el-tag
                :type="projectUtils.getStatusTagType(project.status)"
                size="small"
              >
                {{ projectUtils.getStatusText(project.status) }}
              </el-tag>
            </div>
            <el-dropdown @command="(command) => handleProjectAction(command, project)">
              <el-button type="text" :icon="MoreFilled" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="view" :icon="View">查看详情</el-dropdown-item>
                  <el-dropdown-item command="edit" :icon="Edit">编辑项目</el-dropdown-item>
                  <el-dropdown-item command="duplicate" :icon="CopyDocument">复制项目</el-dropdown-item>
                  <el-dropdown-item
                    v-if="project.status === ProjectStatus.ACTIVE"
                    command="archive"
                    :icon="FolderDelete"
                  >
                    归档项目
                  </el-dropdown-item>
                  <el-dropdown-item
                    v-else
                    command="activate"
                    :icon="FolderOpened"
                  >
                    激活项目
                  </el-dropdown-item>
                  <el-dropdown-item command="export" :icon="Download">导出数据</el-dropdown-item>
                  <el-dropdown-item command="delete" :icon="Delete" divided>删除项目</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>

          <div class="project-description">
            {{ project.description || '暂无描述' }}
          </div>

          <div class="project-stats">
            <div
              v-for="stat in projectUtils.formatProjectStats(project)"
              :key="stat.label"
              class="stat-item"
            >
              <div class="stat-dot" :style="{ backgroundColor: stat.color }"></div>
              <span class="stat-text">{{ stat.label }}: {{ stat.value }}</span>
            </div>
          </div>

          <div class="project-footer">
            <span class="project-time">
              更新于 {{ formatTime(project.updated_at) }}
            </span>
          </div>
        </div>

        <!-- 空状态 -->
        <el-empty
          v-if="projects.length === 0 && !loading"
          description="暂无项目数据"
        >
          <el-button type="primary" @click="handleCreateProject">
            <el-icon><Plus /></el-icon>
            创建项目
          </el-button>
        </el-empty>
      </div>

      <!-- 列表视图 -->
      <el-table
        v-else
        :data="projects"
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="项目名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '活跃' : '已归档' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间">
          <template #default="{ row }">
            {{ formatTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="handleViewProject(row)">查看</el-button>
            <el-button size="small" @click="handleEditProject(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDeleteProject(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

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

    <!-- 创建/编辑项目对话框 -->
    <el-dialog
      v-model="projectDialogVisible"
      :title="editingProject ? '编辑项目' : '创建项目'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="projectForm" label-width="80px">
        <el-form-item label="项目名称" required>
          <el-input
            v-model="projectForm.name"
            placeholder="请输入项目名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input
            v-model="projectForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入项目描述"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="handleCancelProject">取消</el-button>
        <el-button type="primary" @click="handleSaveProject" :loading="projectDialogLoading">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 项目详情对话框 -->
    <ProjectDetailDialog
      v-model="projectDetailVisible"
      :project="selectedProject"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Folder,
  FolderOpened,
  FolderDelete,
  Document,
  Plus,
  Grid,
  List,
  MoreFilled,
  View,
  Edit,
  CopyDocument,
  Download,
  Delete,
  Search,
  Refresh
} from '@element-plus/icons-vue'

import {
  TcPageHeader,
  TcCard
} from '@/components/ui'
import ProjectDetailDialog from './components/ProjectDetailDialog.vue'

import { projectApi, ProjectStatus, projectUtils, type Project } from '@/api/project'
import { formatTime } from '@/utils'
import type { FormItem, TableColumn } from '@/components/ui/types'

// 响应式数据
const loading = ref(false)
const viewMode = ref<'grid' | 'list'>('grid')
const projects = ref<Project[]>([])
const selectedProjects = ref<Project[]>([])
const selectedProject = ref<Project | null>(null)

// 统计数据
const stats = reactive({
  total_projects: 0,
  active_projects: 0,
  archived_projects: 0,
  total_test_cases: 0
})

// 搜索表单
const searchForm = ref({
  search: '',
  status: null as ProjectStatus | null
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 对话框状态
const projectDialogVisible = ref(false)
const projectDetailVisible = ref(false)
const projectDialogLoading = ref(false)
const editingProject = ref<Project | null>(null)

// 项目表单
const projectForm = ref({
  name: '',
  description: ''
})

// 页面头部操作
const headerActions = computed(() => [
  {
    type: 'button' as const,
    label: '创建项目',
    buttonType: 'primary' as const,
    icon: Plus,
    handler: handleCreateProject
  },
  {
    type: 'dropdown' as const,
    label: '更多操作',
    items: [
      {
        label: '批量导出',
        command: 'batch-export',
        icon: Download
      },
      {
        label: '数据统计',
        command: 'statistics',
        icon: Document
      }
    ],
    handler: handleMoreAction
  }
])

// 搜索字段配置
const searchFields: FormItem[] = [
  {
    prop: 'search',
    label: '项目名称',
    type: 'input',
    placeholder: '请输入项目名称',
    span: 8
  },
  {
    prop: 'status',
    label: '项目状态',
    type: 'select',
    placeholder: '请选择状态',
    options: [
      { label: '活跃', value: ProjectStatus.ACTIVE },
      { label: '已归档', value: ProjectStatus.ARCHIVED }
    ],
    span: 8
  }
]

// 项目表单配置
const projectFormItems: FormItem[] = [
  {
    prop: 'name',
    label: '项目名称',
    type: 'input',
    placeholder: '请输入项目名称',
    rules: [
      { required: true, message: '请输入项目名称', trigger: 'blur' },
      { max: 255, message: '项目名称不能超过255个字符', trigger: 'blur' }
    ]
  },
  {
    prop: 'description',
    label: '项目描述',
    type: 'textarea',
    placeholder: '请输入项目描述（可选）'
  }
]

// 表格列配置
const tableColumns: TableColumn[] = [
  {
    prop: 'name',
    label: '项目名称',
    minWidth: 200,
    render: (row) => {
      return `
        <div class="project-name-cell">
          <div class="project-avatar-small" style="background-color: ${projectUtils.generateProjectColor(row.name)}">
            ${row.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <div class="name">${row.name}</div>
            <div class="description">${row.description || '暂无描述'}</div>
          </div>
        </div>
      `
    }
  },
  {
    prop: 'status',
    label: '状态',
    width: 100,
    render: (row) => {
      const type = projectUtils.getStatusTagType(row.status)
      const text = projectUtils.getStatusText(row.status)
      return `<el-tag type="${type}" size="small">${text}</el-tag>`
    }
  },
  {
    prop: 'test_case_count',
    label: '测试用例',
    width: 100,
    align: 'center'
  },
  {
    prop: 'category_count',
    label: '分类',
    width: 80,
    align: 'center'
  },
  {
    prop: 'tag_count',
    label: '标签',
    width: 80,
    align: 'center'
  },
  {
    prop: 'updated_at',
    label: '更新时间',
    width: 180,
    formatter: (row) => formatTime(row.updated_at)
  }
]

// 表格操作
const tableActions = [
  {
    label: '查看',
    type: 'primary' as const,
    size: 'small' as const,
    icon: 'View',
    handler: (row: Project) => handleViewProject(row)
  },
  {
    label: '编辑',
    type: 'default' as const,
    size: 'small' as const,
    icon: 'Edit',
    handler: (row: Project) => handleEditProject(row)
  },
  {
    label: '删除',
    type: 'danger' as const,
    size: 'small' as const,
    icon: 'Delete',
    handler: (row: Project) => handleDeleteProject(row)
  }
]

// 批量操作
const batchActions = computed(() => [
  {
    label: '批量删除',
    type: 'danger' as const,
    icon: 'Delete',
    disabled: computed(() => selectedProjects.value.length === 0),
    handler: handleBatchDelete
  },
  {
    label: '批量归档',
    type: 'warning' as const,
    icon: 'FolderDelete',
    disabled: computed(() => selectedProjects.value.length === 0),
    handler: handleBatchArchive
  }
])

// 生命周期
onMounted(() => {
  loadProjects()
  loadStats()
})

// 方法实现
const loadProjects = async () => {
  loading.value = true
  try {
    const response = await projectApi.getProjects({
      page: pagination.page,
      page_size: pagination.pageSize,
      search: searchForm.value.search || undefined,
      status: searchForm.value.status || undefined
    })
    
    projects.value = response.items
    pagination.total = response.total
  } catch (error) {
    ElMessage.error('加载项目列表失败')
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const response = await projectApi.getProjectStats()
    Object.assign(stats, response)
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadProjects()
}

const handleReset = () => {
  searchForm.value.search = ''
  searchForm.value.status = null
  pagination.page = 1
  loadProjects()
}

const handleCreateProject = () => {
  editingProject.value = null
  projectForm.value.name = ''
  projectForm.value.description = ''
  projectDialogVisible.value = true
}

const handleEditProject = (project: Project) => {
  editingProject.value = project
  projectForm.value.name = project.name
  projectForm.value.description = project.description || ''
  projectDialogVisible.value = true
}

const handleViewProject = (project: Project) => {
  selectedProject.value = project
  projectDetailVisible.value = true
}

const handleSaveProject = async () => {
  const validation = projectUtils.validateProjectName(projectForm.value.name)
  if (!validation.valid) {
    ElMessage.error(validation.message)
    return
  }

  projectDialogLoading.value = true
  try {
    if (editingProject.value) {
      await projectApi.updateProject(editingProject.value.id, {
        name: projectForm.value.name,
        description: projectForm.value.description
      })
      ElMessage.success('项目更新成功')
    } else {
      await projectApi.createProject({
        name: projectForm.value.name,
        description: projectForm.value.description
      })
      ElMessage.success('项目创建成功')
    }
    
    projectDialogVisible.value = false
    loadProjects()
    loadStats()
  } catch (error) {
    ElMessage.error(editingProject.value ? '项目更新失败' : '项目创建失败')
  } finally {
    projectDialogLoading.value = false
  }
}

const handleCancelProject = () => {
  projectDialogVisible.value = false
  editingProject.value = null
}

const handleDeleteProject = async (project: Project) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目"${project.name}"吗？此操作不可撤销。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )
    
    await projectApi.deleteProject(project.id)
    ElMessage.success('项目删除成功')
    loadProjects()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('项目删除失败')
    }
  }
}

const handleProjectAction = async (command: string, project: Project) => {
  switch (command) {
    case 'view':
      handleViewProject(project)
      break
    case 'edit':
      handleEditProject(project)
      break
    case 'duplicate':
      // TODO: 实现项目复制
      break
    case 'archive':
      await projectApi.archiveProject(project.id)
      ElMessage.success('项目已归档')
      loadProjects()
      loadStats()
      break
    case 'activate':
      await projectApi.activateProject(project.id)
      ElMessage.success('项目已激活')
      loadProjects()
      loadStats()
      break
    case 'export':
      // TODO: 实现项目导出
      break
    case 'delete':
      handleDeleteProject(project)
      break
  }
}

const handleMoreAction = (command: string) => {
  switch (command) {
    case 'batch-export':
      // TODO: 实现批量导出
      break
    case 'statistics':
      // TODO: 显示统计页面
      break
  }
}

const handleSelectionChange = (selection: Project[]) => {
  selectedProjects.value = selection
}

async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedProjects.value.length} 个项目吗？此操作不可撤销。`,
      '确认批量删除',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )

    const ids = selectedProjects.value.map(p => p.id)
    await projectApi.batchDeleteProjects(ids)
    ElMessage.success('批量删除成功')
    loadProjects()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

async function handleBatchArchive() {
  // TODO: 实现批量归档
}

const handlePageChange = (page: number) => {
  pagination.page = page
  loadProjects()
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadProjects()
}
</script>

<style lang="scss" scoped>
.project-management {
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
      min-width: 160px;

      .stat-icon {
        width: 48px;
        height: 48px;
        border-radius: var(--border-radius-lg);
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--primary-100);
        color: var(--primary-color);
        font-size: 24px;

        &.active {
          background: var(--success-100);
          color: var(--success-color);
        }
      }

      .stat-content {
        .stat-value {
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

  .search-card {
    margin: var(--spacing-xl) 0;
  }

  .list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .project-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: var(--spacing-lg);
    padding: var(--spacing-lg) 0;

    .project-card {
      background: var(--bg-primary);
      border: 1px solid var(--border-color);
      border-radius: var(--border-radius-lg);
      padding: var(--spacing-lg);
      cursor: pointer;
      transition: all var(--transition-normal);

      &:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        border-color: var(--primary-color);
      }

      .project-header {
        display: flex;
        align-items: flex-start;
        gap: var(--spacing-md);
        margin-bottom: var(--spacing-md);

        .project-avatar {
          width: 48px;
          height: 48px;
          border-radius: var(--border-radius-lg);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: var(--font-weight-bold);
          font-size: var(--font-size-lg);
          flex-shrink: 0;
        }

        .project-info {
          flex: 1;
          min-width: 0;

          .project-name {
            font-size: var(--font-size-lg);
            font-weight: var(--font-weight-semibold);
            color: var(--text-primary);
            margin: 0 0 var(--spacing-xs) 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
        }
      }

      .project-description {
        color: var(--text-secondary);
        font-size: var(--font-size-sm);
        line-height: var(--line-height-relaxed);
        margin-bottom: var(--spacing-md);
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }

      .project-stats {
        display: flex;
        flex-wrap: wrap;
        gap: var(--spacing-md);
        margin-bottom: var(--spacing-md);

        .stat-item {
          display: flex;
          align-items: center;
          gap: var(--spacing-xs);

          .stat-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
          }

          .stat-text {
            font-size: var(--font-size-xs);
            color: var(--text-secondary);
          }
        }
      }

      .project-footer {
        padding-top: var(--spacing-md);
        border-top: 1px solid var(--border-color-light);

        .project-time {
          font-size: var(--font-size-xs);
          color: var(--text-tertiary);
        }
      }
    }
  }
}

// 表格内的项目名称单元格样式
:deep(.project-name-cell) {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);

  .project-avatar-small {
    width: 32px;
    height: 32px;
    border-radius: var(--border-radius);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: var(--font-weight-semibold);
    font-size: var(--font-size-sm);
    flex-shrink: 0;
  }

  .name {
    font-weight: var(--font-weight-medium);
    color: var(--text-primary);
  }

  .description {
    font-size: var(--font-size-xs);
    color: var(--text-secondary);
    margin-top: 2px;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .project-management {
    .stats-cards {
      flex-direction: column;
    }

    .project-grid {
      grid-template-columns: 1fr;
    }
  }
}
</style>
