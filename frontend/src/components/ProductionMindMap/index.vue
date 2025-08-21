<template>
  <div class="production-mindmap" ref="containerRef">
    <svg ref="svgRef" class="mindmap-svg"></svg>
    
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
        <button @click="fitToView" class="toolbar-btn" title="适应视图">
          <el-icon><FullScreen /></el-icon>
        </button>
        <button @click="centerView" class="toolbar-btn" title="居中显示">
          <el-icon><Aim /></el-icon>
        </button>
      </div>
    </div>
    
    <!-- 节点详情面板 -->
    <div v-if="selectedNode" class="node-detail-panel" :style="panelStyle">
      <div class="panel-header">
        <h4>{{ selectedNode.label }}</h4>
        <button @click="closePanel" class="close-btn">×</button>
      </div>
      <div class="panel-content">
        <div class="detail-item">
          <label>类型:</label>
          <span class="node-type" :class="selectedNode.type">{{ getNodeTypeLabel(selectedNode.type) }}</span>
        </div>
        <div v-if="selectedNode.data?.description" class="detail-item">
          <label>描述:</label>
          <p>{{ selectedNode.data.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as d3 from 'd3'
import { ZoomIn, ZoomOut, Refresh, Aim, FullScreen } from '@element-plus/icons-vue'

interface MindMapNode {
  id: string
  label: string
  type: string
  level: number
  data?: any
  x?: number
  y?: number
  fx?: number
  fy?: number
}

interface Props {
  data: any
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'node-click': [node: MindMapNode]
}>()

const containerRef = ref<HTMLElement>()
const svgRef = ref<SVGElement>()
const selectedNode = ref<MindMapNode | null>(null)
const panelStyle = ref({})

let svg: any
let g: any
let zoom: any
let simulation: any
let width = 800
let height = 600

const getNodeTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    'root': '根节点',
    'category': '分类',
    'test_case': '测试用例',
    'step': '测试步骤'
  }
  return labelMap[type] || type
}

const initSVG = () => {
  if (!svgRef.value || !containerRef.value) return false

  const container = containerRef.value
  width = container.clientWidth || 800
  height = container.clientHeight || 600

  svg = d3.select(svgRef.value)
    .attr('width', width)
    .attr('height', height)

  g = svg.append('g')

  zoom = d3.zoom()
    .scaleExtent([0.1, 3])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    })

  svg.call(zoom)
  return true
}

const transformData = (data: any) => {
  // 如果是新的API格式
  if (data?.mind_map_data?.nodes && data?.mind_map_data?.edges) {
    const nodes = data.mind_map_data.nodes.map((node: any) => ({
      id: node.id,
      label: node.label || 'Unknown',
      type: node.type || 'default',
      level: node.level || 0,
      data: node.data
    }))

    const links = data.mind_map_data.edges.map((edge: any) => ({
      source: edge.source,
      target: edge.target
    }))

    return { nodes, links }
  }

  // 如果是树形结构数据，转换为节点和边
  if (data && (data.id || data.title)) {
    const nodes: any[] = []
    const links: any[] = []

    const traverse = (node: any, level = 0) => {
      nodes.push({
        id: node.id,
        label: node.title || node.label || 'Unknown',
        type: node.type || 'default',
        level,
        data: {
          description: node.description,
          priority: node.priority,
          status: node.status,
          testSteps: node.testSteps,
          tags: node.tags
        }
      })

      if (node.children && Array.isArray(node.children)) {
        node.children.forEach((child: any) => {
          links.push({
            source: node.id,
            target: child.id
          })
          traverse(child, level + 1)
        })
      }
    }

    traverse(data)
    return { nodes, links }
  }

  return { nodes: [], links: [] }
}

const renderMindMap = () => {
  console.log('开始渲染思维导图，数据:', props.data)
  if (!props.data || !g) {
    console.log('数据或SVG容器不存在')
    return
  }

  const { nodes, links } = transformData(props.data)
  console.log('转换后的节点和连接:', { nodes, links })
  if (nodes.length === 0) {
    console.log('没有节点数据')
    return
  }

  // 清除之前的内容
  g.selectAll('*').remove()

  // 创建力导向模拟
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id((d: any) => d.id).distance(120))
    .force('charge', d3.forceManyBody().strength(-400))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(60))

  // 创建连接线
  const link = g.selectAll('.link')
    .data(links)
    .enter()
    .append('line')
    .attr('class', 'link')
    .style('stroke', '#999')
    .style('stroke-width', 2)
    .style('stroke-opacity', 0.6)

  // 创建节点组
  const node = g.selectAll('.node')
    .data(nodes)
    .enter()
    .append('g')
    .attr('class', 'node')
    .style('cursor', 'pointer')

  // 添加节点圆形
  node.append('circle')
    .attr('r', (d: any) => {
      switch (d.type) {
        case 'root': return 35
        case 'category': return 28
        case 'module': return 25
        case 'testcase': return 22
        case 'test_case': return 22
        default: return 18
      }
    })
    .style('fill', (d: any) => {
      switch (d.type) {
        case 'root': return '#ff6b6b'
        case 'category': return '#4ecdc4'
        case 'module': return '#48cae4'
        case 'testcase': return '#feca57'
        case 'test_case': return '#feca57'
        default: return '#667eea'
      }
    })
    .style('stroke', '#fff')
    .style('stroke-width', 3)
    .style('filter', 'drop-shadow(2px 2px 4px rgba(0,0,0,0.3))')

  // 添加节点文本
  node.append('text')
    .text((d: any) => d.label.length > 12 ? d.label.substring(0, 12) + '...' : d.label)
    .attr('text-anchor', 'middle')
    .attr('dy', '.35em')
    .style('fill', '#fff')
    .style('font-size', '12px')
    .style('font-weight', 'bold')
    .style('pointer-events', 'none')

  // 添加交互
  node.on('click', (event, d) => {
    selectedNode.value = d
    const rect = containerRef.value?.getBoundingClientRect()
    if (rect) {
      panelStyle.value = {
        left: `${Math.min(event.clientX - rect.left + 20, rect.width - 300)}px`,
        top: `${Math.max(event.clientY - rect.top - 100, 20)}px`
      }
    }
    emit('node-click', d)
  })

  // 添加拖拽
  node.call(d3.drag()
    .on('start', (event: any, d: any) => {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      d.fx = d.x
      d.fy = d.y
    })
    .on('drag', (event: any, d: any) => {
      d.fx = event.x
      d.fy = event.y
    })
    .on('end', (event: any, d: any) => {
      if (!event.active) simulation.alphaTarget(0)
      d.fx = null
      d.fy = null
    })
  )

  // 更新模拟
  simulation.on('tick', () => {
    link
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y)

    node.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
  })

  // 添加进入动画
  node.style('opacity', 0)
    .transition()
    .duration(800)
    .delay((d, i) => i * 100)
    .style('opacity', 1)

  // 在模拟稳定后自动适应视图
  simulation.on('end', () => {
    setTimeout(() => {
      fitToView()
    }, 500)
  })

  // 立即进行一次初始适应，确保内容可见且工具栏不被遮挡
  setTimeout(() => {
    fitToView()
  }, 100)
}

// 工具栏功能
const zoomIn = () => svg?.transition().duration(300).call(zoom.scaleBy, 1.2)
const zoomOut = () => svg?.transition().duration(300).call(zoom.scaleBy, 0.8)
const resetZoom = () => svg?.transition().duration(500).call(zoom.transform, d3.zoomIdentity)

const fitToView = () => {
  if (!svg || !g) return
  const bounds = g.node()?.getBBox()
  if (!bounds) return

  // 工具栏在左上角，为其留出空间
  const toolbarSpace = 120 // 左上角工具栏占用的空间
  const padding = 60

  const availableWidth = width - padding * 2
  const availableHeight = height - padding * 2

  const scale = Math.min(
    availableWidth / bounds.width,
    availableHeight / bounds.height,
    0.9 // 限制最大缩放
  ) * 0.8 // 留一些边距

  // 居中显示，稍微向右下偏移避开工具栏
  const offsetX = toolbarSpace / 2
  const offsetY = toolbarSpace / 2

  const translate = [
    width / 2 - scale * (bounds.x + bounds.width / 2) + offsetX,
    height / 2 - scale * (bounds.y + bounds.height / 2) + offsetY
  ]

  svg.transition().duration(500).call(
    zoom.transform,
    d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
  )
}
const centerView = () => {
  if (!svg || !g) return
  const bounds = g.node()?.getBBox()
  if (!bounds) return

  // 为工具栏和边距留出空间
  const padding = 100 // 增加边距
  const availableWidth = width - padding
  const availableHeight = height - padding

  const scale = 0.8 / Math.max(bounds.width / availableWidth, bounds.height / availableHeight)
  const translate = [
    width / 2 - scale * (bounds.x + bounds.width / 2),
    height / 2 - scale * (bounds.y + bounds.height / 2)
  ]

  svg.transition().duration(750).call(
    zoom.transform,
    d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
  )
}

const closePanel = () => {
  selectedNode.value = null
}

// 监听数据变化
watch(() => props.data, () => {
  nextTick(() => renderMindMap())
}, { deep: true })

// 窗口大小改变处理
const handleResize = () => {
  if (!containerRef.value) return

  const container = containerRef.value
  const newWidth = container.clientWidth
  const newHeight = container.clientHeight

  if (newWidth !== width || newHeight !== height) {
    width = newWidth
    height = newHeight

    if (svg) {
      svg.attr('width', width).attr('height', height)
      // 重新调整视图
      setTimeout(() => {
        fitToView()
      }, 100)
    }
  }
}

onMounted(() => {
  console.log('ProductionMindMap 组件已挂载')
  nextTick(() => {
    if (initSVG()) {
      console.log('SVG 初始化成功')
      renderMindMap()
    } else {
      console.log('SVG 初始化失败')
    }
  })

  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (simulation) simulation.stop()
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
.production-mindmap {
  position: relative;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  
  .mindmap-svg {
    width: 100%;
    height: 100%;
  }
  
  .mindmap-toolbar {
    position: absolute;
    top: 20px;
    left: 20px;
    z-index: 1000;
    
    .toolbar-group {
      display: flex;
      flex-direction: row; // 改为水平排列，更适合左上角
      gap: 8px;
      background: rgba(255, 255, 255, 0.95);
      border-radius: 12px;
      padding: 8px 12px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.2);
      
      .toolbar-btn {
        width: 40px;
        height: 40px;
        border: none;
        border-radius: 8px;
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
      }
    }
  }
  
  .node-detail-panel {
    position: absolute;
    width: 280px;
    background: white;
    border-radius: 16px;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
    z-index: 20;
    overflow: hidden;
    
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
        font-size: 20px;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        
        &:hover {
          background: rgba(255, 255, 255, 0.2);
        }
      }
    }
    
    .panel-content {
      padding: 16px;
      
      .detail-item {
        margin-bottom: 12px;
        
        label {
          display: block;
          font-size: 12px;
          color: #666;
          margin-bottom: 4px;
          font-weight: 500;
        }
        
        .node-type {
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
          
          &.root { background: #ffe6e6; color: #ff6b6b; }
          &.category { background: #e6f7f7; color: #4ecdc4; }
          &.test_case { background: #fff4e6; color: #feca57; }
        }
        
        p {
          margin: 0;
          font-size: 14px;
          color: #333;
          line-height: 1.4;
        }
      }
    }
  }
}
</style>
