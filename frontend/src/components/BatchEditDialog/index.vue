<template>
  <el-dialog
    v-model="visible"
    title="批量编辑测试用例"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="batch-edit-content">
      <el-alert
        :title="`将对选中的 ${selectedIds.length} 个测试用例进行批量编辑`"
        type="info"
        :closable="false"
        show-icon
        class="info-alert"
      />

      <el-form
        ref="formRef"
        :model="formData"
        label-width="120px"
        class="batch-form"
      >
        <el-form-item label="测试类型">
          <el-checkbox v-model="updateFields.testType" class="field-checkbox">
            更新测试类型
          </el-checkbox>
          <el-select
            v-model="formData.testType"
            placeholder="选择测试类型"
            :disabled="!updateFields.testType"
            style="width: 100%"
          >
            <el-option
              v-for="option in testTypeOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="测试级别">
          <el-checkbox v-model="updateFields.testLevel" class="field-checkbox">
            更新测试级别
          </el-checkbox>
          <el-select
            v-model="formData.testLevel"
            placeholder="选择测试级别"
            :disabled="!updateFields.testLevel"
            style="width: 100%"
          >
            <el-option
              v-for="option in testLevelOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="优先级">
          <el-checkbox v-model="updateFields.priority" class="field-checkbox">
            更新优先级
          </el-checkbox>
          <el-select
            v-model="formData.priority"
            placeholder="选择优先级"
            :disabled="!updateFields.priority"
            style="width: 100%"
          >
            <el-option
              v-for="option in priorityOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-checkbox v-model="updateFields.status" class="field-checkbox">
            更新状态
          </el-checkbox>
          <el-select
            v-model="formData.status"
            placeholder="选择状态"
            :disabled="!updateFields.status"
            style="width: 100%"
          >
            <el-option
              v-for="option in statusOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="标签">
          <el-checkbox v-model="updateFields.tags" class="field-checkbox">
            更新标签
          </el-checkbox>
          <div class="tags-update-options">
            <el-radio-group
              v-model="tagsUpdateMode"
              :disabled="!updateFields.tags"
              class="tags-mode"
            >
              <el-radio value="replace">替换标签</el-radio>
              <el-radio value="add">添加标签</el-radio>
              <el-radio value="remove">移除标签</el-radio>
            </el-radio-group>
            
            <el-select
              v-model="formData.tags"
              multiple
              filterable
              allow-create
              placeholder="选择或输入标签"
              :disabled="!updateFields.tags"
              style="width: 100%; margin-top: 8px"
            >
              <el-option
                v-for="tag in commonTags"
                :key="tag"
                :label="tag"
                :value="tag"
              />
            </el-select>
          </div>
        </el-form-item>

        <el-form-item label="分类">
          <el-checkbox v-model="updateFields.category" class="field-checkbox">
            更新分类
          </el-checkbox>
          <el-input
            v-model="formData.category"
            placeholder="请输入分类"
            :disabled="!updateFields.category"
          />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSave" :disabled="!hasUpdates">
          保存更改
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  TEST_TYPE_OPTIONS,
  TEST_LEVEL_OPTIONS,
  PRIORITY_OPTIONS,
  STATUS_OPTIONS
} from '@/types/testCase'

interface Props {
  modelValue: boolean
  selectedIds: string[]
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'save', updates: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref()
const tagsUpdateMode = ref('replace')

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 更新字段标记
const updateFields = reactive({
  testType: false,
  testLevel: false,
  priority: false,
  status: false,
  tags: false,
  category: false
})

// 表单数据
const formData = reactive({
  testType: 'functional',
  testLevel: 'system',
  priority: 'P2',
  status: 'draft',
  tags: [] as string[],
  category: ''
})

// 选项数据
const testTypeOptions = TEST_TYPE_OPTIONS
const testLevelOptions = TEST_LEVEL_OPTIONS
const priorityOptions = PRIORITY_OPTIONS
const statusOptions = STATUS_OPTIONS

const commonTags = [
  '功能测试', '接口测试', '性能测试', '安全测试',
  '兼容性测试', '易用性测试', '回归测试', '冒烟测试'
]

// 是否有更新
const hasUpdates = computed(() => {
  return Object.values(updateFields).some(value => value)
})

// 监听对话框打开
watch(visible, (newVisible) => {
  if (newVisible) {
    // 重置表单
    Object.keys(updateFields).forEach(key => {
      updateFields[key as keyof typeof updateFields] = false
    })
    
    Object.assign(formData, {
      testType: 'functional',
      testLevel: 'system',
      priority: 'P2',
      status: 'draft',
      tags: [],
      category: ''
    })
    
    tagsUpdateMode.value = 'replace'
  }
})

// 保存
const handleSave = () => {
  if (!hasUpdates.value) {
    ElMessage.warning('请至少选择一个要更新的字段')
    return
  }

  const updates: any = {}
  
  // 只包含选中要更新的字段
  Object.keys(updateFields).forEach(key => {
    if (updateFields[key as keyof typeof updateFields]) {
      if (key === 'tags') {
        updates[key] = {
          mode: tagsUpdateMode.value,
          values: formData.tags
        }
      } else {
        updates[key] = formData[key as keyof typeof formData]
      }
    }
  })

  emit('save', updates)
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
}
</script>

<style lang="scss" scoped>
.batch-edit-content {
  .info-alert {
    margin-bottom: 20px;
  }
  
  .batch-form {
    .field-checkbox {
      margin-bottom: 8px;
    }
    
    .tags-update-options {
      width: 100%;
      
      .tags-mode {
        display: flex;
        gap: 16px;
        margin-bottom: 8px;
      }
    }
  }
}

.dialog-footer {
  text-align: right;
  
  .el-button {
    margin-left: 12px;
  }
}
</style>
