<template>
  <div class="category-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-info">
          <h1 class="page-title">分类管理</h1>
          <p class="page-subtitle">管理测试用例分类，支持项目级别的分类组织</p>
        </div>
        <div class="header-actions">
          <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
            新建分类
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
            placeholder="输入分类名称搜索"
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

    <!-- 分类列表 -->
    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <span>分类列表 ({{ pagination.total }})</span>
          <div class="header-actions">
            <el-button
              v-if="selectedCategories.length > 0"
              type="danger"
              :icon="Delete"
              @click="handleBatchDelete"
            >
              批量删除 ({{ selectedCategories.length }})
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="categories"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column label="分类名称" min-width="200">
          <template #default="{ row }">
            <div class="category-info">
              <div
                class="category-color"
                :style="{ backgroundColor: row.color }"
              />
              <span class="category-name">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="描述" prop="description" min-width="200" />
        <el-table-column label="所属项目" prop="project_name" width="150" />
        <el-table-column label="测试用例数" prop="test_case_count" width="120" align="center" />
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
      :title="editingCategory ? '编辑分类' : '新建分类'"
      width="500px"
    >
      <el-form
        ref="categoryFormRef"
        :model="categoryForm"
        :rules="categoryRules"
        label-width="80px"
      >
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="categoryForm.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="categoryForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入分类描述"
          />
        </el-form-item>
        <el-form-item label="颜色" prop="color">
          <el-color-picker v-model="categoryForm.color" />
        </el-form-item>
        <el-form-item label="所属项目" prop="project_id">
          <el-select
            v-model="categoryForm.project_id"
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
          {{ editingCategory ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Delete } from '@element-plus/icons-vue'
import { categoryApi, categoryUtils, type Category } from '@/api/category'
import { projectApi, type Project } from '@/api/project'

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const showCreateDialog = ref(false)
const editingCategory = ref<Category | null>(null)
const categories = ref<Category[]>([])
const projects = ref<Project[]>([])
const selectedCategories = ref<Category[]>([])

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

// 分类表单
const categoryForm = reactive({
  name: '',
  description: '',
  color: categoryUtils.generateCategoryColor('default'),
  project_id: ''
})

// 表单验证规则
const categoryRules = {
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' },
    { max: 100, message: '分类名称不能超过100个字符', trigger: 'blur' }
  ]
}

// 表单引用
const categoryFormRef = ref()

// 方法
const loadCategories = async () => {
  loading.value = true
  try {
    const response = await categoryApi.getCategories({
      page: pagination.page,
      page_size: pagination.pageSize,
      search: searchForm.search || undefined,
      project_id: searchForm.projectId || undefined
    })
    categories.value = response.items
    pagination.total = response.total
  } catch (error) {
    ElMessage.error('加载分类列表失败')
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
  loadCategories()
}

const handleReset = () => {
  searchForm.search = ''
  searchForm.projectId = ''
  handleSearch()
}

const handlePageChange = () => {
  loadCategories()
}

const handlePageSizeChange = () => {
  pagination.page = 1
  loadCategories()
}

const handleSelectionChange = (selection: Category[]) => {
  selectedCategories.value = selection
}

const handleEdit = (category: Category) => {
  editingCategory.value = category
  categoryForm.name = category.name
  categoryForm.description = category.description || ''
  categoryForm.color = category.color || categoryUtils.generateCategoryColor(category.name)
  categoryForm.project_id = category.project_id || ''
  showCreateDialog.value = true
}

const handleDelete = async (category: Category) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除分类"${category.name}"吗？`,
      '确认删除',
      { type: 'warning' }
    )
    
    await categoryApi.deleteCategory(category.id)
    ElMessage.success('删除成功')
    loadCategories()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedCategories.value.length} 个分类吗？`,
      '确认批量删除',
      { type: 'warning' }
    )
    
    const ids = selectedCategories.value.map(item => item.id)
    await categoryApi.batchDeleteCategories(ids)
    ElMessage.success('批量删除成功')
    loadCategories()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

const handleSubmit = async () => {
  try {
    await categoryFormRef.value.validate()
    
    submitting.value = true
    
    if (editingCategory.value) {
      await categoryApi.updateCategory(editingCategory.value.id, categoryForm)
      ElMessage.success('更新成功')
    } else {
      await categoryApi.createCategory(categoryForm)
      ElMessage.success('创建成功')
    }
    
    showCreateDialog.value = false
    resetForm()
    loadCategories()
  } catch (error) {
    ElMessage.error(editingCategory.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

const resetForm = () => {
  editingCategory.value = null
  categoryForm.name = ''
  categoryForm.description = ''
  categoryForm.color = categoryUtils.generateCategoryColor('default')
  categoryForm.project_id = ''
  categoryFormRef.value?.resetFields()
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadCategories()
  loadProjects()
})
</script>

<style scoped>
.category-management {
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

.category-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.category-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid #e5e7eb;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
