<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑测试用例' : '测试用例详情'"
    width="90%"
    :close-on-click-modal="false"
    @close="handleClose"
    class="test-case-detail-dialog"
    top="5vh"
  >
    <!-- 自定义头部 -->
    <template #header>
      <div class="dialog-header">
        <div class="case-title-section">
          <h2 class="case-title">{{ formData.title || '未命名测试用例' }}</h2>
          <div class="case-meta">
            <el-tag :type="getTestTypeTagType(formData.testType)" size="small">
              {{ getTestTypeLabel(formData.testType) }}
            </el-tag>
            <el-tag :type="getPriorityTagType(formData.priority)" size="small">
              {{ formData.priority }}
            </el-tag>
            <el-tag :type="getStatusTagType(formData.status)" size="small">
              {{ getStatusLabel(formData.status) }}
            </el-tag>
          </div>
        </div>
        <div class="case-actions">
          <el-button v-if="!isEdit" type="primary" @click="handleEdit">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
        </div>
      </div>
    </template>
    <!-- 主要内容区域 -->
    <div class="dialog-content">
      <el-row :gutter="24">
        <!-- 左侧主要信息 -->
        <el-col :span="16">
          <div class="main-content">
            <!-- 基本信息卡片 -->
            <el-card class="info-card" shadow="never">
              <template #header>
                <div class="card-header">
                  <el-icon><InfoFilled /></el-icon>
                  <span>基本信息</span>
                </div>
              </template>

              <el-form
                ref="formRef"
                :model="formData"
                :rules="formRules"
                label-width="100px"
                class="test-case-form"
              >
                <el-form-item label="标题" prop="title">
                  <el-input
                    v-model="formData.title"
                    placeholder="请输入测试用例标题"
                    :readonly="!isEdit"
                  />
                </el-form-item>

                <el-form-item label="描述" prop="description">
                  <el-input
                    v-model="formData.description"
                    type="textarea"
                    :rows="3"
                    placeholder="请输入测试用例描述"
                    :readonly="!isEdit"
                  />
                </el-form-item>

                <el-form-item label="前置条件">
                  <el-input
                    v-model="formData.preconditions"
                    type="textarea"
                    :rows="2"
                    placeholder="请输入前置条件"
                    :readonly="!isEdit"
                  />
                </el-form-item>
              </el-form>
            </el-card>

            <!-- 测试步骤卡片 -->
            <el-card class="steps-card" shadow="never">
              <template #header>
                <div class="card-header">
                  <el-icon><List /></el-icon>
                  <span>测试步骤</span>
                  <div class="steps-count">
                    共 {{ formData.testSteps?.length || 0 }} 个步骤
                  </div>
                </div>
              </template>

              <div class="test-steps-container">
                <div
                  v-for="(step, index) in formData.testSteps"
                  :key="index"
                  class="test-step-item"
                >
                  <div class="step-header">
                    <div class="step-number">{{ step.step }}</div>
                    <el-button
                      v-if="isEdit"
                      type="text"
                      size="small"
                      @click="removeStep(index)"
                      class="delete-btn"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>

                  <div class="step-content">
                    <div class="step-field">
                      <div class="field-label">
                        <el-icon><Operation /></el-icon>
                        操作步骤
                      </div>
                      <div v-if="!isEdit" class="field-content">
                        {{ step.action || '无' }}
                      </div>
                      <el-input
                        v-else
                        v-model="step.action"
                        type="textarea"
                        :rows="2"
                        placeholder="请输入具体的操作步骤"
                      />
                    </div>

                    <div class="step-field">
                      <div class="field-label">
                        <el-icon><Check /></el-icon>
                        预期结果
                      </div>
                      <div v-if="!isEdit" class="field-content">
                        {{ step.expectedResult || '无' }}
                      </div>
                      <el-input
                        v-else
                        v-model="step.expectedResult"
                        type="textarea"
                        :rows="2"
                        placeholder="请输入该步骤的预期结果"
                      />
                    </div>

                    <div v-if="step.data || isEdit" class="step-field">
                      <div class="field-label">
                        <el-icon><Document /></el-icon>
                        测试数据
                      </div>
                      <div v-if="!isEdit" class="field-content">
                        {{ step.data || '无' }}
                      </div>
                      <el-input
                        v-else
                        v-model="step.data"
                        placeholder="测试数据（可选）"
                      />
                    </div>
                  </div>
                </div>

                <div v-if="!formData.testSteps || formData.testSteps.length === 0" class="empty-steps">
                  <el-empty description="暂无测试步骤" :image-size="80" />
                </div>

                <el-button
                  v-if="isEdit"
                  type="primary"
                  plain
                  class="add-step-btn"
                  @click="addStep"
                >
                  <el-icon><Plus /></el-icon>
                  添加测试步骤
                </el-button>
              </div>
            </el-card>

            <!-- 最终期望结果卡片 -->
            <el-card class="result-card" shadow="never">
              <template #header>
                <div class="card-header">
                  <el-icon><SuccessFilled /></el-icon>
                  <span>最终期望结果</span>
                </div>
              </template>

              <div v-if="!isEdit" class="result-content">
                {{ formData.expectedResults || '无最终期望结果' }}
              </div>
              <el-input
                v-else
                v-model="formData.expectedResults"
                type="textarea"
                :rows="4"
                placeholder="请输入测试用例的最终期望结果"
              />
            </el-card>
          </div>
        </el-col>

        <!-- 右侧信息面板 -->
        <el-col :span="8">
          <div class="side-panel">
            <!-- 属性信息卡片 -->
            <el-card class="properties-card" shadow="never">
              <template #header>
                <div class="card-header">
                  <el-icon><Setting /></el-icon>
                  <span>属性信息</span>
                </div>
              </template>

              <div class="properties-content">
                <div class="property-item">
                  <label>测试类型</label>
                  <div v-if="!isEdit" class="property-value">
                    <el-tag :type="getTestTypeTagType(formData.testType)" size="small">
                      {{ getTestTypeLabel(formData.testType) }}
                    </el-tag>
                  </div>
                  <el-select
                    v-else
                    v-model="formData.testType"
                    placeholder="选择测试类型"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="option in testTypeOptions"
                      :key="option.value"
                      :label="option.label"
                      :value="option.value"
                    />
                  </el-select>
                </div>

                <div class="property-item">
                  <label>测试级别</label>
                  <div v-if="!isEdit" class="property-value">
                    {{ getTestLevelLabel(formData.testLevel) }}
                  </div>
                  <el-select
                    v-else
                    v-model="formData.testLevel"
                    placeholder="选择测试级别"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="option in testLevelOptions"
                      :key="option.value"
                      :label="option.label"
                      :value="option.value"
                    />
                  </el-select>
                </div>

                <div class="property-item">
                  <label>优先级</label>
                  <div v-if="!isEdit" class="property-value">
                    <el-tag :type="getPriorityTagType(formData.priority)" size="small">
                      {{ formData.priority }}
                    </el-tag>
                  </div>
                  <el-select
                    v-else
                    v-model="formData.priority"
                    placeholder="选择优先级"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="option in priorityOptions"
                      :key="option.value"
                      :label="option.label"
                      :value="option.value"
                    />
                  </el-select>
                </div>

                <div class="property-item">
                  <label>状态</label>
                  <div v-if="!isEdit" class="property-value">
                    <el-tag :type="getStatusTagType(formData.status)" size="small">
                      {{ getStatusLabel(formData.status) }}
                    </el-tag>
                  </div>
                  <el-select
                    v-else
                    v-model="formData.status"
                    placeholder="选择状态"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="option in statusOptions"
                      :key="option.value"
                      :label="option.label"
                      :value="option.value"
                    />
                  </el-select>
                </div>

                <div class="property-item">
                  <label>标签</label>
                  <div v-if="!isEdit" class="property-value">
                    <el-tag
                      v-for="tag in formData.tags"
                      :key="tag"
                      size="small"
                      style="margin-right: 4px; margin-bottom: 4px;"
                    >
                      {{ tag }}
                    </el-tag>
                    <span v-if="!formData.tags || formData.tags.length === 0" class="no-data">无标签</span>
                  </div>
                  <el-select
                    v-else
                    v-model="formData.tags"
                    multiple
                    filterable
                    allow-create
                    placeholder="选择或输入标签"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="tag in commonTags"
                      :key="tag"
                      :label="tag"
                      :value="tag"
                    />
                  </el-select>
                </div>
              </div>
            </el-card>
          </div>
        </el-col>
      </el-row>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button v-if="!isEdit" type="primary" @click="toggleEdit">
          编辑
        </el-button>
        <el-button v-if="isEdit" type="primary" @click="handleSave">
          保存
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { TestCase, TestStep } from '@/types/testCase'
import {
  TEST_TYPE_OPTIONS,
  TEST_LEVEL_OPTIONS,
  PRIORITY_OPTIONS,
  STATUS_OPTIONS
} from '@/types/testCase'

interface Props {
  modelValue: boolean
  testCase?: TestCase | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'save', testCase: TestCase): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref()
const isEdit = ref(false)

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 表单数据
const formData = ref<TestCase>({
  id: '',
  title: '',
  description: '',
  testType: 'functional',
  testLevel: 'system',
  priority: 'P2',
  status: 'draft',
  preconditions: '',
  testSteps: [],
  expectedResult: '',
  tags: [],
  category: '',
  sessionId: '',
  createdAt: '',
  updatedAt: ''
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

// 表单验证规则
const formRules = {
  title: [
    { required: true, message: '请输入测试用例标题', trigger: 'blur' }
  ],
  testType: [
    { required: true, message: '请选择测试类型', trigger: 'change' }
  ],
  testLevel: [
    { required: true, message: '请选择测试级别', trigger: 'change' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

// 监听测试用例变化
watch(() => props.testCase, (testCase) => {
  if (testCase) {
    // 确保测试步骤数据格式正确
    const normalizedTestCase = {
      ...testCase,
      testSteps: (testCase.testSteps || []).map((step: any) => ({
        step: step.step || step.step_number,
        action: step.action,
        expectedResult: step.expectedResult || step.expected,
        data: step.data
      }))
    }
    formData.value = normalizedTestCase
    isEdit.value = false
  } else {
    // 新建模式
    formData.value = {
      id: '',
      title: '',
      description: '',
      testType: 'functional',
      testLevel: 'system',
      priority: 'P2',
      status: 'draft',
      preconditions: '',
      testSteps: [],
      expectedResults: '',
      tags: [],
      category: '',
      sessionId: '',
      createdAt: '',
      updatedAt: ''
    }
    isEdit.value = true
  }
}, { immediate: true })

// 添加测试步骤
const addStep = () => {
  const newStep: TestStep = {
    step: formData.value.testSteps.length + 1,
    action: '',
    expectedResult: ''
  }
  formData.value.testSteps.push(newStep)
}

// 删除测试步骤
const removeStep = (index: number) => {
  formData.value.testSteps.splice(index, 1)
  // 重新编号
  formData.value.testSteps.forEach((step, idx) => {
    step.step = idx + 1
  })
}

// 切换编辑模式
const toggleEdit = () => {
  isEdit.value = !isEdit.value
}

// 保存
const handleSave = async () => {
  try {
    await formRef.value?.validate()
    emit('save', formData.value)
  } catch (error) {
    ElMessage.error('请检查表单填写是否正确')
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  isEdit.value = false
}

// 辅助函数
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

const getTestTypeLabel = (testType: string) => {
  const option = testTypeOptions.find(opt => opt.value === testType)
  return option?.label || testType
}

const getTestLevelLabel = (testLevel: string) => {
  const option = testLevelOptions.find(opt => opt.value === testLevel)
  return option?.label || testLevel
}

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

const getStatusTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    'draft': 'info',
    'review': 'warning',
    'approved': 'success',
    'deprecated': 'danger'
  }
  return typeMap[status] || ''
}

const getStatusLabel = (status: string) => {
  const option = statusOptions.find(opt => opt.value === status)
  return option?.label || status
}
</script>

<style lang="scss" scoped>
.test-case-detail-dialog {
  :deep(.el-dialog__header) {
    padding: 0;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }

  :deep(.el-dialog__body) {
    padding: 0;
  }

  .dialog-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;

    .case-title-section {
      flex: 1;

      .case-title {
        margin: 0 0 8px 0;
        font-size: 20px;
        font-weight: 600;
      }

      .case-meta {
        display: flex;
        gap: 8px;

        .el-tag {
          background: rgba(255, 255, 255, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.3);
          color: white;
        }
      }
    }

    .case-actions {
      .el-button {
        background: rgba(255, 255, 255, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: white;

        &:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      }
    }
  }

  .dialog-content {
    padding: 24px;
    background: #f8fafc;
    min-height: 60vh;

    .main-content {
      .info-card, .steps-card {
        margin-bottom: 20px;
        border: none;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

        :deep(.el-card__header) {
          background: white;
          border-bottom: 1px solid var(--el-border-color-lighter);

          .card-header {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            color: var(--el-text-color-primary);

            .steps-count {
              margin-left: auto;
              font-size: 12px;
              color: var(--el-text-color-secondary);
              background: var(--el-fill-color-light);
              padding: 2px 8px;
              border-radius: 12px;
            }
          }
        }

        :deep(.el-card__body) {
          padding: 20px;
        }
      }
    }

    .side-panel {
      .properties-card {
        border: none;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

        .properties-content {
          .property-item {
            margin-bottom: 16px;

            label {
              display: block;
              font-size: 13px;
              font-weight: 500;
              color: var(--el-text-color-regular);
              margin-bottom: 6px;
            }

            .property-value {
              min-height: 32px;
              display: flex;
              align-items: center;
              flex-wrap: wrap;

              .no-data {
                color: var(--el-text-color-placeholder);
                font-style: italic;
              }
            }
          }

          .property-item:last-child {
            margin-bottom: 0;
          }
        }
      }
    }

    .result-card {
      margin-bottom: 20px;
      border: none;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

      .result-content {
        background: var(--el-color-success-light-9);
        border: 1px solid var(--el-color-success-light-7);
        border-radius: 6px;
        padding: 16px;
        line-height: 1.6;
        color: var(--el-text-color-primary);
        white-space: pre-wrap;
        min-height: 60px;

        &:empty::before {
          content: '无最终期望结果';
          color: var(--el-text-color-placeholder);
          font-style: italic;
        }
      }
    }
  }
}

.test-case-form {
  .test-steps-container {
    .test-step-item {
      background: white;
      border: 1px solid var(--el-border-color-light);
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 16px;
      transition: all 0.3s ease;

      &:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }

      .step-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;

        .step-number {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 6px 12px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 600;
          min-width: 40px;
          text-align: center;
        }

        .delete-btn {
          color: var(--el-color-danger);

          &:hover {
            background: var(--el-color-danger-light-9);
          }
        }
      }

      .step-content {
        .step-field {
          margin-bottom: 16px;

          .field-label {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            font-weight: 500;
            color: var(--el-text-color-primary);
            margin-bottom: 8px;
          }

          .field-content {
            background: var(--el-fill-color-lighter);
            padding: 12px;
            border-radius: 6px;
            min-height: 40px;
            line-height: 1.5;
            color: var(--el-text-color-primary);
            white-space: pre-wrap;
          }
        }

        .step-field:last-child {
          margin-bottom: 0;
        }
      }
    }

    .empty-steps {
      text-align: center;
      padding: 40px 0;
    }

    .add-step-btn {
      width: 100%;
      height: 48px;
      border: 2px dashed var(--el-color-primary);
      color: var(--el-color-primary);
      background: var(--el-color-primary-light-9);

      &:hover {
        background: var(--el-color-primary-light-8);
      }
    }
  }
}

.dialog-footer {
  padding: 16px 24px;
  background: white;
  border-top: 1px solid var(--el-border-color-lighter);
  text-align: right;

  .el-button {
    margin-left: 12px;
  }
}
</style>
