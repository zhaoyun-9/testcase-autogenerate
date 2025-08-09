<template>
  <div class="simple-mindmap" ref="containerRef">
    <div class="debug-panel">
      <h4>调试信息</h4>
      <p>状态: {{ status }}</p>
      <p>节点数: {{ nodeCount }}</p>
      <p>连接数: {{ linkCount }}</p>
      <button @click="forceRender">强制重新渲染</button>
    </div>
    
    <svg ref="svgRef" class="mindmap-svg">
      <!-- SVG内容将由D3.js动态生成 -->
    </svg>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import * as d3 from 'd3'

interface Props {
  data: any
}

const props = defineProps<Props>()

const containerRef = ref<HTMLElement>()
const svgRef = ref<SVGElement>()
const status = ref('初始化中...')
const nodeCount = ref(0)
const linkCount = ref(0)

let svg: any
let width = 800
let height = 600

const forceRender = () => {
  status.value = '强制重新渲染...'
  renderMindMap()
}

const initSVG = () => {
  if (!svgRef.value || !containerRef.value) {
    status.value = 'DOM元素未准备好'
    return false
  }

  const container = containerRef.value
  width = container.clientWidth || 800
  height = container.clientHeight || 600

  svg = d3.select(svgRef.value)
    .attr('width', width)
    .attr('height', height)
    .style('background', 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)')

  status.value = `SVG初始化完成 ${width}x${height}`
  return true
}

const transformData = (data: any) => {
  console.log('转换数据:', data)
  
  if (!data || !data.mind_map_data) {
    status.value = '数据格式错误'
    return { nodes: [], links: [] }
  }

  const mindMapData = data.mind_map_data

  if (mindMapData.nodes && mindMapData.edges) {
    const nodes = mindMapData.nodes.map((node: any) => ({
      id: node.id,
      label: node.label || 'Unknown',
      type: node.type || 'default',
      x: Math.random() * width,
      y: Math.random() * height
    }))

    const links = mindMapData.edges.map((edge: any) => ({
      source: edge.source,
      target: edge.target
    }))

    nodeCount.value = nodes.length
    linkCount.value = links.length
    status.value = `数据转换完成: ${nodes.length}节点, ${links.length}连接`
    
    return { nodes, links }
  }

  status.value = '不支持的数据格式'
  return { nodes: [], links: [] }
}

const renderMindMap = () => {
  console.log('开始渲染思维导图')
  status.value = '开始渲染...'

  if (!svg) {
    if (!initSVG()) {
      return
    }
  }

  if (!props.data) {
    status.value = '没有数据'
    return
  }

  const { nodes, links } = transformData(props.data)

  if (nodes.length === 0) {
    status.value = '没有节点数据'
    return
  }

  // 清除之前的内容
  svg.selectAll('*').remove()

  // 创建连接线
  const link = svg.selectAll('.link')
    .data(links)
    .enter()
    .append('line')
    .attr('class', 'link')
    .style('stroke', '#999')
    .style('stroke-width', 2)
    .style('stroke-opacity', 0.6)

  // 创建节点
  const node = svg.selectAll('.node')
    .data(nodes)
    .enter()
    .append('g')
    .attr('class', 'node')

  // 添加圆形
  node.append('circle')
    .attr('r', (d: any) => {
      switch (d.type) {
        case 'root': return 30
        case 'category': return 25
        case 'test_case': return 20
        default: return 15
      }
    })
    .style('fill', (d: any) => {
      switch (d.type) {
        case 'root': return '#ff6b6b'
        case 'category': return '#4ecdc4'
        case 'test_case': return '#feca57'
        default: return '#667eea'
      }
    })
    .style('stroke', '#fff')
    .style('stroke-width', 2)
    .style('cursor', 'pointer')

  // 添加文本
  node.append('text')
    .text((d: any) => d.label.length > 10 ? d.label.substring(0, 10) + '...' : d.label)
    .attr('text-anchor', 'middle')
    .attr('dy', '.35em')
    .style('fill', '#fff')
    .style('font-size', '12px')
    .style('font-weight', 'bold')
    .style('pointer-events', 'none')

  // 创建力导向模拟
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id((d: any) => d.id).distance(100))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(60))

  // 更新位置
  simulation.on('tick', () => {
    link
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y)

    node
      .attr('transform', (d: any) => `translate(${d.x},${d.y})`)
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

  status.value = '渲染完成!'
  console.log('思维导图渲染完成')
}

// 监听数据变化
watch(() => props.data, () => {
  console.log('数据变化，重新渲染')
  nextTick(() => {
    renderMindMap()
  })
}, { deep: true })

onMounted(() => {
  console.log('SimpleMindMap mounted')
  nextTick(() => {
    if (initSVG()) {
      renderMindMap()
    }
  })
})
</script>

<style lang="scss" scoped>
.simple-mindmap {
  position: relative;
  width: 100%;
  height: 100%;
  border: 2px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  
  .debug-panel {
    position: absolute;
    top: 10px;
    left: 10px;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 10px;
    border-radius: 4px;
    font-size: 12px;
    z-index: 100;
    
    h4 {
      margin: 0 0 8px 0;
      font-size: 14px;
    }
    
    p {
      margin: 2px 0;
    }
    
    button {
      margin-top: 8px;
      padding: 4px 8px;
      background: #667eea;
      color: white;
      border: none;
      border-radius: 3px;
      cursor: pointer;
      font-size: 11px;
      
      &:hover {
        background: #5a67d8;
      }
    }
  }
  
  .mindmap-svg {
    width: 100%;
    height: 100%;
  }
}
</style>
