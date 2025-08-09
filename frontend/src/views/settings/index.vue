<template>
  <div class="settings-page">
    <div class="page-container">
      <!-- 页面标题 -->
      <div class="page-header">
        <h1 class="page-title">系统设置</h1>
        <p class="page-subtitle">配置系统参数和个人偏好</p>
      </div>

      <el-row :gutter="24">
        <!-- 设置菜单 -->
        <el-col :span="6">
          <el-card class="settings-menu" shadow="never">
            <el-menu
              :default-active="activeTab"
              @select="handleMenuSelect"
              class="menu"
            >
              <el-menu-item index="general">
                <el-icon><Setting /></el-icon>
                <span>常规设置</span>
              </el-menu-item>
              <el-menu-item index="appearance">
                <el-icon><Brush /></el-icon>
                <span>外观设置</span>
              </el-menu-item>
              <el-menu-item index="generation">
                <el-icon><Magic /></el-icon>
                <span>生成设置</span>
              </el-menu-item>
              <el-menu-item index="export">
                <el-icon><Download /></el-icon>
                <span>导出设置</span>
              </el-menu-item>
              <el-menu-item index="system">
                <el-icon><Monitor /></el-icon>
                <span>系统信息</span>
              </el-menu-item>
              <el-menu-item index="logs">
                <el-icon><Document /></el-icon>
                <span>系统日志</span>
              </el-menu-item>
              <el-menu-item index="backup">
                <el-icon><FolderAdd /></el-icon>
                <span>备份管理</span>
              </el-menu-item>
              <el-menu-item index="about">
                <el-icon><InfoFilled /></el-icon>
                <span>关于</span>
              </el-menu-item>
            </el-menu>
          </el-card>
        </el-col>

        <!-- 设置内容 -->
        <el-col :span="18">
          <el-card class="settings-content" shadow="never">
            <!-- 常规设置 -->
            <div v-if="activeTab === 'general'" class="settings-section">
              <h3 class="section-title">常规设置</h3>
              
              <el-form :model="settings.general" label-width="150px">
                <el-form-item label="默认语言">
                  <el-select v-model="settings.general.language" style="width: 200px">
                    <el-option label="简体中文" value="zh-CN" />
                    <el-option label="English" value="en-US" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="自动保存">
                  <el-switch v-model="settings.general.autoSave" />
                  <span class="form-help">自动保存编辑的测试用例</span>
                </el-form-item>
                
                <el-form-item label="保存间隔">
                  <el-input-number
                    v-model="settings.general.saveInterval"
                    :min="10"
                    :max="300"
                    :step="10"
                    :disabled="!settings.general.autoSave"
                  />
                  <span class="form-help">秒</span>
                </el-form-item>
                
                <el-form-item label="确认删除">
                  <el-switch v-model="settings.general.confirmDelete" />
                  <span class="form-help">删除测试用例时显示确认对话框</span>
                </el-form-item>
              </el-form>
            </div>

            <!-- 外观设置 -->
            <div v-if="activeTab === 'appearance'" class="settings-section">
              <h3 class="section-title">外观设置</h3>
              
              <el-form :model="settings.appearance" label-width="150px">
                <el-form-item label="主题模式">
                  <el-radio-group v-model="settings.appearance.theme">
                    <el-radio label="light">浅色主题</el-radio>
                    <el-radio label="dark">深色主题</el-radio>
                    <el-radio label="auto">跟随系统</el-radio>
                  </el-radio-group>
                </el-form-item>
                
                <el-form-item label="主色调">
                  <div class="color-picker-group">
                    <div
                      v-for="color in colorOptions"
                      :key="color.value"
                      class="color-option"
                      :class="{ active: settings.appearance.primaryColor === color.value }"
                      :style="{ backgroundColor: color.value }"
                      @click="settings.appearance.primaryColor = color.value"
                    >
                      <el-icon v-if="settings.appearance.primaryColor === color.value">
                        <Check />
                      </el-icon>
                    </div>
                  </div>
                </el-form-item>
                
                <el-form-item label="字体大小">
                  <el-slider
                    v-model="settings.appearance.fontSize"
                    :min="12"
                    :max="18"
                    :step="1"
                    show-tooltip
                    :format-tooltip="(val) => `${val}px`"
                  />
                </el-form-item>
                
                <el-form-item label="侧边栏宽度">
                  <el-slider
                    v-model="settings.appearance.sidebarWidth"
                    :min="200"
                    :max="400"
                    :step="10"
                    show-tooltip
                    :format-tooltip="(val) => `${val}px`"
                  />
                </el-form-item>
                
                <el-form-item label="紧凑模式">
                  <el-switch v-model="settings.appearance.compact" />
                  <span class="form-help">减少界面元素间距</span>
                </el-form-item>
              </el-form>
            </div>

            <!-- 生成设置 -->
            <div v-if="activeTab === 'generation'" class="settings-section">
              <h3 class="section-title">生成设置</h3>
              
              <el-form :model="settings.generation" label-width="150px">
                <el-form-item label="默认测试类型">
                  <el-select v-model="settings.generation.defaultTestType" style="width: 200px">
                    <el-option label="功能测试" value="functional" />
                    <el-option label="接口测试" value="interface" />
                    <el-option label="性能测试" value="performance" />
                    <el-option label="安全测试" value="security" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="默认优先级">
                  <el-select v-model="settings.generation.defaultPriority" style="width: 200px">
                    <el-option label="P0 - 最高" value="P0" />
                    <el-option label="P1 - 高" value="P1" />
                    <el-option label="P2 - 中" value="P2" />
                    <el-option label="P3 - 低" value="P3" />
                    <el-option label="P4 - 最低" value="P4" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="最大用例数">
                  <el-input-number
                    v-model="settings.generation.maxTestCases"
                    :min="1"
                    :max="200"
                    :step="1"
                  />
                </el-form-item>
                
                <el-form-item label="自动生成思维导图">
                  <el-switch v-model="settings.generation.autoGenerateMindmap" />
                </el-form-item>
                
                <el-form-item label="默认标签">
                  <el-select
                    v-model="settings.generation.defaultTags"
                    multiple
                    filterable
                    allow-create
                    placeholder="选择或输入默认标签"
                    style="width: 300px"
                  >
                    <el-option
                      v-for="tag in commonTags"
                      :key="tag"
                      :label="tag"
                      :value="tag"
                    />
                  </el-select>
                </el-form-item>
              </el-form>
            </div>

            <!-- 导出设置 -->
            <div v-if="activeTab === 'export'" class="settings-section">
              <h3 class="section-title">导出设置</h3>
              
              <el-form :model="settings.export" label-width="150px">
                <el-form-item label="默认导出格式">
                  <el-select v-model="settings.export.defaultFormat" style="width: 200px">
                    <el-option label="Excel" value="excel" />
                    <el-option label="PDF" value="pdf" />
                    <el-option label="Word" value="word" />
                    <el-option label="JSON" value="json" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="包含字段">
                  <el-checkbox-group v-model="settings.export.includeFields">
                    <el-checkbox label="title">标题</el-checkbox>
                    <el-checkbox label="description">描述</el-checkbox>
                    <el-checkbox label="preconditions">前置条件</el-checkbox>
                    <el-checkbox label="steps">测试步骤</el-checkbox>
                    <el-checkbox label="expected">预期结果</el-checkbox>
                    <el-checkbox label="tags">标签</el-checkbox>
                    <el-checkbox label="metadata">元数据</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>
                
                <el-form-item label="文件名模板">
                  <el-input
                    v-model="settings.export.filenameTemplate"
                    placeholder="例如: TestCases_{date}_{time}"
                    style="width: 300px"
                  />
                  <div class="form-help">
                    可用变量: {date}, {time}, {session}, {count}
                  </div>
                </el-form-item>
                
                <el-form-item label="自动下载">
                  <el-switch v-model="settings.export.autoDownload" />
                  <span class="form-help">导出完成后自动下载文件</span>
                </el-form-item>
              </el-form>
            </div>

            <!-- 系统信息 -->
            <div v-if="activeTab === 'system'" class="settings-section">
              <h3 class="section-title">系统信息</h3>

              <div class="system-info">
                <el-row :gutter="24">
                  <el-col :span="12">
                    <el-card class="info-card">
                      <template #header>
                        <span>基本信息</span>
                      </template>
                      <div class="info-item">
                        <span class="label">系统版本:</span>
                        <span class="value">{{ systemInfo.version }}</span>
                      </div>
                      <div class="info-item">
                        <span class="label">构建时间:</span>
                        <span class="value">{{ systemInfo.build_time }}</span>
                      </div>
                      <div class="info-item">
                        <span class="label">运行环境:</span>
                        <span class="value">{{ systemInfo.environment }}</span>
                      </div>
                      <div class="info-item">
                        <span class="label">运行时间:</span>
                        <span class="value">{{ formatUptime(systemInfo.uptime) }}</span>
                      </div>
                    </el-card>
                  </el-col>
                  <el-col :span="12">
                    <el-card class="info-card">
                      <template #header>
                        <span>系统状态</span>
                      </template>
                      <div class="info-item">
                        <span class="label">数据库状态:</span>
                        <el-tag :type="systemInfo.database_status === 'healthy' ? 'success' : 'danger'">
                          {{ systemInfo.database_status === 'healthy' ? '正常' : '异常' }}
                        </el-tag>
                      </div>
                      <div class="info-item">
                        <span class="label">活跃会话:</span>
                        <span class="value">{{ systemInfo.active_sessions }}</span>
                      </div>
                      <div class="info-item">
                        <span class="label">磁盘使用:</span>
                        <el-progress
                          :percentage="systemInfo.disk_usage?.percentage || 0"
                          :color="getUsageColor(systemInfo.disk_usage?.percentage || 0)"
                        />
                        <span class="usage-text">
                          {{ formatFileSize(systemInfo.disk_usage?.used || 0) }} /
                          {{ formatFileSize(systemInfo.disk_usage?.total || 0) }}
                        </span>
                      </div>
                      <div class="info-item">
                        <span class="label">内存使用:</span>
                        <el-progress
                          :percentage="systemInfo.memory_usage?.percentage || 0"
                          :color="getUsageColor(systemInfo.memory_usage?.percentage || 0)"
                        />
                        <span class="usage-text">
                          {{ formatFileSize(systemInfo.memory_usage?.used || 0) }} /
                          {{ formatFileSize(systemInfo.memory_usage?.total || 0) }}
                        </span>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>

                <el-card class="stats-card" style="margin-top: 20px;">
                  <template #header>
                    <span>系统统计</span>
                    <el-button type="primary" size="small" @click="loadSystemStats">刷新</el-button>
                  </template>
                  <el-row :gutter="24">
                    <el-col :span="6">
                      <div class="stat-item">
                        <div class="stat-value">{{ systemStats.total_projects }}</div>
                        <div class="stat-label">总项目数</div>
                      </div>
                    </el-col>
                    <el-col :span="6">
                      <div class="stat-item">
                        <div class="stat-value">{{ systemStats.total_test_cases }}</div>
                        <div class="stat-label">总测试用例</div>
                      </div>
                    </el-col>
                    <el-col :span="6">
                      <div class="stat-item">
                        <div class="stat-value">{{ systemStats.total_users }}</div>
                        <div class="stat-label">用户数</div>
                      </div>
                    </el-col>
                    <el-col :span="6">
                      <div class="stat-item">
                        <div class="stat-value">{{ systemStats.total_sessions }}</div>
                        <div class="stat-label">总会话数</div>
                      </div>
                    </el-col>
                  </el-row>
                </el-card>
              </div>
            </div>

            <!-- 系统日志 -->
            <div v-if="activeTab === 'logs'" class="settings-section">
              <h3 class="section-title">系统日志</h3>

              <div class="logs-section">
                <div class="logs-toolbar">
                  <el-form :model="logFilters" inline>
                    <el-form-item label="日志级别">
                      <el-select v-model="logFilters.level" placeholder="选择级别" clearable>
                        <el-option label="DEBUG" value="DEBUG" />
                        <el-option label="INFO" value="INFO" />
                        <el-option label="WARNING" value="WARNING" />
                        <el-option label="ERROR" value="ERROR" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="模块">
                      <el-input v-model="logFilters.module" placeholder="输入模块名" clearable />
                    </el-form-item>
                    <el-form-item>
                      <el-button type="primary" @click="loadLogs">查询</el-button>
                      <el-button @click="clearLogFilters">重置</el-button>
                      <el-button type="danger" @click="handleClearLogs">清理日志</el-button>
                    </el-form-item>
                  </el-form>
                </div>

                <el-table :data="logs" v-loading="logsLoading" max-height="400">
                  <el-table-column label="时间" prop="timestamp" width="180">
                    <template #default="{ row }">
                      {{ formatDate(row.timestamp) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="级别" prop="level" width="80">
                    <template #default="{ row }">
                      <el-tag :color="getLogLevelColor(row.level)" size="small">
                        {{ row.level }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="模块" prop="module" width="120" />
                  <el-table-column label="消息" prop="message" min-width="300" />
                </el-table>

                <div class="pagination-wrapper">
                  <el-pagination
                    v-model:current-page="logPagination.page"
                    v-model:page-size="logPagination.pageSize"
                    :total="logPagination.total"
                    :page-sizes="[20, 50, 100]"
                    layout="total, sizes, prev, pager, next"
                    @size-change="loadLogs"
                    @current-change="loadLogs"
                  />
                </div>
              </div>
            </div>

            <!-- 备份管理 -->
            <div v-if="activeTab === 'backup'" class="settings-section">
              <h3 class="section-title">备份管理</h3>

              <div class="backup-section">
                <div class="backup-toolbar">
                  <el-button type="primary" :icon="Plus" @click="showCreateBackupDialog = true">
                    创建备份
                  </el-button>
                  <el-button @click="loadBackups">刷新列表</el-button>
                </div>

                <el-table :data="backups" v-loading="backupsLoading">
                  <el-table-column label="文件名" prop="filename" min-width="200" />
                  <el-table-column label="大小" prop="size" width="120">
                    <template #default="{ row }">
                      {{ formatFileSize(row.size) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="描述" prop="description" min-width="150" />
                  <el-table-column label="状态" prop="status" width="100">
                    <template #default="{ row }">
                      <el-tag :type="getBackupStatusType(row.status)">
                        {{ getBackupStatusText(row.status) }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="创建时间" prop="created_at" width="180">
                    <template #default="{ row }">
                      {{ formatDate(row.created_at) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="200" fixed="right">
                    <template #default="{ row }">
                      <el-button
                        v-if="row.status === 'completed'"
                        type="primary"
                        size="small"
                        @click="handleDownloadBackup(row)"
                      >
                        下载
                      </el-button>
                      <el-button
                        v-if="row.status === 'completed'"
                        type="warning"
                        size="small"
                        @click="handleRestoreBackup(row)"
                      >
                        恢复
                      </el-button>
                      <el-button
                        type="danger"
                        size="small"
                        @click="handleDeleteBackup(row)"
                      >
                        删除
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>

            <!-- 关于 -->
            <div v-if="activeTab === 'about'" class="settings-section">
              <h3 class="section-title">关于</h3>
              
              <div class="about-content">
                <div class="app-info">
                  <div class="app-icon">
                    <el-icon size="48" color="#409EFF">
                      <Document />
                    </el-icon>
                  </div>
                  <div class="app-details">
                    <h4>测试用例自动化平台</h4>
                    <p>版本: 1.0.0</p>
                    <p>构建时间: 2024-01-15</p>
                  </div>
                </div>
                
                <div class="description">
                  <p>
                    基于AI技术的智能测试用例生成平台，支持多种输入方式，
                    能够自动分析需求文档、API规范、数据库结构等，
                    生成专业的测试用例和思维导图。
                  </p>
                </div>
                
                <div class="features">
                  <h5>主要功能:</h5>
                  <ul>
                    <li>多样化输入支持（文档、图片、API规范等）</li>
                    <li>智能测试用例生成</li>
                    <li>思维导图可视化</li>
                    <li>Excel导出功能</li>
                    <li>测试用例分类管理</li>
                  </ul>
                </div>
                
                <div class="tech-stack">
                  <h5>技术栈:</h5>
                  <div class="tech-tags">
                    <el-tag>Vue 3</el-tag>
                    <el-tag>Element Plus</el-tag>
                    <el-tag>TypeScript</el-tag>
                    <el-tag>FastAPI</el-tag>
                    <el-tag>Python</el-tag>
                  </div>
                </div>
              </div>
            </div>

            <!-- 保存按钮 -->
            <div v-if="activeTab !== 'about'" class="settings-actions">
              <el-button type="primary" @click="saveSettings" :loading="saving">
                保存设置
              </el-button>
              <el-button @click="resetSettings">
                重置默认
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 创建备份对话框 -->
    <el-dialog
      v-model="showCreateBackupDialog"
      title="创建备份"
      width="500px"
    >
      <el-form :model="backupForm" label-width="100px">
        <el-form-item label="备份描述">
          <el-input
            v-model="backupForm.description"
            placeholder="请输入备份描述"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="包含选项">
          <el-checkbox v-model="backupForm.include_uploads">包含上传文件</el-checkbox>
          <el-checkbox v-model="backupForm.include_logs">包含系统日志</el-checkbox>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateBackupDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateBackup">创建备份</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { systemApi } from '@/api/system'

const activeTab = ref('general')
const saving = ref(false)

// 系统信息相关
const systemInfo = ref({
  version: '1.0.0',
  build_time: '2024-01-15',
  environment: 'production',
  database_status: 'healthy',
  uptime: 0,
  active_sessions: 0,
  disk_usage: { total: 0, used: 0, free: 0, percentage: 0 },
  memory_usage: { total: 0, used: 0, free: 0, percentage: 0 }
})

const systemStats = ref({
  total_projects: 0,
  total_test_cases: 0,
  total_users: 0,
  total_sessions: 0
})

// 日志相关
const logs = ref([])
const logsLoading = ref(false)
const logFilters = reactive({
  level: '',
  module: ''
})
const logPagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 备份相关
const backups = ref([])
const backupsLoading = ref(false)
const showCreateBackupDialog = ref(false)
const backupForm = reactive({
  description: '',
  include_uploads: true,
  include_logs: false
})

// 设置数据
const settings = reactive({
  general: {
    language: 'zh-CN',
    autoSave: true,
    saveInterval: 30,
    confirmDelete: true
  },
  appearance: {
    theme: 'light',
    primaryColor: '#409EFF',
    fontSize: 14,
    sidebarWidth: 250,
    compact: false
  },
  generation: {
    defaultTestType: 'functional',
    defaultPriority: 'P2',
    maxTestCases: 50,
    autoGenerateMindmap: true,
    defaultTags: ['功能测试']
  },
  export: {
    defaultFormat: 'excel',
    includeFields: ['title', 'description', 'steps', 'expected'],
    filenameTemplate: 'TestCases_{date}_{time}',
    autoDownload: true
  }
})

// 颜色选项
const colorOptions = [
  { name: '默认蓝', value: '#409EFF' },
  { name: '成功绿', value: '#67C23A' },
  { name: '警告橙', value: '#E6A23C' },
  { name: '危险红', value: '#F56C6C' },
  { name: '信息灰', value: '#909399' },
  { name: '紫色', value: '#9C27B0' },
  { name: '青色', value: '#00BCD4' },
  { name: '粉色', value: '#E91E63' }
]

// 常用标签
const commonTags = [
  '功能测试', '接口测试', '性能测试', '安全测试',
  '兼容性测试', '易用性测试', '回归测试', '冒烟测试'
]

// 处理菜单选择
const handleMenuSelect = (index: string) => {
  activeTab.value = index
}

// 保存设置
const saveSettings = async () => {
  try {
    saving.value = true
    
    // 保存到localStorage
    localStorage.setItem('app-settings', JSON.stringify(settings))
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success('设置保存成功')
  } catch (error) {
    console.error('保存设置失败:', error)
    ElMessage.error('保存设置失败')
  } finally {
    saving.value = false
  }
}

// 系统信息相关方法
const loadSystemInfo = async () => {
  try {
    const info = await systemApi.getSystemInfo()
    systemInfo.value = info
  } catch (error) {
    console.error('加载系统信息失败:', error)
  }
}

const loadSystemStats = async () => {
  try {
    const stats = await systemApi.getSystemStats()
    systemStats.value = stats
  } catch (error) {
    console.error('加载系统统计失败:', error)
  }
}

const formatUptime = (seconds: number) => {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (days > 0) {
    return `${days}天 ${hours}小时 ${minutes}分钟`
  } else if (hours > 0) {
    return `${hours}小时 ${minutes}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟 ${secs}秒`
  } else {
    return `${secs}秒`
  }
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getUsageColor = (percentage: number) => {
  if (percentage < 60) return '#67C23A'
  if (percentage < 80) return '#E6A23C'
  return '#F56C6C'
}

// 日志相关方法
const loadLogs = async () => {
  logsLoading.value = true
  try {
    const response = await systemApi.getSystemLogs({
      level: logFilters.level || undefined,
      module: logFilters.module || undefined,
      page: logPagination.page,
      page_size: logPagination.pageSize
    })
    logs.value = response.items
    logPagination.total = response.total
  } catch (error) {
    console.error('加载日志失败:', error)
    ElMessage.error('加载日志失败')
  } finally {
    logsLoading.value = false
  }
}

const clearLogFilters = () => {
  logFilters.level = ''
  logFilters.module = ''
  logPagination.page = 1
  loadLogs()
}

const handleClearLogs = async () => {
  try {
    await ElMessageBox.confirm('确定要清理系统日志吗？此操作不可恢复。', '确认清理', {
      type: 'warning'
    })

    await systemApi.clearLogs()
    ElMessage.success('日志清理成功')
    loadLogs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('日志清理失败')
    }
  }
}

const getLogLevelColor = (level: string) => {
  switch (level.toLowerCase()) {
    case 'error':
      return 'danger'
    case 'warning':
    case 'warn':
      return 'warning'
    case 'info':
      return 'primary'
    case 'debug':
      return 'info'
    default:
      return 'default'
  }
}

// 备份相关方法
const loadBackups = async () => {
  backupsLoading.value = true
  try {
    const response = await systemApi.getBackups()
    backups.value = response.items
  } catch (error) {
    console.error('加载备份列表失败:', error)
    ElMessage.error('加载备份列表失败')
  } finally {
    backupsLoading.value = false
  }
}

const handleCreateBackup = async () => {
  try {
    await systemApi.createBackup(backupForm)
    ElMessage.success('备份创建成功')
    showCreateBackupDialog.value = false
    loadBackups()
  } catch (error) {
    ElMessage.error('备份创建失败')
  }
}

const handleDownloadBackup = async (backup: any) => {
  try {
    const blob = await systemApi.downloadBackup(backup.id)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = backup.filename
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    ElMessage.error('下载备份失败')
  }
}

const handleRestoreBackup = async (backup: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要恢复备份"${backup.filename}"吗？此操作将覆盖当前数据。`,
      '确认恢复',
      { type: 'warning' }
    )

    await systemApi.restoreBackup(backup.id)
    ElMessage.success('备份恢复成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('备份恢复失败')
    }
  }
}

const handleDeleteBackup = async (backup: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除备份"${backup.filename}"吗？`,
      '确认删除',
      { type: 'warning' }
    )

    await systemApi.deleteBackup(backup.id)
    ElMessage.success('备份删除成功')
    loadBackups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('备份删除失败')
    }
  }
}

const getBackupStatusType = (status: string) => {
  const statusMap: Record<string, any> = {
    'completed': 'success',
    'failed': 'danger',
    'in_progress': 'warning'
  }
  return statusMap[status] || 'info'
}

const getBackupStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'completed': '完成',
    'failed': '失败',
    'in_progress': '进行中'
  }
  return statusMap[status] || '未知'
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 重置设置
const resetSettings = () => {
  Object.assign(settings, {
    general: {
      language: 'zh-CN',
      autoSave: true,
      saveInterval: 30,
      confirmDelete: true
    },
    appearance: {
      theme: 'light',
      primaryColor: '#409EFF',
      fontSize: 14,
      sidebarWidth: 250,
      compact: false
    },
    generation: {
      defaultTestType: 'functional',
      defaultPriority: 'P2',
      maxTestCases: 50,
      autoGenerateMindmap: true,
      defaultTags: ['功能测试']
    },
    export: {
      defaultFormat: 'excel',
      includeFields: ['title', 'description', 'steps', 'expected'],
      filenameTemplate: 'TestCases_{date}_{time}',
      autoDownload: true
    }
  })
  
  ElMessage.success('已重置为默认设置')
}

// 加载设置
const loadSettings = () => {
  try {
    const savedSettings = localStorage.getItem('app-settings')
    if (savedSettings) {
      const parsed = JSON.parse(savedSettings)
      Object.assign(settings, parsed)
    }
  } catch (error) {
    console.error('加载设置失败:', error)
  }
}

onMounted(() => {
  loadSettings()
  loadSystemInfo()
  loadSystemStats()
  if (activeTab.value === 'logs') {
    loadLogs()
  }
  if (activeTab.value === 'backup') {
    loadBackups()
  }
})
</script>

<style lang="scss" scoped>
.settings-page {
  .page-header {
    margin-bottom: 24px;
    
    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin-bottom: 8px;
    }
    
    .page-subtitle {
      font-size: 14px;
      color: var(--el-text-color-regular);
    }
  }
  
  .settings-menu {
    .menu {
      border: none;
    }
  }
  
  .settings-content {
    min-height: 600px;
    
    .settings-section {
      .section-title {
        font-size: 18px;
        font-weight: 500;
        color: var(--el-text-color-primary);
        margin-bottom: 24px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--el-border-color-light);
      }
      
      .form-help {
        font-size: 12px;
        color: var(--el-text-color-placeholder);
        margin-left: 8px;
      }
      
      .color-picker-group {
        display: flex;
        gap: 8px;
        
        .color-option {
          width: 32px;
          height: 32px;
          border-radius: 6px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 2px solid transparent;
          transition: all 0.3s ease;
          
          &:hover {
            transform: scale(1.1);
          }
          
          &.active {
            border-color: var(--el-color-primary);
            
            .el-icon {
              color: white;
            }
          }
        }
      }
      
      .about-content {
        .app-info {
          display: flex;
          align-items: center;
          gap: 16px;
          margin-bottom: 24px;
          
          .app-details {
            h4 {
              font-size: 18px;
              font-weight: 500;
              margin-bottom: 8px;
            }
            
            p {
              font-size: 14px;
              color: var(--el-text-color-regular);
              margin-bottom: 4px;
            }
          }
        }
        
        .description {
          margin-bottom: 24px;
          
          p {
            font-size: 14px;
            line-height: 1.6;
            color: var(--el-text-color-regular);
          }
        }
        
        .features,
        .tech-stack {
          margin-bottom: 24px;
          
          h5 {
            font-size: 16px;
            font-weight: 500;
            margin-bottom: 12px;
          }
          
          ul {
            padding-left: 20px;
            
            li {
              font-size: 14px;
              color: var(--el-text-color-regular);
              margin-bottom: 4px;
            }
          }
          
          .tech-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
          }
        }
      }

      // 系统信息样式
      .system-info {
        .info-card {
          .info-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid var(--el-border-color-lighter);

            &:last-child {
              border-bottom: none;
            }

            .label {
              font-weight: 500;
              color: var(--el-text-color-regular);
            }

            .value {
              color: var(--el-text-color-primary);
            }

            .usage-text {
              font-size: 12px;
              color: var(--el-text-color-placeholder);
              margin-left: 8px;
            }
          }
        }

        .stats-card {
          .stat-item {
            text-align: center;

            .stat-value {
              font-size: 24px;
              font-weight: 600;
              color: var(--el-color-primary);
              margin-bottom: 4px;
            }

            .stat-label {
              font-size: 12px;
              color: var(--el-text-color-regular);
            }
          }
        }
      }

      // 日志样式
      .logs-section {
        .logs-toolbar {
          margin-bottom: 16px;
          padding: 16px;
          background: var(--el-bg-color-page);
          border-radius: 6px;
        }

        .pagination-wrapper {
          display: flex;
          justify-content: center;
          margin-top: 16px;
        }
      }

      // 备份样式
      .backup-section {
        .backup-toolbar {
          margin-bottom: 16px;
          display: flex;
          gap: 12px;
        }
      }
    }
    
    .settings-actions {
      margin-top: 32px;
      padding-top: 24px;
      border-top: 1px solid var(--el-border-color-light);
      
      .el-button {
        margin-right: 12px;
      }
    }
  }
}
</style>
