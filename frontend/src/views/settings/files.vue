<template>
  <div class="file-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-info">
          <h1 class="page-title">文件管理</h1>
          <p class="page-subtitle">管理上传的文件，查看文件类型支持和存储使用情况</p>
        </div>
        <div class="header-actions">
          <el-button type="primary" :icon="Upload" @click="showUploadDialog = true">
            上传文件
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ fileStats.total_files }}</div>
            <div class="stat-label">总文件数</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><FolderOpened /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ formatFileSize(fileStats.total_size) }}</div>
            <div class="stat-label">总大小</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><Picture /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ fileStats.image_count }}</div>
            <div class="stat-label">图片文件</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><VideoPlay /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ fileStats.video_count }}</div>
            <div class="stat-label">视频文件</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="search-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="搜索">
          <el-input
            v-model="searchForm.search"
            placeholder="输入文件名搜索"
            :prefix-icon="Search"
            clearable
            @input="handleSearch"
          />
        </el-form-item>
        <el-form-item label="文件类型">
          <el-select
            v-model="searchForm.fileType"
            placeholder="选择文件类型"
            clearable
            @change="handleSearch"
          >
            <el-option label="文档" value="document" />
            <el-option label="图片" value="image" />
            <el-option label="视频" value="video" />
            <el-option label="API规范" value="api_spec" />
            <el-option label="数据库Schema" value="database_schema" />
          </el-select>
        </el-form-item>
        <el-form-item label="上传时间">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            @change="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 文件列表 -->
    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <span>文件列表 ({{ pagination.total }})</span>
          <div class="header-actions">
            <el-button
              v-if="selectedFiles.length > 0"
              type="danger"
              :icon="Delete"
              @click="handleBatchDelete"
            >
              批量删除 ({{ selectedFiles.length }})
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="files"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column label="文件名" min-width="200">
          <template #default="{ row }">
            <div class="file-info">
              <el-icon class="file-icon">
                <component :is="getFileIcon(row.file_type)" />
              </el-icon>
              <span class="file-name">{{ row.original_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="类型" prop="file_type" width="120">
          <template #default="{ row }">
            <el-tag :type="getFileTypeColor(row.file_type)" size="small">
              {{ getFileTypeText(row.file_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="大小" prop="file_size" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column label="上传时间" prop="created_at" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="使用状态" prop="usage_count" width="100" align="center">
          <template #default="{ row }">
            <el-badge :value="row.usage_count" :max="99" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              text
              @click="handlePreview(row)"
            >
              预览
            </el-button>
            <el-button
              type="success"
              size="small"
              text
              @click="handleDownload(row)"
            >
              下载
            </el-button>
            <el-button
              type="danger"
              size="small"
              text
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
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
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传文件"
      width="600px"
    >
      <el-upload
        ref="uploadRef"
        :action="uploadAction"
        :headers="uploadHeaders"
        :data="uploadData"
        :multiple="true"
        :show-file-list="true"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
        drag
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持文档、图片、视频、API规范、数据库Schema等文件类型
          </div>
        </template>
      </el-upload>
      
      <template #footer>
        <el-button @click="showUploadDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 文件预览对话框 -->
    <el-dialog
      v-model="showPreviewDialog"
      :title="previewFile?.original_name"
      width="80%"
      top="5vh"
    >
      <div class="file-preview">
        <div v-if="previewFile?.file_type === 'image'" class="image-preview">
          <img :src="getFileUrl(previewFile)" alt="预览图片" />
        </div>
        <div v-else-if="previewFile?.file_type === 'document'" class="document-preview">
          <iframe :src="getFileUrl(previewFile)" width="100%" height="500px"></iframe>
        </div>
        <div v-else class="unsupported-preview">
          <el-icon size="48"><Document /></el-icon>
          <p>该文件类型不支持预览</p>
          <el-button type="primary" @click="handleDownload(previewFile)">
            下载文件
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Upload, Search, Delete, Document, FolderOpened, 
  Picture, VideoPlay, UploadFilled 
} from '@element-plus/icons-vue'
import { fileApi } from '@/api/testCase'

// 响应式数据
const loading = ref(false)
const showUploadDialog = ref(false)
const showPreviewDialog = ref(false)
const files = ref([])
const selectedFiles = ref([])
const previewFile = ref(null)

// 文件统计
const fileStats = ref({
  total_files: 0,
  total_size: 0,
  image_count: 0,
  video_count: 0,
  document_count: 0
})

// 搜索表单
const searchForm = reactive({
  search: '',
  fileType: '',
  dateRange: null
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 上传配置
const uploadAction = '/api/v1/files/upload'
const uploadHeaders = {}
const uploadData = {}

// 方法
const loadFiles = async () => {
  loading.value = true
  try {
    // 这里应该调用实际的文件列表API
    // const response = await fileApi.getFiles({...})
    // 模拟数据
    files.value = []
    pagination.total = 0
  } catch (error) {
    ElMessage.error('加载文件列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadFiles()
}

const handleReset = () => {
  searchForm.search = ''
  searchForm.fileType = ''
  searchForm.dateRange = null
  handleSearch()
}

const handlePageChange = () => {
  loadFiles()
}

const handlePageSizeChange = () => {
  pagination.page = 1
  loadFiles()
}

const handleSelectionChange = (selection: any[]) => {
  selectedFiles.value = selection
}

const handlePreview = (file: any) => {
  previewFile.value = file
  showPreviewDialog.value = true
}

const handleDownload = (file: any) => {
  const link = document.createElement('a')
  link.href = getFileUrl(file)
  link.download = file.original_name
  link.click()
}

const handleDelete = async (file: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文件"${file.original_name}"吗？`,
      '确认删除',
      { type: 'warning' }
    )
    
    // await fileApi.deleteFile(file.id)
    ElMessage.success('删除成功')
    loadFiles()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedFiles.value.length} 个文件吗？`,
      '确认批量删除',
      { type: 'warning' }
    )
    
    // const ids = selectedFiles.value.map(item => item.id)
    // await fileApi.batchDeleteFiles(ids)
    ElMessage.success('批量删除成功')
    loadFiles()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

const beforeUpload = (file: File) => {
  const maxSize = 100 * 1024 * 1024 // 100MB
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过100MB')
    return false
  }
  return true
}

const handleUploadSuccess = () => {
  ElMessage.success('上传成功')
  loadFiles()
}

const handleUploadError = () => {
  ElMessage.error('上传失败')
}

// 工具函数
const formatFileSize = (bytes: number) => {
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const getFileIcon = (fileType: string) => {
  const iconMap: Record<string, any> = {
    'document': Document,
    'image': Picture,
    'video': VideoPlay,
    'api_spec': Document,
    'database_schema': Document
  }
  return iconMap[fileType] || Document
}

const getFileTypeColor = (fileType: string) => {
  const colorMap: Record<string, any> = {
    'document': 'primary',
    'image': 'success',
    'video': 'warning',
    'api_spec': 'info',
    'database_schema': 'danger'
  }
  return colorMap[fileType] || 'info'
}

const getFileTypeText = (fileType: string) => {
  const textMap: Record<string, string> = {
    'document': '文档',
    'image': '图片',
    'video': '视频',
    'api_spec': 'API规范',
    'database_schema': '数据库Schema'
  }
  return textMap[fileType] || '未知'
}

const getFileUrl = (file: any) => {
  return `/uploads/${file.file_path}`
}

// 生命周期
onMounted(() => {
  loadFiles()
})
</script>

<style scoped>
.file-management {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.page-subtitle {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  .stat-content {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 8px;
    background: #f3f4f6;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #6b7280;
  }

  .stat-info {
    .stat-value {
      font-size: 24px;
      font-weight: 600;
      color: #1f2937;
      margin-bottom: 4px;
    }

    .stat-label {
      font-size: 14px;
      color: #6b7280;
    }
  }
}

.search-card {
  margin-bottom: 20px;
}

.list-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  color: #6b7280;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.file-preview {
  .image-preview img {
    max-width: 100%;
    height: auto;
  }

  .unsupported-preview {
    text-align: center;
    padding: 40px;
    color: #6b7280;
  }
}
</style>
