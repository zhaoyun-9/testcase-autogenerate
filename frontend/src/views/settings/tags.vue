<template>
  <div class="tag-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-info">
          <h1 class="page-title">标签管理</h1>
          <p class="page-subtitle">管理测试用例标签，支持项目级别的标签组织</p>
        </div>
        <div class="header-actions">
          <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
            新建标签
          </el-button>
        </div>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="search-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="搜索">
          <el-input
            v-model="searchForm.search"
            placeholder="输入标签名称搜索"
            :prefix-icon="Search"
            clearable
            @input="handleSearch"
          />
        </el-form-item>
        <el-form-item label="项目">
          <el-select
            v-model="searchForm.projectId"
            placeholder="选择项目"
            clearable
            @change="handleSearch"
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
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 标签列表 -->
    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <span>标签列表 ({{ pagination.total }})</span>
          <div class="header-actions">
            <el-button
              v-if="selectedTags.length > 0"
              type="danger"
              :icon="Delete"
              @click="handleBatchDelete"
            >
              批量删除 ({{ selectedTags.length }})
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="tags"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column label="标签名称" min-width="200">
          <template #default="{ row }">
            <el-tag
              :color="row.color"
              effect="light"
              size="small"
            >
              {{ row.name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="描述" prop="description" min-width="200" />
        <el-table-column label="所属项目" prop="project_name" width="150" />
        <el-table-column label="使用次数" prop="test_case_count" width="120" align="center">
          <template #default="{ row }">
            <el-badge :value="row.test_case_count" :max="999" />
          </template>
        </el-table-column>
        <el-table-column label="创建时间" prop="created_at" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              text
              @click="handleEdit(row)"
            >
              编辑
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

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingTag ? '编辑标签' : '新建标签'"
      width="500px"
    >
      <el-form
        ref="tagFormRef"
        :model="tagForm"
        :rules="tagRules"
        label-width="80px"
      >
        <el-form-item label="标签名称" prop="name">
          <el-input v-model="tagForm.name" placeholder="请输入标签名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="tagForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入标签描述"
          />
        </el-form-item>
        <el-form-item label="颜色" prop="color">
          <el-color-picker v-model="tagForm.color" />
        </el-form-item>
        <el-form-item label="所属项目" prop="project_id">
          <el-select
            v-model="tagForm.project_id"
            placeholder="选择项目（可选）"
            clearable
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          {{ editingTag ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Delete } from '@element-plus/icons-vue'
import { tagApi, tagUtils, type Tag } from '@/api/tag'
import { projectApi, type Project } from '@/api/project'

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const showCreateDialog = ref(false)
const editingTag = ref<Tag | null>(null)
const tags = ref<Tag[]>([])
const projects = ref<Project[]>([])
const selectedTags = ref<Tag[]>([])

// 搜索表单
const searchForm = reactive({
  search: '',
  projectId: ''
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 标签表单
const tagForm = reactive({
  name: '',
  description: '',
  color: tagUtils.generateTagColor('default'),
  project_id: ''
})

// 表单验证规则
const tagRules = {
  name: [
    { required: true, message: '请输入标签名称', trigger: 'blur' },
    { max: 50, message: '标签名称不能超过50个字符', trigger: 'blur' },
    {
      validator: (rule: any, value: string, callback: Function) => {
        const result = tagUtils.validateTagName(value)
        if (!result.valid) {
          callback(new Error(result.message))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 表单引用
const tagFormRef = ref()

// 方法
const loadTags = async () => {
  loading.value = true
  try {
    const response = await tagApi.getTags({
      page: pagination.page,
      page_size: pagination.pageSize,
      search: searchForm.search || undefined,
      project_id: searchForm.projectId || undefined
    })
    tags.value = response.items
    pagination.total = response.total
  } catch (error) {
    ElMessage.error('加载标签列表失败')
  } finally {
    loading.value = false
  }
}

const loadProjects = async () => {
  try {
    const response = await projectApi.getProjects({ page_size: 100 })
    projects.value = response.items
  } catch (error) {
    console.error('加载项目列表失败:', error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadTags()
}

const handleReset = () => {
  searchForm.search = ''
  searchForm.projectId = ''
  handleSearch()
}

const handlePageChange = () => {
  loadTags()
}

const handlePageSizeChange = () => {
  pagination.page = 1
  loadTags()
}

const handleSelectionChange = (selection: Tag[]) => {
  selectedTags.value = selection
}

const handleEdit = (tag: Tag) => {
  editingTag.value = tag
  tagForm.name = tag.name
  tagForm.description = tag.description || ''
  tagForm.color = tag.color || tagUtils.generateTagColor(tag.name)
  tagForm.project_id = tag.project_id || ''
  showCreateDialog.value = true
}

const handleDelete = async (tag: Tag) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除标签"${tag.name}"吗？`,
      '确认删除',
      { type: 'warning' }
    )
    
    await tagApi.deleteTag(tag.id)
    ElMessage.success('删除成功')
    loadTags()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedTags.value.length} 个标签吗？`,
      '确认批量删除',
      { type: 'warning' }
    )
    
    const ids = selectedTags.value.map(item => item.id)
    await tagApi.batchDeleteTags(ids)
    ElMessage.success('批量删除成功')
    loadTags()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

const handleSubmit = async () => {
  try {
    await tagFormRef.value.validate()
    
    submitting.value = true
    
    if (editingTag.value) {
      await tagApi.updateTag(editingTag.value.id, tagForm)
      ElMessage.success('更新成功')
    } else {
      await tagApi.createTag(tagForm)
      ElMessage.success('创建成功')
    }
    
    showCreateDialog.value = false
    resetForm()
    loadTags()
  } catch (error) {
    ElMessage.error(editingTag.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

const resetForm = () => {
  editingTag.value = null
  tagForm.name = ''
  tagForm.description = ''
  tagForm.color = tagUtils.generateTagColor('default')
  tagForm.project_id = ''
  tagFormRef.value?.resetFields()
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadTags()
  loadProjects()
})
</script>

<style scoped>
.tag-management {
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

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
