<template>
  <div class="mindmap-detail">
    <div class="detail-header">
      <div class="header-left">
        <el-button @click="goBack" text>
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
        <div class="title-section">
          <h1>{{ mindmapTitle }}</h1>
          <span class="last-saved">{{ lastSavedText }}</span>
        </div>
      </div>
      
      <div class="header-right">
        <el-button @click="saveMindmap" type="primary" :loading="saving">
          <el-icon><Document /></el-icon>
          保存
        </el-button>
      </div>
    </div>

    <div class="mindmap-container">
      <EnhancedMindMap 
        v-if="mindmapData"
        :data="mindmapData" 
        :show-animation="true"
        @node-click="handleNodeClick"
        @node-update="handleNodeUpdate"
        @data-change="handleDataChange"
      />
      
      <div v-else class="loading-state">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <span>加载中...</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Document, Loading } from '@element-plus/icons-vue'
import EnhancedMindMap from '@/components/EnhancedMindMap/index.vue'

const router = useRouter()
const route = useRoute()

// 响应式数据
const mindmapData = ref<any>(null)
const saving = ref(false)
const lastSaved = ref<Date>(new Date())

// 计算属性
const mindmapTitle = computed(() => {
  return mindmapData.value?.mind_map_data?.label || '思维导图'
})

const lastSavedText = computed(() => {
  const now = new Date()
  const diff = now.getTime() - lastSaved.value.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  
  if (minutes < 1) {
    return '刚刚保存'
  } else if (minutes < 60) {
    return `${minutes}分钟前保存`
  } else {
    const hours = Math.floor(minutes / 60)
    return `${hours}小时前保存`
  }
})

// 方法
const goBack = () => {
  router.push({ name: 'MindmapList' })
}

const loadMindmapData = () => {
  const mindmapId = route.params.id

  // 从 sessionStorage 中读取数据
  const storedData = sessionStorage.getItem(`mindmap_${mindmapId}`)
  if (storedData) {
    try {
      mindmapData.value = JSON.parse(storedData)
    } catch (error) {
      console.error('解析思维导图数据失败:', error)
      loadFromAPI(mindmapId)
    }
  } else {
    // 如果没有存储数据，从API加载或创建默认数据
    loadFromAPI(mindmapId)
  }
}

const loadFromAPI = (id: any) => {
  // 模拟API加载
  console.log('从API加载思维导图数据，ID:', id)
  setTimeout(() => {
    mindmapData.value = {
      mind_map_data: {
        id: 'center',
        label: `思维导图 ${id}`,
        type: 'center',
        level: 0,
        children: [
          {
            id: 'sample1',
            label: '示例分支1',
            type: 'branch',
            level: 1,
            side: 'left',
            children: []
          },
          {
            id: 'sample2',
            label: '示例分支2',
            type: 'branch',
            level: 1,
            side: 'right',
            children: []
          }
        ]
      }
    }
  }, 500)
}

const saveMindmap = async () => {
  if (!mindmapData.value) return
  
  saving.value = true
  
  try {
    // 模拟保存API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    lastSaved.value = new Date()
    ElMessage.success('思维导图已保存')
  } catch (error) {
    ElMessage.error('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

const handleNodeClick = (node: any) => {
  console.log('节点被点击:', node)
}

const handleNodeUpdate = (node: any) => {
  console.log('节点已更新:', node)
  // 标记为有未保存的更改
}

const handleDataChange = (data: any) => {
  console.log('数据已变更:', data)
  mindmapData.value = data
  // 可以在这里实现自动保存
}

// 生命周期
onMounted(() => {
  loadMindmapData()
})
</script>

<style lang="scss" scoped>
.mindmap-detail {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;

  .detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    background: white;
    border-bottom: 1px solid #e5e7eb;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);

    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;

      .title-section {
        h1 {
          margin: 0;
          font-size: 20px;
          font-weight: 600;
          color: #1f2937;
          line-height: 1.2;
        }

        .last-saved {
          font-size: 12px;
          color: #6b7280;
        }
      }
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }

  .mindmap-container {
    flex: 1;
    position: relative;
    overflow: hidden;

    .loading-state {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 12px;
      color: #6b7280;

      .loading-icon {
        font-size: 32px;
        animation: spin 1s linear infinite;
      }

      span {
        font-size: 14px;
      }
    }
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .mindmap-detail {
    .detail-header {
      padding: 12px 16px;
      flex-direction: column;
      gap: 12px;
      align-items: stretch;

      .header-left,
      .header-right {
        justify-content: center;
      }
    }
  }
}
</style>
