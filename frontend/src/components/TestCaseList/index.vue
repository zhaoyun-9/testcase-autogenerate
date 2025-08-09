<template>
  <div class="test-case-list">
    <!-- 工具栏 -->
    <div v-if="showToolbar" class="toolbar">
      <div class="toolbar-left">
        <el-checkbox
          v-if="showSelection"
          :indeterminate="isIndeterminate"
          v-model="checkAll"
          @change="handleCheckAllChange"
        >
          全选
        </el-checkbox>
        
        <span v-if="selectedCount > 0" class="selection-info">
          已选择 {{ selectedCount }} 项
        </span>
      </div>
      
      <div class="toolbar-right">
        <el-button-group v-if="showActions && selectedCount > 0">
          <el-button size="small" @click="handleBatchEdit">
            <el-icon><Edit /></el-icon>
            批量编辑
          </el-button>
          <el-button size="small" @click="handleBatchDelete">
            <el-icon><Delete /></el-icon>
            批量删除
          </el-button>
        </el-button-group>
        
        <el-dropdown v-if="showViewOptions" @command="handleViewCommand">
          <el-button size="small">
            视图选项
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="card">卡片视图</el-dropdown-item>
              <el-dropdown-item command="table">表格视图</el-dropdown-item>
              <el-dropdown-item command="compact">紧凑视图</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 测试用例列表 -->
    <div class="test-case-items" :class="`view-${viewMode}`">
      <div
        v-for="testCase in testCases"
        :key="testCase.id"
        class="test-case-item"
        :class="{ 'is-selected': selectedIds.includes(testCase.id) }"
      >
        <!-- 选择框 -->
        <div v-if="showSelection" class="item-selection">
          <el-checkbox
            :model-value="selectedIds.includes(testCase.id)"
            @change="handleItemSelect(testCase.id, $event)"
          />
        </div>

        <!-- 测试用例内容 -->
        <div class="item-content" @click="handleItemClick(testCase)">
          <!-- 标题和基本信息 -->
          <div class="item-header">
            <h3 class="item-title" :title="testCase.title">
              {{ testCase.title }}
            </h3>
            
            <div class="item-meta">
              <el-tag
                :type="getTestTypeTagType(testCase.testType)"
                size="small"
              >
                {{ getTestTypeLabel(testCase.testType) }}
              </el-tag>
              
              <el-tag
                :type="getPriorityTagType(testCase.priority)"
                size="small"
              >
                {{ testCase.priority }}
              </el-tag>
              
              <el-tag
                :type="getStatusTagType(testCase.status)"
                size="small"
              >
                {{ getStatusLabel(testCase.status) }}
              </el-tag>
            </div>
          </div>

          <!-- 描述 -->
          <div v-if="testCase.description" class="item-description">
            {{ testCase.description }}
          </div>

          <!-- 测试步骤预览 -->
          <div v-if="testCase.testSteps?.length > 0" class="item-steps">
            <div class="steps-header">
              <el-icon><List /></el-icon>
              <span>测试步骤 ({{ testCase.testSteps.length }})</span>
            </div>
            <div class="steps-preview">
              <div
                v-for="(step, index) in testCase.testSteps.slice(0, 3)"
                :key="index"
                class="step-item"
              >
                <span class="step-number">{{ step.step }}</span>
                <span class="step-action">{{ step.action }}</span>
              </div>
              <div v-if="testCase.testSteps.length > 3" class="step-more">
                还有 {{ testCase.testSteps.length - 3 }} 个步骤...
              </div>
            </div>
          </div>

          <!-- 标签 -->
          <div v-if="testCase.tags?.length > 0" class="item-tags">
            <el-tag
              v-for="tag in testCase.tags.slice(0, 5)"
              :key="tag"
              size="small"
              type="info"
              effect="plain"
            >
              {{ tag }}
            </el-tag>
            <span v-if="testCase.tags.length > 5" class="more-tags">
              +{{ testCase.tags.length - 5 }}
            </span>
          </div>

          <!-- 底部信息 -->
          <div class="item-footer">
            <div class="footer-left">
              <span class="create-time">
                创建于 {{ formatTime(testCase.createdAt) }}
              </span>
              <span v-if="testCase.updatedAt" class="update-time">
                更新于 {{ formatTime(testCase.updatedAt) }}
              </span>
            </div>
            
            <div class="footer-right">
              <span class="test-level">{{ getTestLevelLabel(testCase.testLevel) }}</span>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div v-if="showActions" class="item-actions">
          <el-dropdown @command="(command) => handleActionCommand(command, testCase)">
            <el-button type="link" size="small">
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="view">
                  <el-icon><View /></el-icon>
                  查看详情
                </el-dropdown-item>
                <el-dropdown-item command="edit">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-dropdown-item>
                <el-dropdown-item command="copy">
                  <el-icon><CopyDocument /></el-icon>
                  复制
                </el-dropdown-item>
                <el-dropdown-item command="delete" divided>
                  <el-icon><Delete /></el-icon>
                  删除
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="testCases.length === 0" class="empty-state">
      <el-empty
        description="暂无测试用例"
        :image-size="120"
      >
        <el-button type="primary" @click="$emit('create')">
          创建测试用例
        </el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { TestCase } from '@/types/testCase'
import { 
  TEST_TYPE_OPTIONS, 
  TEST_LEVEL_OPTIONS, 
  STATUS_OPTIONS 
} from '@/types/testCase'
import dayjs from 'dayjs'

interface Props {
  testCases: TestCase[]
  showSelection?: boolean
  showActions?: boolean
  showToolbar?: boolean
  showViewOptions?: boolean
  viewMode?: 'card' | 'table' | 'compact'
}

interface Emits {
  (e: 'selection-change', selectedIds: string[]): void
  (e: 'item-click', testCase: TestCase): void
  (e: 'view', testCase: TestCase): void
  (e: 'edit', testCase: TestCase): void
  (e: 'copy', testCase: TestCase): void
  (e: 'delete', testCase: TestCase): void
  (e: 'batch-edit', selectedIds: string[]): void
  (e: 'batch-delete', selectedIds: string[]): void
  (e: 'create'): void
}

const props = withDefaults(defineProps<Props>(), {
  showSelection: false,
  showActions: true,
  showToolbar: true,
  showViewOptions: true,
  viewMode: 'card'
})

const emit = defineEmits<Emits>()

const selectedIds = ref<string[]>([])
const viewMode = ref(props.viewMode)

// 计算属性
const selectedCount = computed(() => selectedIds.value.length)

const checkAll = computed({
  get: () => selectedIds.value.length === props.testCases.length && props.testCases.length > 0,
  set: (value: boolean) => {
    if (value) {
      selectedIds.value = props.testCases.map(tc => tc.id)
    } else {
      selectedIds.value = []
    }
    emit('selection-change', selectedIds.value)
  }
})

const isIndeterminate = computed(() => 
  selectedIds.value.length > 0 && selectedIds.value.length < props.testCases.length
)

// 处理全选
const handleCheckAllChange = (value: boolean) => {
  checkAll.value = value
}

// 处理单项选择
const handleItemSelect = (id: string, checked: boolean) => {
  if (checked) {
    if (!selectedIds.value.includes(id)) {
      selectedIds.value.push(id)
    }
  } else {
    const index = selectedIds.value.indexOf(id)
    if (index > -1) {
      selectedIds.value.splice(index, 1)
    }
  }
  emit('selection-change', selectedIds.value)
}

// 处理项目点击
const handleItemClick = (testCase: TestCase) => {
  emit('item-click', testCase)
}

// 处理操作命令
const handleActionCommand = (command: string, testCase: TestCase) => {
  switch (command) {
    case 'view':
      emit('view', testCase)
      break
    case 'edit':
      emit('edit', testCase)
      break
    case 'copy':
      emit('copy', testCase)
      break
    case 'delete':
      handleDeleteConfirm(testCase)
      break
  }
}

// 删除确认
const handleDeleteConfirm = async (testCase: TestCase) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除测试用例"${testCase.title}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    emit('delete', testCase)
  } catch {
    // 用户取消
  }
}

// 批量编辑
const handleBatchEdit = () => {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要编辑的测试用例')
    return
  }
  emit('batch-edit', selectedIds.value)
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要删除的测试用例')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIds.value.length} 个测试用例吗？`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    emit('batch-delete', selectedIds.value)
  } catch {
    // 用户取消
  }
}

// 处理视图命令
const handleViewCommand = (command: string) => {
  viewMode.value = command as 'card' | 'table' | 'compact'
}

// 获取测试类型标签类型
const getTestTypeTagType = (testType: string) => {
  const typeMap: Record<string, string> = {
    'functional': 'primary',
    'interface': 'success',
    'performance': 'warning',
    'security': 'danger',
    'compatibility': 'info',
    'usability': ''
  }
  return typeMap[testType] || ''
}

// 获取测试类型标签
const getTestTypeLabel = (testType: string) => {
  const option = TEST_TYPE_OPTIONS.find(opt => opt.value === testType)
  return option?.label || testType
}

// 获取优先级标签类型
const getPriorityTagType = (priority: string) => {
  const typeMap: Record<string, string> = {
    'P0': 'danger',
    'P1': 'warning',
    'P2': 'primary',
    'P3': 'info',
    'P4': ''
  }
  return typeMap[priority] || ''
}

// 获取状态标签类型
const getStatusTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    'draft': 'info',
    'review': 'warning',
    'approved': 'success',
    'deprecated': 'danger'
  }
  return typeMap[status] || ''
}

// 获取状态标签
const getStatusLabel = (status: string) => {
  const option = STATUS_OPTIONS.find(opt => opt.value === status)
  return option?.label || status
}

// 获取测试级别标签
const getTestLevelLabel = (testLevel: string) => {
  const option = TEST_LEVEL_OPTIONS.find(opt => opt.value === testLevel)
  return option?.label || testLevel
}

// 格式化时间
const formatTime = (time: string) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

// 暴露方法
defineExpose({
  getSelectedIds: () => selectedIds.value,
  clearSelection: () => {
    selectedIds.value = []
    emit('selection-change', selectedIds.value)
  }
})
</script>

<style lang="scss" scoped>
.test-case-list {
  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding: 12px 0;
    border-bottom: 1px solid var(--el-border-color-light);
    
    .toolbar-left {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .selection-info {
        font-size: 14px;
        color: var(--el-text-color-regular);
      }
    }
    
    .toolbar-right {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }
  
  .test-case-items {
    &.view-card {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
      gap: 16px;
    }
    
    &.view-table {
      // 表格视图样式
    }
    
    &.view-compact {
      .test-case-item {
        .item-content {
          padding: 12px;
        }
        
        .item-description,
        .item-steps {
          display: none;
        }
      }
    }
  }
  
  .test-case-item {
    display: flex;
    border: 1px solid var(--el-border-color-light);
    border-radius: 8px;
    background-color: var(--el-bg-color);
    transition: all 0.3s ease;
    
    &:hover {
      border-color: var(--el-color-primary-light-7);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    &.is-selected {
      border-color: var(--el-color-primary);
      background-color: var(--el-color-primary-light-9);
    }
    
    .item-selection {
      padding: 16px 12px;
      border-right: 1px solid var(--el-border-color-lighter);
    }
    
    .item-content {
      flex: 1;
      padding: 16px;
      cursor: pointer;
      
      .item-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 12px;
        
        .item-title {
          font-size: 16px;
          font-weight: 500;
          color: var(--el-text-color-primary);
          margin: 0;
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          margin-right: 12px;
        }
        
        .item-meta {
          display: flex;
          gap: 8px;
          flex-shrink: 0;
        }
      }
      
      .item-description {
        font-size: 14px;
        color: var(--el-text-color-regular);
        line-height: 1.5;
        margin-bottom: 12px;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
      }
      
      .item-steps {
        margin-bottom: 12px;
        
        .steps-header {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 13px;
          color: var(--el-text-color-regular);
          margin-bottom: 8px;
        }
        
        .steps-preview {
          .step-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            color: var(--el-text-color-regular);
            margin-bottom: 4px;
            
            .step-number {
              display: inline-flex;
              align-items: center;
              justify-content: center;
              width: 18px;
              height: 18px;
              background-color: var(--el-color-primary-light-8);
              color: var(--el-color-primary);
              border-radius: 50%;
              font-size: 12px;
              flex-shrink: 0;
            }
            
            .step-action {
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            }
          }
          
          .step-more {
            font-size: 12px;
            color: var(--el-text-color-placeholder);
            margin-top: 4px;
          }
        }
      }
      
      .item-tags {
        margin-bottom: 12px;
        
        .el-tag {
          margin-right: 8px;
          margin-bottom: 4px;
        }
        
        .more-tags {
          font-size: 12px;
          color: var(--el-text-color-placeholder);
        }
      }
      
      .item-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 12px;
        color: var(--el-text-color-secondary);
        
        .footer-left {
          display: flex;
          gap: 12px;
        }
        
        .test-level {
          font-weight: 500;
        }
      }
    }
    
    .item-actions {
      padding: 16px 12px;
      border-left: 1px solid var(--el-border-color-lighter);
      display: flex;
      align-items: flex-start;
    }
  }
  
  .empty-state {
    text-align: center;
    padding: 40px 20px;
  }
}
</style>
