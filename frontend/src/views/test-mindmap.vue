<template>
  <div class="test-mindmap-page">
    <h1>思维导图测试页面</h1>

    <div class="controls">
      <button @click="loadTestData">加载测试数据</button>
      <button @click="loadRealData">加载真实数据</button>
      <button @click="toggleDebug">切换调试模式</button>
    </div>

    <div class="test-containers">
      <div class="test-container">
        <h3>原始MindMapViewer组件</h3>
        <MindMapViewer
          :data="currentData"
          view-mode="mind"
          theme="default"
          layout="horizontal"
          :zoom="1"
          :show-animation="true"
          @node-click="handleNodeClick"
          @zoom-change="handleZoomChange"
        />
      </div>

      <div class="test-container">
        <h3>简化SimpleMindMap组件</h3>
        <SimpleMindMap :data="currentData" />
      </div>
    </div>

    <div v-if="selectedNode" class="selected-info">
      <h3>选中节点信息:</h3>
      <pre>{{ JSON.stringify(selectedNode, null, 2) }}</pre>
    </div>

    <div class="data-info">
      <h3>当前数据:</h3>
      <pre>{{ JSON.stringify(currentData, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import MindMapViewer from '@/components/MindMapViewer/index.vue'
import SimpleMindMap from '@/components/SimpleMindMap/index.vue'
import { mindmapApi } from '@/api/testCase'

const selectedNode = ref(null)
const currentData = ref(null)

// 测试数据
const testData = {
  mind_map_data: {
    nodes: [
      {
        id: 'root',
        label: '测试用例总览',
        type: 'root',
        level: 0,
        data: {
          description: '共 3 个测试用例',
          total_count: 3
        }
      },
      {
        id: 'category1',
        label: '功能测试',
        type: 'category',
        level: 1,
        data: {
          description: '功能测试分类'
        }
      },
      {
        id: 'test1',
        label: '登录测试',
        type: 'test_case',
        level: 2,
        data: {
          priority: 'P0',
          test_level: 'SYSTEM',
          description: '测试用户登录功能',
          test_steps_count: 3
        }
      },
      {
        id: 'test2',
        label: '注册测试',
        type: 'test_case',
        level: 2,
        data: {
          priority: 'P1',
          test_level: 'SYSTEM',
          description: '测试用户注册功能',
          test_steps_count: 5
        }
      }
    ],
    edges: [
      {
        id: 'edge1',
        source: 'root',
        target: 'category1',
        type: 'default'
      },
      {
        id: 'edge2',
        source: 'category1',
        target: 'test1',
        type: 'default'
      },
      {
        id: 'edge3',
        source: 'category1',
        target: 'test2',
        type: 'default'
      }
    ]
  }
}

// 加载测试数据
const loadTestData = () => {
  currentData.value = testData
  console.log('加载测试数据:', testData)
}

// 加载真实数据
const loadRealData = async () => {
  try {
    const data = await mindmapApi.getMindmapBySession('c11a1424-b11a-4ba2-8cc5-3fa42fd33793')
    currentData.value = data
    console.log('加载真实数据:', data)
  } catch (error) {
    console.error('加载真实数据失败:', error)
  }
}

const toggleDebug = () => {
  console.log('切换调试模式')
}

const handleNodeClick = (node: any) => {
  selectedNode.value = node
  console.log('节点点击:', node)
}

const handleZoomChange = (zoom: number) => {
  console.log('缩放变化:', zoom)
}

// 初始加载测试数据
loadTestData()
</script>

<style lang="scss" scoped>
.test-mindmap-page {
  padding: 20px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  
  h1 {
    margin-bottom: 20px;
    color: #333;
  }

  .controls {
    margin-bottom: 20px;
    display: flex;
    gap: 10px;

    button {
      padding: 8px 16px;
      border: 1px solid #ddd;
      border-radius: 4px;
      background: white;
      cursor: pointer;

      &:hover {
        background: #f5f5f5;
      }
    }
  }

  .test-containers {
    display: flex;
    gap: 20px;
    margin-bottom: 20px;
  }

  .test-container {
    flex: 1;
    height: 400px;
    border: 2px solid #ddd;
    border-radius: 8px;
    overflow: hidden;

    h3 {
      margin: 0;
      padding: 10px;
      background: #f5f5f5;
      border-bottom: 1px solid #ddd;
      font-size: 14px;
      color: #666;
    }

    > div {
      height: calc(100% - 45px);
    }
  }
  
  .selected-info, .data-info {
    background: #f5f5f5;
    padding: 15px;
    border-radius: 8px;
    max-height: 200px;
    overflow-y: auto;
    margin-bottom: 20px;

    h3 {
      margin-top: 0;
      margin-bottom: 10px;
    }

    pre {
      margin: 0;
      font-size: 12px;
      background: white;
      padding: 10px;
      border-radius: 4px;
      border: 1px solid #ddd;
    }
  }
}
</style>
