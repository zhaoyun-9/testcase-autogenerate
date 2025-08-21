<template>
  <div class="mindmap-viewer" ref="containerRef">
    <!-- 调试信息 -->
    <div v-if="showDebug" class="debug-info">
      <p>数据状态: {{ dataStatus }}</p>
      <p>节点数量: {{ nodeCount }}</p>
      <p>连接数量: {{ linkCount }}</p>
    </div>

    <svg ref="svgRef" class="mindmap-svg">
      <defs>
        <!-- 定义渐变和滤镜 -->
        <linearGradient id="nodeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
        </linearGradient>

        <linearGradient id="rootGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#ff6b6b;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#ee5a24;stop-opacity:1" />
        </linearGradient>

        <linearGradient id="categoryGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#4ecdc4;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#44a08d;stop-opacity:1" />
        </linearGradient>

        <linearGradient id="testcaseGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#feca57;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#ff9ff3;stop-opacity:1" />
        </linearGradient>

        <!-- 阴影滤镜 -->
        <filter id="dropshadow" x="-50%" y="-50%" width="200%" height="200%">
          <feDropShadow dx="2" dy="2" stdDeviation="3" flood-color="#000000" flood-opacity="0.3"/>
        </filter>

        <!-- 发光效果 -->
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>

      <!-- 连接线组 -->
      <g class="links-group"></g>

      <!-- 节点组 -->
      <g class="nodes-group"></g>
    </svg>
    
    <!-- 工具栏 -->
    <div class="mindmap-toolbar">
      <div class="toolbar-group">
        <button @click="zoomIn" class="toolbar-btn" title="放大">
          <el-icon><ZoomIn /></el-icon>
        </button>
        <button @click="zoomOut" class="toolbar-btn" title="缩小">
          <el-icon><ZoomOut /></el-icon>
        </button>
        <button @click="resetZoom" class="toolbar-btn" title="重置缩放">
          <el-icon><Refresh /></el-icon>
        </button>
        <button @click="centerView" class="toolbar-btn" title="居中">
          <el-icon><Aim /></el-icon>
        </button>
      </div>
      
      <div class="toolbar-group">
        <button @click="toggleAnimation" class="toolbar-btn" :class="{ active: animationEnabled }" title="动画">
          <el-icon><VideoPlay /></el-icon>
        </button>
        <button @click="exportImage" class="toolbar-btn" title="导出图片">
          <el-icon><Download /></el-icon>
        </button>
      </div>
    </div>
    
    <!-- 节点详情面板 -->
    <div v-if="selectedNode" class="node-detail-panel" :style="panelStyle">
      <div class="panel-header">
        <h4>{{ selectedNode.label }}</h4>
        <button @click="closePanel" class="close-btn">
          <el-icon><Close /></el-icon>
        </button>
      </div>
      
      <div class="panel-content">
        <div class="detail-item">
          <label>类型:</label>
          <el-tag :type="getNodeTypeColor(selectedNode.type)">
            {{ getNodeTypeLabel(selectedNode.type) }}
          </el-tag>
        </div>
        
        <div v-if="selectedNode.data?.description" class="detail-item">
          <label>描述:</label>
          <p>{{ selectedNode.data.description }}</p>
        </div>
        
        <div v-if="selectedNode.data?.priority" class="detail-item">
          <label>优先级:</label>
          <el-tag :type="getPriorityColor(selectedNode.data.priority)">
            {{ selectedNode.data.priority }}
          </el-tag>
        </div>
        
        <div v-if="selectedNode.data?.test_level" class="detail-item">
          <label>测试级别:</label>
          <span>{{ selectedNode.data.test_level }}</span>
        </div>
        
        <div v-if="selectedNode.data?.test_steps_count" class="detail-item">
          <label>测试步骤:</label>
          <span>{{ selectedNode.data.test_steps_count }} 步</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as d3 from 'd3'
import { ElMessage } from 'element-plus'
import {
  ZoomIn,
  ZoomOut,
  Refresh,
  Aim,
  VideoPlay,
  Download,
  Close
} from '@element-plus/icons-vue'

interface MindMapNode {
  id: string
  label: string
  type: string
  level: number
  data?: any
  style?: any
  children?: MindMapNode[]
  x?: number
  y?: number
  fx?: number
  fy?: number
}

interface Props {
  data: any
  viewMode?: string
  theme?: string
  layout?: string
  zoom?: number
  showAnimation?: boolean
}

interface Emits {
  (e: 'node-click', node: MindMapNode): void
  (e: 'zoom-change', zoom: number): void
}

const props = withDefaults(defineProps<Props>(), {
  viewMode: 'mind',
  theme: 'default',
  layout: 'horizontal',
  zoom: 1,
  showAnimation: true
})

const emit = defineEmits<Emits>()

const containerRef = ref<HTMLElement>()
const svgRef = ref<SVGElement>()
const selectedNode = ref<MindMapNode | null>(null)
const animationEnabled = ref(props.showAnimation)
const panelStyle = ref({})
const showDebug = ref(true)
const dataStatus = ref('未加载')
const nodeCount = ref(0)
const linkCount = ref(0)

let svg: d3.Selection<SVGElement, unknown, null, undefined>
let g: d3.Selection<SVGGElement, unknown, null, undefined>
let zoom: d3.ZoomBehavior<SVGElement, unknown>
let simulation: d3.Simulation<MindMapNode, undefined>

const width = ref(800)
const height = ref(600)
const currentZoom = ref(1)

// 节点类型颜色映射
const getNodeTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    'root': 'danger',
    'category': 'success', 
    'test_case': 'warning',
    'step': 'info'
  }
  return colorMap[type] || 'info'
}

const getNodeTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    'root': '根节点',
    'category': '分类',
    'test_case': '测试用例',
    'step': '测试步骤'
  }
  return labelMap[type] || type
}

const getPriorityColor = (priority: string) => {
  const colorMap: Record<string, string> = {
    'P0': 'danger',
    'P1': 'warning',
    'P2': 'info',
    'P3': 'success'
  }
  return colorMap[priority] || 'info'
}

// 初始化SVG
const initSVG = () => {
  if (!svgRef.value || !containerRef.value) {
    console.log('初始化SVG失败: 缺少DOM元素', { svgRef: svgRef.value, containerRef: containerRef.value })
    return false
  }

  const container = containerRef.value
  width.value = container.clientWidth || 800
  height.value = container.clientHeight || 600

  console.log('初始化SVG:', { width: width.value, height: height.value })

  svg = d3.select(svgRef.value)
    .attr('width', width.value)
    .attr('height', height.value)

  // 创建主要的g元素
  g = svg.append('g')

  // 设置缩放行为
  zoom = d3.zoom<SVGElement, unknown>()
    .scaleExtent([0.1, 3])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
      currentZoom.value = event.transform.k
      emit('zoom-change', currentZoom.value)
    })

  svg.call(zoom)

  console.log('SVG初始化完成')
  return true
}

// 转换数据结构
const transformData = (data: any): { nodes: MindMapNode[], links: any[] } => {
  console.log('开始转换数据:', data)

  if (!data) {
    dataStatus.value = '数据为空'
    return { nodes: [], links: [] }
  }

  if (!data.mind_map_data) {
    dataStatus.value = '缺少mind_map_data'
    return { nodes: [], links: [] }
  }

  const mindMapData = data.mind_map_data
  console.log('思维导图数据:', mindMapData)

  // 如果数据已经是nodes和edges格式
  if (mindMapData.nodes && mindMapData.edges) {
    dataStatus.value = '正在转换nodes/edges格式'

    const nodes: MindMapNode[] = mindMapData.nodes.map((node: any) => ({
      id: node.id,
      label: node.label || node.title || 'Unknown',
      type: node.type || 'default',
      level: node.level || 0,
      data: node.data,
      style: node.style
    }))

    const links = mindMapData.edges.map((edge: any) => ({
      source: edge.source,
      target: edge.target,
      id: edge.id,
      type: edge.type,
      style: edge.style
    }))

    nodeCount.value = nodes.length
    linkCount.value = links.length
    dataStatus.value = `转换完成: ${nodes.length}个节点, ${links.length}个连接`

    console.log('转换结果:', { nodes, links })
    return { nodes, links }
  }

  // 如果是树形结构，递归转换
  const nodes: MindMapNode[] = []
  const links: any[] = []

  const traverse = (node: any, level = 0, parentId?: string) => {
    const mindMapNode: MindMapNode = {
      id: node.id,
      label: node.label || node.title || 'Unknown',
      type: node.type || 'default',
      level,
      data: node.data,
      style: node.style
    }

    nodes.push(mindMapNode)

    if (parentId) {
      links.push({
        source: parentId,
        target: node.id
      })
    }

    if (node.children) {
      node.children.forEach((child: any) => {
        traverse(child, level + 1, node.id)
      })
    }
  }

  if (mindMapData.nodes) {
    traverse(mindMapData.nodes, 0)
  } else if (mindMapData) {
    traverse(mindMapData, 0)
  }

  return { nodes, links }
}

// 渲染思维导图
const renderMindMap = () => {
  console.log('开始渲染思维导图', { data: props.data, g, svg })

  if (!props.data) {
    console.log('渲染思维导图失败: 缺少数据')
    dataStatus.value = '缺少数据'
    return
  }

  if (!g) {
    console.log('SVG未初始化，尝试重新初始化')
    if (!initSVG()) {
      console.log('渲染思维导图失败: SVG初始化失败')
      dataStatus.value = 'SVG初始化失败'
      return
    }
  }

  const { nodes, links } = transformData(props.data)

  console.log('转换后的数据:', { nodes, links })

  if (nodes.length === 0) {
    console.log('没有节点数据')
    dataStatus.value = '没有节点数据'
    return
  }

  dataStatus.value = '开始渲染'

  // 清除之前的内容
  g.selectAll('*').remove()

  // 创建力导向模拟
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id((d: any) => d.id).distance(100))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width.value / 2, height.value / 2))
    .force('collision', d3.forceCollide().radius(50))

  // 创建连接线
  const link = g.append('g')
    .attr('class', 'links')
    .selectAll('line')
    .data(links)
    .enter().append('line')
    .attr('class', 'link')
    .style('stroke', '#999')
    .style('stroke-opacity', 0.6)
    .style('stroke-width', 2)

  // 创建节点组
  const node = g.append('g')
    .attr('class', 'nodes')
    .selectAll('g')
    .data(nodes)
    .enter().append('g')
    .attr('class', 'node')
    .style('cursor', 'pointer')
    .call(d3.drag<SVGGElement, MindMapNode>()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended))

  // 添加节点圆形
  node.append('circle')
    .attr('r', (d) => {
      switch (d.type) {
        case 'root': return 30
        case 'category': return 25
        case 'test_case': return 20
        default: return 15
      }
    })
    .style('fill', (d) => {
      switch (d.type) {
        case 'root': return 'url(#rootGradient)'
        case 'category': return 'url(#categoryGradient)'
        case 'test_case': return 'url(#testcaseGradient)'
        default: return 'url(#nodeGradient)'
      }
    })
    .style('filter', 'url(#dropshadow)')
    .on('mouseover', function(event, d) {
      d3.select(this).style('filter', 'url(#glow)')
    })
    .on('mouseout', function(event, d) {
      d3.select(this).style('filter', 'url(#dropshadow)')
    })
    .on('click', (event, d) => {
      handleNodeClick(event, d)
    })

  // 添加节点文本
  node.append('text')
    .text((d) => d.label.length > 15 ? d.label.substring(0, 15) + '...' : d.label)
    .attr('dy', '.35em')
    .attr('text-anchor', 'middle')
    .style('fill', '#fff')
    .style('font-size', '12px')
    .style('font-weight', 'bold')
    .style('pointer-events', 'none')

  // 更新模拟
  simulation.on('tick', () => {
    link
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y)

    node
      .attr('transform', (d) => `translate(${d.x},${d.y})`)
  })

  // 如果启用动画，添加进入动画
  if (animationEnabled.value) {
    node.style('opacity', 0)
      .transition()
      .duration(1000)
      .delay((d, i) => i * 100)
      .style('opacity', 1)

    link.style('opacity', 0)
      .transition()
      .duration(1000)
      .delay(500)
      .style('opacity', 0.6)
  }

  dataStatus.value = '渲染完成'
  console.log('思维导图渲染完成')
}

// 拖拽事件处理
const dragstarted = (event: any, d: MindMapNode) => {
  if (!event.active) simulation.alphaTarget(0.3).restart()
  d.fx = d.x
  d.fy = d.y
}

const dragged = (event: any, d: MindMapNode) => {
  d.fx = event.x
  d.fy = event.y
}

const dragended = (event: any, d: MindMapNode) => {
  if (!event.active) simulation.alphaTarget(0)
  d.fx = null
  d.fy = null
}

// 节点点击处理
const handleNodeClick = (event: MouseEvent, node: MindMapNode) => {
  selectedNode.value = node

  // 计算面板位置
  const rect = containerRef.value?.getBoundingClientRect()
  if (rect) {
    panelStyle.value = {
      left: `${Math.min(event.clientX - rect.left + 20, rect.width - 300)}px`,
      top: `${Math.max(event.clientY - rect.top - 100, 20)}px`
    }
  }

  emit('node-click', node)
}

// 工具栏操作
const zoomIn = () => {
  if (!svg) return
  svg.transition().duration(300).call(
    zoom.scaleBy, 1.2
  )
}

const zoomOut = () => {
  if (!svg) return
  svg.transition().duration(300).call(
    zoom.scaleBy, 0.8
  )
}

const resetZoom = () => {
  if (!svg) return
  svg.transition().duration(500).call(
    zoom.transform,
    d3.zoomIdentity
  )
}

const centerView = () => {
  if (!svg || !g) return

  const bounds = g.node()?.getBBox()
  if (!bounds) return

  const fullWidth = width.value
  const fullHeight = height.value
  const scale = 0.8 / Math.max(bounds.width / fullWidth, bounds.height / fullHeight)
  const translate = [
    fullWidth / 2 - scale * (bounds.x + bounds.width / 2),
    fullHeight / 2 - scale * (bounds.y + bounds.height / 2)
  ]

  svg.transition().duration(750).call(
    zoom.transform,
    d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
  )
}

const toggleAnimation = () => {
  animationEnabled.value = !animationEnabled.value
  ElMessage.success(`动画效果已${animationEnabled.value ? '开启' : '关闭'}`)
}

const exportImage = () => {
  if (!svgRef.value) return

  try {
    const svgData = new XMLSerializer().serializeToString(svgRef.value)
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()

    canvas.width = width.value
    canvas.height = height.value

    img.onload = () => {
      ctx?.drawImage(img, 0, 0)
      const link = document.createElement('a')
      link.download = 'mindmap.png'
      link.href = canvas.toDataURL()
      link.click()
    }

    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)))
    ElMessage.success('图片导出成功')
  } catch (error) {
    ElMessage.error('图片导出失败')
  }
}

const closePanel = () => {
  selectedNode.value = null
}

// 响应式处理
const handleResize = () => {
  if (!containerRef.value || !svg) return

  const container = containerRef.value
  width.value = container.clientWidth
  height.value = container.clientHeight

  svg.attr('width', width.value).attr('height', height.value)

  if (simulation) {
    simulation.force('center', d3.forceCenter(width.value / 2, height.value / 2))
    simulation.alpha(0.3).restart()
  }
}

// 监听数据变化
watch(() => props.data, () => {
  nextTick(() => {
    renderMindMap()
  })
}, { deep: true })

watch(() => props.zoom, (newZoom) => {
  if (svg && Math.abs(currentZoom.value - newZoom) > 0.01) {
    svg.transition().duration(300).call(
      zoom.scaleTo, newZoom
    )
  }
})

onMounted(() => {
  console.log('MindMapViewer mounted', { props: props.data })
  nextTick(() => {
    console.log('nextTick - 开始初始化')
    if (initSVG()) {
      renderMindMap()
    } else {
      console.log('SVG初始化失败，延迟重试')
      setTimeout(() => {
        if (initSVG()) {
          renderMindMap()
        }
      }, 100)
    }
    window.addEventListener('resize', handleResize)
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (simulation) {
    simulation.stop()
  }
})
</script>

<style lang="scss" scoped>
.mindmap-viewer {
  position: relative;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  overflow: hidden;

  .debug-info {
    position: absolute;
    top: 10px;
    left: 10px;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 10px;
    border-radius: 4px;
    font-size: 12px;
    z-index: 100;

    p {
      margin: 2px 0;
    }
  }

  .mindmap-svg {
    width: 100%;
    height: 100%;
    background: radial-gradient(circle at center, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
  }

  .mindmap-toolbar {
    position: absolute;
    top: 20px;
    right: 20px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    z-index: 10;

    .toolbar-group {
      display: flex;
      flex-direction: column;
      gap: 5px;
      background: rgba(255, 255, 255, 0.9);
      border-radius: 8px;
      padding: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      backdrop-filter: blur(10px);

      .toolbar-btn {
        width: 36px;
        height: 36px;
        border: none;
        border-radius: 6px;
        background: transparent;
        color: #666;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;

        &:hover {
          background: rgba(102, 126, 234, 0.1);
          color: #667eea;
          transform: scale(1.05);
        }

        &.active {
          background: #667eea;
          color: white;
        }
      }
    }
  }

  .node-detail-panel {
    position: absolute;
    width: 280px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    z-index: 20;
    overflow: hidden;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);

    .panel-header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;

      h4 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
      }

      .close-btn {
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        transition: background 0.3s ease;

        &:hover {
          background: rgba(255, 255, 255, 0.2);
        }
      }
    }

    .panel-content {
      padding: 16px;

      .detail-item {
        margin-bottom: 12px;

        &:last-child {
          margin-bottom: 0;
        }

        label {
          display: block;
          font-size: 12px;
          color: #666;
          margin-bottom: 4px;
          font-weight: 500;
        }

        p {
          margin: 0;
          font-size: 14px;
          color: #333;
          line-height: 1.4;
        }

        span {
          font-size: 14px;
          color: #333;
        }
      }
    }
  }
}

// 全局样式覆盖
:deep(.link) {
  stroke-dasharray: 5,5;
  animation: dash 1s linear infinite;
}

@keyframes dash {
  to {
    stroke-dashoffset: -10;
  }
}

// 节点悬停效果
:deep(.node) {
  transition: all 0.3s ease;

  &:hover {
    transform: scale(1.1);
  }

  circle {
    transition: all 0.3s ease;
  }

  text {
    transition: all 0.3s ease;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .mindmap-viewer {
    .mindmap-toolbar {
      top: 10px;
      right: 10px;

      .toolbar-group {
        padding: 6px;

        .toolbar-btn {
          width: 32px;
          height: 32px;
        }
      }
    }

    .node-detail-panel {
      width: 240px;

      .panel-header {
        padding: 12px;

        h4 {
          font-size: 14px;
        }
      }

      .panel-content {
        padding: 12px;

        .detail-item {
          margin-bottom: 10px;

          label {
            font-size: 11px;
          }

          p, span {
            font-size: 13px;
          }
        }
      }
    }
  }
}
</style>
