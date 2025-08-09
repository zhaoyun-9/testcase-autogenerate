<template>
  <div class="session-list">
    <!-- 页面头部 -->
    <TcPageHeader
      title="会话管理"
      subtitle="查看和管理所有测试用例生成会话"
      :actions="headerActions"
    />

    <!-- 搜索和过滤 -->
    <TcCard class="search-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="搜索">
          <el-input
            v-model="searchForm.search"
            placeholder="搜索会话ID"
            clearable
            style="width: 300px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="searchForm.status"
            placeholder="选择状态"
            clearable
            style="width: 150px"
          >
            <el-option label="已完成" value="completed" />
            <el-option label="处理中" value="processing" />
            <el-option label="失败" value="failed" />
            <el-option label="已创建" value="created" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select
            v-model="searchForm.session_type"
            placeholder="选择类型"
            clearable
            style="width: 150px"
          >
            <el-option label="文档解析" value="document_parse" />
            <el-option label="图片分析" value="image_analysis" />
            <el-option label="API规范" value="api_spec_parse" />
            <el-option label="数据库架构" value="database_schema_parse" />
            <el-option label="视频分析" value="video_analysis" />
            <el-option label="手动输入" value="manual_input" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
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

    <!-- 会话列表 -->
    <TcCard>
      <template #header>
        <div class="list-header">
          <h3>会话列表</h3>
          <div class="list-actions">
            <el-button @click="refreshList">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="sessionList"
        v-loading="loading"
        row-key="id"
        @row-click="handleRowClick"
      >
        <el-table-column prop="id" label="会话ID" width="120">
          <template #default="{ row }">
            <el-tag size="small" type="info">
              {{ row.id.slice(0, 8) }}...
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="session_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="getSessionTypeColor(row.session_type)">
              {{ getSessionTypeText(row.session_type) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="getStatusColor(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="generated_count" label="生成数量" width="100">
          <template #default="{ row }">
            <span class="count-text">{{ row.generated_count }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="思维导图" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.mind_map_exists" size="small" type="success">
              已生成
            </el-tag>
            <el-tag v-else size="small" type="info">
              未生成
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="processing_time" label="处理时间" width="100">
          <template #default="{ row }">
            <span v-if="row.processing_time">{{ row.processing_time }}s</span>
            <span v-else class="text-placeholder">-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click.stop="viewSession(row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
            <el-button 
              v-if="row.mind_map_exists" 
              size="small" 
              @click.stop="viewMindmap(row)"
            >
              <el-icon><Share /></el-icon>
              思维导图
            </el-button>
            <el-button size="small" @click.stop="viewTestCases(row)">
              <el-icon><Document /></el-icon>
              用例
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </TcCard>

    <!-- 空状态 -->
    <TcCard v-if="!loading && sessionList.length === 0" class="empty-state">
      <el-empty description="暂无会话记录">
        <el-button type="primary" @click="$router.push('/test-case/generate')">
          立即生成测试用例
        </el-button>
      </el-empty>
    </TcCard>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { sessionsApi } from '@/api'
import TcPageHeader from '@/components/ui/TcPageHeader/index.vue'
import TcCard from '@/components/ui/TcCard/index.vue'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const sessionList = ref<any[]>([])

// 搜索表单
const searchForm = reactive({
  search: '',
  status: '',
  session_type: ''
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 页面头部操作
const headerActions = computed(() => [
  {
    type: 'button' as const,
    label: '生成测试用例',
    buttonType: 'primary' as const,
    icon: 'Plus',
    handler: () => router.push('/test-case/generate')
  }
])

// 生命周期
onMounted(() => {
  loadSessionList()
})

// 方法
const loadSessionList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      status: searchForm.status || undefined,
      session_type: searchForm.session_type || undefined
    }
    
    const response = await sessionsApi.getSessions(params)
    sessionList.value = response.items || []
    pagination.total = response.total || 0
  } catch (error) {
    console.error('加载会话列表失败:', error)
    ElMessage.error('加载会话列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadSessionList()
}

const handleReset = () => {
  searchForm.search = ''
  searchForm.status = ''
  searchForm.session_type = ''
  pagination.page = 1
  loadSessionList()
}

const refreshList = () => {
  loadSessionList()
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  loadSessionList()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadSessionList()
}

const handleRowClick = (row: any) => {
  viewSession(row)
}

const viewSession = (row: any) => {
  router.push(`/test-case/session/${row.id}`)
}

const viewMindmap = (row: any) => {
  router.push(`/test-case/mindmap/${row.id}`)
}

const viewTestCases = (row: any) => {
  router.push({
    path: '/test-case/management',
    query: { session_id: row.id }
  })
}

// 工具方法
const formatTime = (time: string) => {
  return new Date(time).toLocaleString()
}

const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    'completed': 'success',
    'processing': 'warning',
    'failed': 'danger',
    'created': 'info'
  }
  return colorMap[status] || 'info'
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

const getSessionTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    'document_parse': 'primary',
    'image_analysis': 'success',
    'api_spec_parse': 'warning',
    'database_schema_parse': 'danger',
    'video_analysis': 'info',
    'manual_input': ''
  }
  return colorMap[type] || ''
}

const getSessionTypeText = (type: string) => {
  const textMap: Record<string, string> = {
    'document_parse': '文档解析',
    'image_analysis': '图片分析',
    'api_spec_parse': 'API规范',
    'database_schema_parse': '数据库架构',
    'video_analysis': '视频分析',
    'manual_input': '手动输入'
  }
  return textMap[type] || type
}
</script>

<style scoped>
.session-list {
  padding: 20px;
}

.search-card {
  margin-bottom: 20px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.list-header h3 {
  margin: 0;
  color: #303133;
}

.count-text {
  font-weight: 600;
  color: #409EFF;
}

.text-placeholder {
  color: #909399;
  font-style: italic;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.empty-state {
  margin-top: 20px;
  text-align: center;
}
</style>
