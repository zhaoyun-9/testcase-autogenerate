<template>
  <div class="test-case-edit">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" :icon="ArrowLeft">返回</el-button>
        <h1>{{ isCreate ? '创建测试用例' : '编辑测试用例' }}</h1>
      </div>
      <div class="header-right">
        <el-button @click="handleSave" type="primary" :loading="saving">
          保存
        </el-button>
        <el-button @click="handleCancel">取消</el-button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <!-- 编辑表单 -->
    <div v-else class="edit-form-container">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
        class="edit-form"
      >
        <!-- 基本信息 -->
        <el-card class="form-card">
          <template #header>
            <div class="card-header">
              <span>基本信息</span>
            </div>
          </template>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="标题" prop="title">
                <el-input
                  v-model="formData.title"
                  placeholder="请输入测试用例标题"
                  maxlength="200"
                  show-word-limit
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="测试类型" prop="testType">
                <el-select
                  v-model="formData.testType"
                  placeholder="请选择测试类型"
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
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="测试级别" prop="testLevel">
                <el-select
                  v-model="formData.testLevel"
                  placeholder="请选择测试级别"
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
            </el-col>
            <el-col :span="12">
              <el-form-item label="优先级" prop="priority">
                <el-select
                  v-model="formData.priority"
                  placeholder="请选择优先级"
                  style="width: 100%"
                >
                  <el-option label="P0 - 紧急" value="P0" />
                  <el-option label="P1 - 高" value="P1" />
                  <el-option label="P2 - 中" value="P2" />
                  <el-option label="P3 - 低" value="P3" />
                  <el-option label="P4 - 最低" value="P4" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="描述">
            <el-input
              v-model="formData.description"
              type="textarea"
              :rows="3"
              placeholder="请输入测试用例描述"
              maxlength="1000"
              show-word-limit
            />
          </el-form-item>
        </el-card>

        <!-- 前置条件 -->
        <el-card class="form-card">
          <template #header>
            <div class="card-header">
              <span>前置条件</span>
            </div>
          </template>
          <el-form-item>
            <el-input
              v-model="formData.preconditions"
              type="textarea"
              :rows="3"
              placeholder="请输入前置条件"
              maxlength="1000"
              show-word-limit
            />
          </el-form-item>
        </el-card>

        <!-- 测试步骤 -->
        <el-card class="form-card">
          <template #header>
            <div class="card-header">
              <span>测试步骤</span>
              <el-button type="primary" size="small" @click="addStep">
                添加步骤
              </el-button>
            </div>
          </template>

          <div class="test-steps">
            <div
              v-for="(step, index) in formData.testSteps"
              :key="index"
              class="step-item"
            >
              <div class="step-header">
                <span class="step-number">步骤 {{ step.step }}</span>
                <el-button
                  type="danger"
                  size="small"
                  text
                  @click="removeStep(index)"
                >
                  删除
                </el-button>
              </div>
              
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item
                    :prop="`testSteps.${index}.action`"
                    :rules="{ required: true, message: '请输入操作步骤' }"
                    label="操作步骤"
                  >
                    <el-input
                      v-model="step.action"
                      placeholder="请输入操作步骤"
                      maxlength="500"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="预期结果">
                    <el-input
                      v-model="step.expectedResult"
                      placeholder="请输入预期结果"
                      maxlength="500"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-form-item label="测试数据">
                <el-input
                  v-model="step.data"
                  placeholder="请输入测试数据（可选）"
                  maxlength="500"
                />
              </el-form-item>
            </div>

            <div v-if="formData.testSteps.length === 0" class="empty-steps">
              <el-empty description="暂无测试步骤" :image-size="80">
                <el-button type="primary" @click="addStep">添加第一个步骤</el-button>
              </el-empty>
            </div>
          </div>
        </el-card>

        <!-- 预期结果 -->
        <el-card class="form-card">
          <template #header>
            <div class="card-header">
              <span>预期结果</span>
            </div>
          </template>
          <el-form-item>
            <el-input
              v-model="formData.expectedResults"
              type="textarea"
              :rows="3"
              placeholder="请输入整体预期结果"
              maxlength="1000"
              show-word-limit
            />
          </el-form-item>
        </el-card>

        <!-- 标签 -->
        <el-card class="form-card">
          <template #header>
            <div class="card-header">
              <span>标签</span>
            </div>
          </template>
          <el-form-item>
            <el-select
              v-model="formData.tags"
              multiple
              filterable
              allow-create
              placeholder="请选择或输入标签"
              style="width: 100%"
            >
              <el-option
                v-for="tag in availableTags"
                :key="tag"
                :label="tag"
                :value="tag"
              />
            </el-select>
          </el-form-item>
        </el-card>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { testCaseManagementApi } from '@/api'
import type { TestCase, TestStep } from '@/types/testCase'
import { 
  TEST_TYPE_OPTIONS, 
  TEST_LEVEL_OPTIONS 
} from '@/types/testCase'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const formRef = ref()

// 计算属性
const testCaseId = computed(() => route.params.id as string)
const isCreate = computed(() => !testCaseId.value || testCaseId.value === 'new')

// 表单数据
const formData = ref<TestCase & { projectId?: string }>({
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
  projectId: 'default-project-001',
  createdAt: '',
  updatedAt: ''
})

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
  ]
}

// 选项数据
const testTypeOptions = TEST_TYPE_OPTIONS
const testLevelOptions = TEST_LEVEL_OPTIONS
const availableTags = ref<string[]>([])

// 生命周期
onMounted(() => {
  if (!isCreate.value) {
    loadTestCase()
  }
  loadAvailableTags()
})

// 方法
const loadTestCase = async () => {
  loading.value = true
  try {
    const response = await testCaseManagementApi.getTestCase(testCaseId.value)
    
    // 转换数据格式
    formData.value = {
      ...response,
      testType: response.test_type,
      testLevel: response.test_level,
      testSteps: (response.test_steps || []).map((step: any) => ({
        step: step.step_number || step.step,
        action: step.action,
        expectedResult: step.expected || step.expectedResult,
        data: step.data
      })),
      expectedResults: response.expected_results,
      createdAt: response.created_at,
      updatedAt: response.updated_at,
      sessionId: response.session_id
    }
  } catch (error) {
    console.error('加载测试用例失败:', error)
    ElMessage.error('加载测试用例失败')
  } finally {
    loading.value = false
  }
}

const loadAvailableTags = async () => {
  // TODO: 从API加载可用标签
  availableTags.value = ['功能测试', '性能测试', '安全测试', '兼容性测试', '用户体验']
}

const addStep = () => {
  const newStep: TestStep = {
    step: formData.value.testSteps.length + 1,
    action: '',
    expectedResult: '',
    data: ''
  }
  formData.value.testSteps.push(newStep)
}

const removeStep = (index: number) => {
  formData.value.testSteps.splice(index, 1)
  // 重新编号
  formData.value.testSteps.forEach((step, idx) => {
    step.step = idx + 1
  })
}

const handleSave = async () => {
  try {
    await formRef.value?.validate()
    
    saving.value = true
    
    // 转换数据格式为后端格式
    const saveData = {
      ...formData.value,
      test_type: formData.value.testType,
      test_level: formData.value.testLevel,
      test_steps: formData.value.testSteps.map(step => ({
        step_number: step.step,
        action: step.action,
        expected: step.expectedResult,
        data: step.data
      })),
      expected_results: formData.value.expectedResults,
      session_id: formData.value.sessionId,
      project_id: formData.value.projectId || 'default-project-001' // 添加默认项目ID
    }
    
    if (isCreate.value) {
      await testCaseManagementApi.createTestCase(saveData)
      ElMessage.success('创建成功')
    } else {
      await testCaseManagementApi.updateTestCase(testCaseId.value, saveData)
      ElMessage.success('更新成功')
    }
    
    router.back()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleCancel = async () => {
  try {
    await ElMessageBox.confirm('确定要取消编辑吗？未保存的更改将丢失。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    router.back()
  } catch {
    // 用户取消
  }
}

const goBack = () => {
  handleCancel()
}
</script>

<style scoped>
.test-case-edit {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.header-right {
  display: flex;
  gap: 12px;
}

.loading-container {
  padding: 20px;
}

.edit-form-container {
  max-width: 1200px;
}

.form-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}

.test-steps {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.step-item {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.step-number {
  font-weight: 600;
  color: #409eff;
}

.empty-steps {
  padding: 40px;
  text-align: center;
}
</style>
