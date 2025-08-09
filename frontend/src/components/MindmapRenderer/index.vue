<template>
  <div class="mindmap-renderer" ref="containerRef">
    <div class="mindmap-canvas" ref="canvasRef"></div>
    
    <!-- 右键菜单 -->
    <div
      v-if="contextMenu.visible"
      class="context-menu"
      :style="{
        left: contextMenu.x + 'px',
        top: contextMenu.y + 'px'
      }"
      @click.stop
    >
      <div class="menu-item" @click="addChildNode">
        <el-icon><Plus /></el-icon>
        添加子节点
      </div>
      <div class="menu-item" @click="editNode">
        <el-icon><Edit /></el-icon>
        编辑节点
      </div>
      <div class="menu-item" @click="deleteNode">
        <el-icon><Delete /></el-icon>
        删除节点
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'

interface MindmapNode {
  id: string
  title: string
  type: string
  description?: string
  testSteps?: any[]
  tags?: string[]
  children?: MindmapNode[]
  x?: number
  y?: number
  width?: number
  height?: number
}

interface Props {
  data: MindmapNode | null
  viewMode: 'tree' | 'mind' | 'org'
  theme: string
  layout: 'horizontal' | 'vertical' | 'radial'
  showDetails: boolean
  zoom: number
}

interface Emits {
  (e: 'node-click', node: MindmapNode): void
  (e: 'node-edit', node: MindmapNode): void
  (e: 'structure-change', data: MindmapNode): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const containerRef = ref<HTMLElement>()
const canvasRef = ref<HTMLElement>()
const svgRef = ref<SVGElement>()

// 右键菜单状态
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  node: null as MindmapNode | null
})

// 渲染状态
const renderData = ref<MindmapNode | null>(null)
const nodeElements = ref<Map<string, HTMLElement>>(new Map())

// 主题配置
const themeConfig = {
  default: {
    nodeColor: '#409EFF',
    textColor: '#303133',
    linkColor: '#DCDFE6',
    backgroundColor: '#FFFFFF'
  },
  dark: {
    nodeColor: '#67C23A',
    textColor: '#FFFFFF',
    linkColor: '#4C4D4F',
    backgroundColor: '#1D1E1F'
  },
  simple: {
    nodeColor: '#909399',
    textColor: '#606266',
    linkColor: '#E4E7ED',
    backgroundColor: '#FAFAFA'
  },
  colorful: {
    nodeColor: '#E6A23C',
    textColor: '#303133',
    linkColor: '#F56C6C',
    backgroundColor: '#F0F9FF'
  }
}

// 监听数据变化
watch(() => props.data, (newData) => {
  if (newData) {
    renderData.value = JSON.parse(JSON.stringify(newData))
    nextTick(() => {
      renderMindmap()
    })
  }
}, { immediate: true })

// 监听配置变化
watch([
  () => props.viewMode,
  () => props.theme,
  () => props.layout,
  () => props.showDetails,
  () => props.zoom
], () => {
  nextTick(() => {
    renderMindmap()
  })
})

// 渲染思维导图
const renderMindmap = () => {
  if (!renderData.value || !canvasRef.value) return

  // 清空画布
  canvasRef.value.innerHTML = ''
  nodeElements.value.clear()

  // 创建SVG容器
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  svg.setAttribute('width', '100%')
  svg.setAttribute('height', '100%')
  svg.style.position = 'absolute'
  svg.style.top = '0'
  svg.style.left = '0'
  svg.style.zIndex = '1'
  canvasRef.value.appendChild(svg)
  svgRef.value = svg

  // 计算布局
  const layout = calculateLayout(renderData.value)
  
  // 渲染连接线
  renderConnections(svg, layout)
  
  // 渲染节点
  renderNodes(layout)
  
  // 应用缩放
  applyZoom()
}

// 计算布局
const calculateLayout = (data: MindmapNode): MindmapNode => {
  const nodeWidth = 150
  const nodeHeight = 60
  const horizontalSpacing = 200
  const verticalSpacing = 80

  const calculateNodePositions = (node: MindmapNode, x: number, y: number, level: number): void => {
    node.x = x
    node.y = y
    node.width = nodeWidth
    node.height = nodeHeight

    if (node.children && node.children.length > 0) {
      const totalHeight = (node.children.length - 1) * verticalSpacing
      const startY = y - totalHeight / 2

      node.children.forEach((child, index) => {
        const childX = x + horizontalSpacing
        const childY = startY + index * verticalSpacing
        calculateNodePositions(child, childX, childY, level + 1)
      })
    }
  }

  // 根据布局模式计算位置
  if (props.layout === 'horizontal') {
    calculateNodePositions(data, 100, 300, 0)
  } else if (props.layout === 'vertical') {
    // 垂直布局逻辑
    calculateNodePositions(data, 300, 100, 0)
  } else if (props.layout === 'radial') {
    // 径向布局逻辑
    calculateRadialLayout(data)
  }

  return data
}

// 径向布局计算
const calculateRadialLayout = (data: MindmapNode) => {
  const centerX = 400
  const centerY = 300
  const radius = 150

  data.x = centerX
  data.y = centerY

  if (data.children) {
    const angleStep = (2 * Math.PI) / data.children.length
    data.children.forEach((child, index) => {
      const angle = index * angleStep
      child.x = centerX + Math.cos(angle) * radius
      child.y = centerY + Math.sin(angle) * radius
    })
  }
}

// 渲染连接线
const renderConnections = (svg: SVGElement, data: MindmapNode) => {
  const theme = themeConfig[props.theme as keyof typeof themeConfig]
  
  const renderLines = (node: MindmapNode) => {
    if (node.children) {
      node.children.forEach(child => {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line')
        line.setAttribute('x1', (node.x! + node.width! / 2).toString())
        line.setAttribute('y1', (node.y! + node.height! / 2).toString())
        line.setAttribute('x2', (child.x! + child.width! / 2).toString())
        line.setAttribute('y2', (child.y! + child.height! / 2).toString())
        line.setAttribute('stroke', theme.linkColor)
        line.setAttribute('stroke-width', '2')
        svg.appendChild(line)
        
        renderLines(child)
      })
    }
  }

  renderLines(data)
}

// 渲染节点
const renderNodes = (data: MindmapNode) => {
  const theme = themeConfig[props.theme as keyof typeof themeConfig]
  
  const renderNode = (node: MindmapNode) => {
    const nodeElement = document.createElement('div')
    nodeElement.className = 'mindmap-node'
    nodeElement.style.position = 'absolute'
    nodeElement.style.left = node.x + 'px'
    nodeElement.style.top = node.y + 'px'
    nodeElement.style.width = node.width + 'px'
    nodeElement.style.height = node.height + 'px'
    nodeElement.style.backgroundColor = theme.nodeColor
    nodeElement.style.color = theme.textColor
    nodeElement.style.border = '2px solid ' + theme.linkColor
    nodeElement.style.borderRadius = '8px'
    nodeElement.style.display = 'flex'
    nodeElement.style.alignItems = 'center'
    nodeElement.style.justifyContent = 'center'
    nodeElement.style.cursor = 'pointer'
    nodeElement.style.zIndex = '2'
    nodeElement.style.fontSize = '14px'
    nodeElement.style.fontWeight = '500'
    nodeElement.style.textAlign = 'center'
    nodeElement.style.padding = '8px'
    nodeElement.style.boxSizing = 'border-box'
    nodeElement.style.transition = 'all 0.3s ease'

    // 节点内容
    const content = document.createElement('div')
    content.innerHTML = node.title
    nodeElement.appendChild(content)

    // 添加详情
    if (props.showDetails && node.description) {
      const details = document.createElement('div')
      details.style.fontSize = '12px'
      details.style.opacity = '0.8'
      details.style.marginTop = '4px'
      details.innerHTML = node.description.substring(0, 20) + '...'
      nodeElement.appendChild(details)
    }

    // 事件监听
    nodeElement.addEventListener('click', (e) => {
      e.stopPropagation()
      emit('node-click', node)
    })

    nodeElement.addEventListener('contextmenu', (e) => {
      e.preventDefault()
      e.stopPropagation()
      showContextMenu(e, node)
    })

    nodeElement.addEventListener('mouseenter', () => {
      nodeElement.style.transform = 'scale(1.05)'
      nodeElement.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)'
    })

    nodeElement.addEventListener('mouseleave', () => {
      nodeElement.style.transform = 'scale(1)'
      nodeElement.style.boxShadow = 'none'
    })

    canvasRef.value!.appendChild(nodeElement)
    nodeElements.value.set(node.id, nodeElement)

    // 递归渲染子节点
    if (node.children) {
      node.children.forEach(child => renderNode(child))
    }
  }

  renderNode(data)
}

// 应用缩放
const applyZoom = () => {
  if (canvasRef.value) {
    canvasRef.value.style.transform = `scale(${props.zoom})`
    canvasRef.value.style.transformOrigin = 'center center'
  }
}

// 显示右键菜单
const showContextMenu = (event: MouseEvent, node: MindmapNode) => {
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    node
  }
}

// 隐藏右键菜单
const hideContextMenu = () => {
  contextMenu.value.visible = false
  contextMenu.value.node = null
}

// 右键菜单操作
const addChildNode = () => {
  if (!contextMenu.value.node) return
  
  const newNode: MindmapNode = {
    id: Date.now().toString(),
    title: '新节点',
    type: 'testcase',
    children: []
  }
  
  if (!contextMenu.value.node.children) {
    contextMenu.value.node.children = []
  }
  
  contextMenu.value.node.children.push(newNode)
  emit('structure-change', renderData.value!)
  hideContextMenu()
  
  nextTick(() => {
    renderMindmap()
  })
}

const editNode = () => {
  if (contextMenu.value.node) {
    emit('node-edit', contextMenu.value.node)
  }
  hideContextMenu()
}

const deleteNode = () => {
  if (!contextMenu.value.node || !renderData.value) return
  
  // 递归查找并删除节点
  const deleteNodeRecursive = (parent: MindmapNode, targetId: string): boolean => {
    if (parent.children) {
      const index = parent.children.findIndex(child => child.id === targetId)
      if (index !== -1) {
        parent.children.splice(index, 1)
        return true
      }
      
      for (const child of parent.children) {
        if (deleteNodeRecursive(child, targetId)) {
          return true
        }
      }
    }
    return false
  }
  
  if (contextMenu.value.node.id !== renderData.value.id) {
    deleteNodeRecursive(renderData.value, contextMenu.value.node.id)
    emit('structure-change', renderData.value)
    hideContextMenu()
    
    nextTick(() => {
      renderMindmap()
    })
  } else {
    ElMessage.warning('不能删除根节点')
  }
}

// 点击空白区域隐藏菜单
const handleClickOutside = () => {
  hideContextMenu()
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  
  // 初始渲染
  if (props.data) {
    renderData.value = JSON.parse(JSON.stringify(props.data))
    nextTick(() => {
      renderMindmap()
    })
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style lang="scss" scoped>
.mindmap-renderer {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  
  .mindmap-canvas {
    position: relative;
    width: 100%;
    height: 100%;
    transition: transform 0.3s ease;
  }
  
  .context-menu {
    position: fixed;
    background: white;
    border: 1px solid var(--el-border-color);
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 1000;
    min-width: 120px;
    
    .menu-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      cursor: pointer;
      font-size: 14px;
      color: var(--el-text-color-primary);
      
      &:hover {
        background-color: var(--el-fill-color-light);
      }
      
      &:first-child {
        border-radius: 6px 6px 0 0;
      }
      
      &:last-child {
        border-radius: 0 0 6px 6px;
      }
    }
  }
}

:deep(.mindmap-node) {
  user-select: none;
}
</style>
