<template>
  <div class="mindmap-list">
    <!-- 页面头部 -->
    <TcPageHeader
      title="思维导图管理"
      subtitle="查看和管理所有生成的测试用例思维导图"
      :actions="headerActions"
    />

    <!-- 搜索和过滤 -->
    <TcCard class="search-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="搜索">
          <el-input
            v-model="searchForm.search"
            placeholder="搜索思维导图名称或会话ID"
            clearable
            style="width: 300px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="项目">
          <el-select
            v-model="searchForm.project_id"
            placeholder="选择项目"
            clearable
            style="width: 200px"
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
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

    <!-- 思维导图列表 -->
    <TcCard>
      <template #header>
        <div class="list-header">
          <h3>思维导图列表</h3>
          <div class="list-actions">
            <el-button @click="refreshList">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="mindmapList"
        v-loading="loading"
        row-key="id"
        @row-click="handleRowClick"
      >
        <el-table-column prop="name" label="名称" min-width="200">
          <template #default="{ row }">
            <div class="mindmap-name">
              <el-icon class="mindmap-icon"><Share /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="session_id" label="会话ID" width="120">
          <template #default="{ row }">
            <el-tag size="small" type="info">
              {{ row.session_id.slice(0, 8) }}...
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="project_name" label="项目" width="150">
          <template #default="{ row }">
            <span v-if="row.project_name">{{ row.project_name }}</span>
            <span v-else class="text-placeholder">未分配</span>
          </template>
        </el-table-column>
        
        <el-table-column label="统计信息" width="200">
          <template #default="{ row }">
            <div class="mindmap-stats">
              <el-tag size="small">
                {{ getNodeCount(row) }} 节点
              </el-tag>
              <el-tag size="small" type="success">
                {{ getEdgeCount(row) }} 连接
              </el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click.stop="viewMindmap(row)">
              <el-icon><View /></el-icon>
              查看
            </el-button>
            <el-button size="small" @click.stop="viewSession(row)">
              <el-icon><Document /></el-icon>
              会话
            </el-button>
            <el-dropdown @command="(command) => handleDropdownCommand(command, row)">
              <el-button size="small">
                更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="export">
                    <el-icon><Download /></el-icon>
                    导出
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" divided>
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
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
    <TcCard v-if="!loading && mindmapList.length === 0" class="empty-state">
      <el-empty description="暂无思维导图">
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { mindmapsApi, projectsApi } from '@/api'
import TcPageHeader from '@/components/ui/TcPageHeader/index.vue'
import TcCard from '@/components/ui/TcCard/index.vue'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const mindmapList = ref<any[]>([])
const projects = ref<any[]>([])

// 搜索表单
const searchForm = reactive({
  search: '',
  project_id: ''
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
  loadProjects()
  loadMindmapList()
})

// 方法
const loadProjects = async () => {
  try {
    const response = await projectsApi.getProjects({ page_size: 100 })
    projects.value = response.items || []
  } catch (error) {
    console.error('加载项目列表失败:', error)
  }
}

const loadMindmapList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      search: searchForm.search || undefined,
      project_id: searchForm.project_id || undefined
    }
    
    const response = await mindmapsApi.getMindmaps(params)
    mindmapList.value = response.items || []
    pagination.total = response.total || 0
  } catch (error) {
    console.error('加载思维导图列表失败:', error)
    ElMessage.error('加载思维导图列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadMindmapList()
}

const handleReset = () => {
  searchForm.search = ''
  searchForm.project_id = ''
  pagination.page = 1
  loadMindmapList()
}

const refreshList = () => {
  loadMindmapList()
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  loadMindmapList()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadMindmapList()
}

const handleRowClick = (row: any) => {
  viewMindmap(row)
}

const viewMindmap = (row: any) => {
  router.push(`/test-case/mindmap/${row.session_id}`)
}

const viewSession = (row: any) => {
  router.push(`/test-case/session/${row.session_id}`)
}

const handleDropdownCommand = async (command: string, row: any) => {
  switch (command) {
    case 'export':
      await exportMindmap(row)
      break
    case 'delete':
      await deleteMindmap(row)
      break
  }
}

const exportMindmap = async (row: any) => {
  try {
    ElMessage.info('导出功能开发中')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const deleteMindmap = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除思维导图"${row.name}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await mindmapsApi.deleteMindmap(row.id)
    ElMessage.success('删除成功')
    loadMindmapList()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 工具方法
const formatTime = (time: string) => {
  return new Date(time).toLocaleString()
}

const getNodeCount = (row: any) => {
  return row.mind_map_data?.nodes?.length || 0
}

const getEdgeCount = (row: any) => {
  return row.mind_map_data?.edges?.length || 0
}
</script>

<style scoped>
.mindmap-list {
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

.mindmap-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mindmap-icon {
  color: #409EFF;
}

.mindmap-stats {
  display: flex;
  gap: 8px;
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
