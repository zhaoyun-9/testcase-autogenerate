<template>
  <div class="mindmap-page">




    <!-- 思维导图容器 -->
    <div class="mindmap-container" ref="mindmapContainer">
        <div v-if="loading" class="loading-container">
          <el-loading
            text="正在加载思维导图..."
            element-loading-text="正在加载思维导图..."
            element-loading-spinner="el-icon-loading"
            element-loading-background="rgba(0, 0, 0, 0.8)"
          />
        </div>

        <el-empty
          v-else-if="!mindmapData"
          description="暂无思维导图数据"
          :image-size="120"
        >
          <el-button type="primary" @click="generateMindmap">
            <el-icon><Plus /></el-icon>
            生成思维导图
          </el-button>
        </el-empty>

        <div v-else class="mindmap-content">
          <!-- 思维导图渲染区域 -->
          <ProductionMindMap
            :data="mindmapData"
            @node-click="handleNodeClick"
          />
        </div>
      </div>

    <!-- 侧边面板 -->
    <div v-if="selectedNode" class="side-panel">
        <el-card shadow="never">
          <template #header>
            <div class="panel-header">
              <span>节点详情</span>
              <el-button type="text" @click="closeSidePanel">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </template>
          
          <div class="node-details">
            <div class="detail-item">
              <label>标题:</label>
              <el-input
                v-model="selectedNode.title"
                @change="updateNode"
                size="small"
              />
            </div>
            
            <div class="detail-item">
              <label>类型:</label>
              <el-tag :type="getNodeTypeTag(selectedNode.type)">
                {{ getNodeTypeLabel(selectedNode.type) }}
              </el-tag>
            </div>
            
            <div v-if="selectedNode.description" class="detail-item">
              <label>描述:</label>
              <el-input
                v-model="selectedNode.description"
                type="textarea"
                :rows="3"
                @change="updateNode"
                size="small"
              />
            </div>
            
            <div v-if="selectedNode.testSteps" class="detail-item">
              <label>测试步骤:</label>
              <div class="test-steps">
                <div
                  v-for="(step, index) in selectedNode.testSteps"
                  :key="index"
                  class="step-item"
                >
                  <span class="step-number">{{ step.step }}</span>
                  <span class="step-action">{{ step.action }}</span>
                </div>
              </div>
            </div>
            
            <div v-if="selectedNode.tags" class="detail-item">
              <label>标签:</label>
              <div class="tags">
                <el-tag
                  v-for="tag in selectedNode.tags"
                  :key="tag"
                  size="small"
                  type="info"
                >
                  {{ tag }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
    </div>

    <!-- 导出对话框 -->
    <ExportDialog
      v-model="exportDialogVisible"
      :mindmap-data="mindmapData"
      @export="handleExport"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Plus,
  Close
} from '@element-plus/icons-vue'



import { mindmapApi } from '@/api/testCase'
import ProductionMindMap from '@/components/ProductionMindMap/index.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const mindmapData = ref(null)
const selectedNode = ref(null)
const mindmapContainer = ref<HTMLElement>()



// 会话ID
const sessionId = computed(() => route.params.sessionId as string)





// 加载思维导图数据
const loadMindmapData = async () => {
  try {
    loading.value = true

    // 如果有会话ID，尝试从API加载数据
    if (sessionId.value) {
      try {
        const data = await mindmapApi.getMindmapBySession(sessionId.value)
        mindmapData.value = data
        return
      } catch (error) {
        console.warn('从API加载思维导图失败，使用默认数据:', error)
      }
    }

    // 使用默认测试数据
    console.log('加载默认测试数据')
    mindmapData.value = {
      id: 'root',
      title: '测试用例思维导图',
      type: 'root',
      children: [
        {
          id: 'functional',
          title: '功能测试',
          type: 'category',
          children: [
            {
              id: 'login',
              title: '登录功能',
              type: 'module',
              children: [
                {
                  id: 'login-valid',
                  title: '有效登录',
                  type: 'testcase',
                  description: '使用有效的用户名和密码进行登录',
                  priority: 'high',
                  status: 'passed'
                },
                {
                  id: 'login-invalid',
                  title: '无效登录',
                  type: 'testcase',
                  description: '使用无效的用户名或密码进行登录',
                  priority: 'high',
                  status: 'failed'
                }
              ]
            },
            {
              id: 'user-management',
              title: '用户管理',
              type: 'module',
              children: [
                {
                  id: 'create-user',
                  title: '创建用户',
                  type: 'testcase',
                  description: '创建新用户账户',
                  priority: 'medium',
                  status: 'pending'
                },
                {
                  id: 'edit-user',
                  title: '编辑用户',
                  type: 'testcase',
                  description: '编辑现有用户信息',
                  priority: 'medium',
                  status: 'passed'
                }
              ]
            }
          ]
        },
        {
          id: 'performance',
          title: '性能测试',
          type: 'category',
          children: [
            {
              id: 'load-test',
              title: '负载测试',
              type: 'testcase',
              description: '测试系统在正常负载下的性能',
              priority: 'high',
              status: 'passed'
            },
            {
              id: 'stress-test',
              title: '压力测试',
              type: 'testcase',
              description: '测试系统在高负载下的性能',
              priority: 'medium',
              status: 'pending'
            }
          ]
        },
        {
          id: 'security',
          title: '安全测试',
          type: 'category',
          children: [
            {
              id: 'auth-test',
              title: '身份验证测试',
              type: 'testcase',
              description: '测试身份验证机制的安全性',
              priority: 'high',
              status: 'passed'
            },
            {
              id: 'sql-injection',
              title: 'SQL注入测试',
              type: 'testcase',
              description: '测试系统对SQL注入攻击的防护',
              priority: 'high',
              status: 'failed'
            }
          ]
        }
      ]
    }
  } catch (error) {
    console.error('加载思维导图失败:', error)
    ElMessage.error('加载思维导图失败')
  } finally {
    loading.value = false
    console.log('思维导图数据加载完成:', mindmapData.value)
  }
}

// 生成思维导图
const generateMindmap = async () => {
  try {
    loading.value = true
    // 这里应该调用生成思维导图的API
    ElMessage.info('正在生成思维导图，请稍候...')
    
    // 模拟生成过程
    setTimeout(() => {
      mindmapData.value = {
        id: 'root',
        title: '测试用例思维导图',
        type: 'root',
        children: [
          {
            id: 'functional',
            title: '功能测试',
            type: 'category',
            children: [
              {
                id: 'login',
                title: '用户登录',
                type: 'testcase',
                description: '测试用户登录功能',
                testSteps: [
                  { step: 1, action: '打开登录页面' },
                  { step: 2, action: '输入用户名和密码' },
                  { step: 3, action: '点击登录按钮' }
                ],
                tags: ['登录', '认证']
              }
            ]
          }
        ]
      }
      loading.value = false
      ElMessage.success('思维导图生成完成')
    }, 2000)
    
  } catch (error) {
    console.error('生成思维导图失败:', error)
    ElMessage.error('生成思维导图失败')
    loading.value = false
  }
}







// 节点操作
const handleNodeClick = (node: any) => {
  selectedNode.value = node
}



const closeSidePanel = () => {
  selectedNode.value = null
}

// 获取节点类型标签
const getNodeTypeTag = (type: string) => {
  const tagMap: Record<string, string> = {
    'root': 'primary',
    'category': 'success',
    'testcase': 'warning',
    'step': 'info'
  }
  return tagMap[type] || 'info'
}

const getNodeTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    'root': '根节点',
    'category': '分类',
    'testcase': '测试用例',
    'step': '测试步骤'
  }
  return labelMap[type] || type
}





onMounted(() => {
  console.log('思维导图页面已挂载')
  loadMindmapData()
})
</script>

<style lang="scss" scoped>
.mindmap-page {
  height: 100vh;
  width: 100vw;
  position: relative;
  overflow: hidden;
  

  


  .mindmap-container {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100%;
    height: 100%;

    .loading-container,
    .empty-container {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f5f5f5;
    }

    .mindmap-content {
      height: 100%;
      width: 100%;
    }
  }
  
  .side-panel {
    position: fixed;
    top: 80px;
    right: 20px;
    width: 300px;
    max-height: calc(100vh - 100px);
    z-index: 1000;
    
    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .node-details {
      .detail-item {
        margin-bottom: 16px;
        
        label {
          display: block;
          font-size: 14px;
          color: var(--el-text-color-regular);
          margin-bottom: 4px;
        }
        
        .test-steps {
          .step-item {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 4px;
            font-size: 13px;
            
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
              flex: 1;
            }
          }
        }
        
        .tags {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
        }
      }
    }
  }
}
</style>
