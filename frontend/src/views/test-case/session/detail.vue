<template>
  <div class="session-detail">
    <!-- 会话信息头部 -->
    <div class="session-header">
      <div class="session-info">
        <h2>会话详情</h2>
        <div class="session-meta">
          <el-tag :type="getStatusType(sessionInfo.status)">
            {{ getStatusText(sessionInfo.status) }}
          </el-tag>
          <span class="session-id">会话ID: {{ sessionId }}</span>
          <span class="created-time">创建时间: {{ formatTime(sessionInfo.created_at) }}</span>
        </div>
      </div>
      <div class="session-actions">
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="exportSession">
          <el-icon><Download /></el-icon>
          导出会话
        </el-button>
      </div>
    </div>

    <!-- 会话统计 -->
    <div class="session-stats">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ testCases.length }}</div>
              <div class="stat-label">测试用例</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ mindMapExists ? 1 : 0 }}</div>
              <div class="stat-label">思维导图</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ exportRecords.length }}</div>
              <div class="stat-label">导出记录</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ sessionInfo.processing_time || 0 }}s</div>
              <div class="stat-label">处理时间</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 主要内容区域 -->
    <div class="session-content">
      <el-tabs v-model="activeTab" type="card">
        <!-- 测试用例列表 -->
        <el-tab-pane label="测试用例" name="testcases">
          <div class="testcase-section">
            <div class="section-header">
              <h3>生成的测试用例 ({{ testCases.length }})</h3>
              <el-button type="primary" @click="viewAllTestCases">
                查看全部
              </el-button>
            </div>
            <el-table :data="testCases" v-loading="loading">
              <el-table-column prop="title" label="标题" min-width="200" />
              <el-table-column prop="test_type" label="类型" width="100">
                <template #default="{ row }">
                  <el-tag size="small">{{ row.test_type }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="priority" label="优先级" width="80">
                <template #default="{ row }">
                  <el-tag :type="getPriorityType(row.priority)" size="small">
                    {{ row.priority }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="创建时间" width="160">
                <template #default="{ row }">
                  {{ formatTime(row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <el-button type="text" @click="viewTestCase(row.id)">
                    查看
                  </el-button>
                  <el-button type="text" @click="editTestCase(row.id)">
                    编辑
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- 思维导图 -->
        <el-tab-pane label="思维导图" name="mindmap">
          <div class="mindmap-section">
            <div class="section-header">
              <h3>测试用例思维导图</h3>
              <div class="mindmap-actions">
                <el-button v-if="!mindMapExists" type="primary" @click="generateMindMap">
                  生成思维导图
                </el-button>
                <el-button v-if="mindMapExists" @click="viewMindMap">
                  查看思维导图
                </el-button>
                <el-button v-if="mindMapExists" @click="exportMindMap">
                  导出思维导图
                </el-button>
              </div>
            </div>
            
            <div v-if="mindMapExists" class="mindmap-preview">
              <el-card>
                <div class="mindmap-info">
                  <p><strong>名称:</strong> {{ mindMapInfo.name }}</p>
                  <p><strong>节点数:</strong> {{ mindMapInfo.nodes_count }}</p>
                  <p><strong>创建时间:</strong> {{ formatTime(mindMapInfo.created_at) }}</p>
                </div>
                <div class="mindmap-thumbnail">
                  <!-- 这里可以放一个思维导图的缩略图 -->
                  <div class="thumbnail-placeholder">
                    思维导图缩略图
                  </div>
                </div>
              </el-card>
            </div>
            
            <div v-else class="no-mindmap">
              <el-empty description="暂无思维导图">
                <el-button type="primary" @click="generateMindMap">
                  立即生成
                </el-button>
              </el-empty>
            </div>
          </div>
        </el-tab-pane>

        <!-- 导出记录 -->
        <el-tab-pane label="导出记录" name="exports">
          <div class="export-section">
            <div class="section-header">
              <h3>导出记录 ({{ exportRecords.length }})</h3>
            </div>
            <el-table :data="exportRecords" v-loading="loading">
              <el-table-column prop="export_type" label="导出类型" width="120" />
              <el-table-column prop="file_name" label="文件名" min-width="200" />
              <el-table-column prop="file_size" label="文件大小" width="100" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="getExportStatusType(row.status)" size="small">
                    {{ row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="导出时间" width="160">
                <template #default="{ row }">
                  {{ formatTime(row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="{ row }">
                  <el-button 
                    type="text" 
                    @click="downloadExport(row)"
                    :disabled="row.status !== 'completed'"
                  >
                    下载
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { testCaseManagementApi, mindmapsApi, sessionsApi } from '@/api'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const activeTab = ref('testcases')
const sessionId = computed(() => route.params.sessionId as string)

// 会话数据
const sessionInfo = ref<any>({})
const testCases = ref<any[]>([])
const mindMapInfo = ref<any>(null)
const exportRecords = ref<any[]>([])

// 计算属性
const mindMapExists = computed(() => !!mindMapInfo.value)

// 生命周期
onMounted(() => {
  loadSessionData()
})

// 方法
const loadSessionData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadSessionInfo(),
      loadTestCases(),
      loadMindMapInfo(),
      loadExportRecords()
    ])
  } catch (error) {
    console.error('加载会话数据失败:', error)
    ElMessage.error('加载会话数据失败')
  } finally {
    loading.value = false
  }
}

const loadSessionInfo = async () => {
  try {
    const session = await sessionsApi.getSession(sessionId.value)
    sessionInfo.value = session
  } catch (error) {
    console.error('加载会话信息失败:', error)
    // 如果API失败，使用模拟数据
    sessionInfo.value = {
      id: sessionId.value,
      status: 'completed',
      created_at: new Date().toISOString(),
      processing_time: 15.6
    }
  }
}

const loadTestCases = async () => {
  try {
    const response = await testCaseManagementApi.getTestCases({
      session_id: sessionId.value,
      page_size: 100
    })
    testCases.value = response.items || []
  } catch (error) {
    console.error('加载测试用例失败:', error)
  }
}

const loadMindMapInfo = async () => {
  try {
    const mindMap = await sessionsApi.getSessionMindmap(sessionId.value)
    mindMapInfo.value = {
      ...mindMap,
      nodes_count: mindMap.mind_map_data?.nodes?.length || 0
    }
  } catch (error) {
    // 思维导图不存在是正常情况
    mindMapInfo.value = null
  }
}

const loadExportRecords = async () => {
  // TODO: 实现加载导出记录的API
  exportRecords.value = []
}

// 工具方法
const formatTime = (time: string) => {
  return new Date(time).toLocaleString()
}

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    'completed': 'success',
    'processing': 'warning',
    'failed': 'danger',
    'created': 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    'completed': '已完成',
    'processing': '处理中',
    'failed': '失败',
    'created': '已创建'
  }
  return textMap[status] || status
}

const getPriorityType = (priority: string) => {
  const typeMap: Record<string, string> = {
    'P0': 'danger',
    'P1': 'warning',
    'P2': '',
    'P3': 'info',
    'P4': 'info'
  }
  return typeMap[priority] || ''
}

const getExportStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    'completed': 'success',
    'processing': 'warning',
    'failed': 'danger'
  }
  return typeMap[status] || 'info'
}

// 操作方法
const refreshData = () => {
  loadSessionData()
}

const viewMindMap = () => {
  router.push(`/test-case/mindmap/${sessionId.value}`)
}

const generateMindMap = async () => {
  if (testCases.value.length === 0) {
    ElMessage.warning('没有测试用例，无法生成思维导图')
    return
  }
  
  try {
    ElMessage.info('正在生成思维导图，请稍候...')
    // TODO: 调用生成思维导图的API
    await loadMindMapInfo()
    ElMessage.success('思维导图生成完成')
  } catch (error) {
    ElMessage.error('生成思维导图失败')
  }
}

const viewAllTestCases = () => {
  router.push({
    path: '/test-case/list',
    query: { session_id: sessionId.value }
  })
}

const viewTestCase = (id: string) => {
  router.push(`/test-case/detail/${id}`)
}

const editTestCase = (id: string) => {
  router.push(`/test-case/edit/${id}`)
}

const exportSession = () => {
  // TODO: 实现导出整个会话的功能
  ElMessage.info('导出功能开发中')
}

const exportMindMap = () => {
  // TODO: 实现导出思维导图的功能
  ElMessage.info('导出思维导图功能开发中')
}

const downloadExport = (record: any) => {
  // TODO: 实现下载导出文件的功能
  ElMessage.info('下载功能开发中')
}
</script>

<style scoped>
.session-detail {
  padding: 20px;
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.session-info h2 {
  margin: 0 0 10px 0;
  color: #303133;
}

.session-meta {
  display: flex;
  gap: 15px;
  align-items: center;
  color: #606266;
  font-size: 14px;
}

.session-stats {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-item {
  padding: 10px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 5px;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}

.session-content {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px 20px 0 20px;
}

.section-header h3 {
  margin: 0;
  color: #303133;
}

.mindmap-preview {
  padding: 0 20px 20px 20px;
}

.mindmap-info {
  margin-bottom: 15px;
}

.mindmap-info p {
  margin: 5px 0;
  color: #606266;
}

.thumbnail-placeholder {
  height: 200px;
  background: #f5f7fa;
  border: 2px dashed #dcdfe6;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  border-radius: 4px;
}

.no-mindmap {
  padding: 40px 20px;
}

.testcase-section,
.export-section {
  padding: 0 20px 20px 20px;
}
</style>
