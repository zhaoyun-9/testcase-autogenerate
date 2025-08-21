<template>
  <div class="video-upload-test">
    <h1>视频文件上传测试页面</h1>
    
    <div class="test-section">
      <h2>文件类型映射测试</h2>
      <div class="mapping-test">
        <div v-for="(category, ext) in FILE_TYPE_MAPPING" :key="ext" class="mapping-item">
          <strong>{{ ext }}</strong> → {{ category }}
          <span class="icon">{{ getFileTypeIcon(ext) }}</span>
          <span class="color" :style="{ color: getFileTypeColor(ext) }">●</span>
          <span class="label">{{ getFileTypeLabel(ext) }}</span>
        </div>
      </div>
    </div>
    
    <div class="test-section">
      <h2>文件上传组件测试</h2>
      <FileUpload
        ref="fileUploadRef"
        :multiple="true"
        :max-size="500"
        :max-count="10"
        accepted-types=".pdf,.doc,.docx,.txt,.md,.png,.jpg,.jpeg,.json,.yaml,.yml,.mp4,.avi,.mov,.wmv,.flv,.webm"
        @change="handleFileChange"
      />
    </div>
    
    <div class="test-section" v-if="selectedFiles.length > 0">
      <h2>选择的文件</h2>
      <div class="file-list">
        <div v-for="file in selectedFiles" :key="file.uid" class="file-item">
          <el-icon :color="getFileTypeColor(file.type)">
            <component :is="getFileTypeIcon(file.type)" />
          </el-icon>
          <div class="file-info">
            <div class="file-name">{{ file.name }}</div>
            <div class="file-meta">
              <span>{{ formatFileSize(file.size) }}</span>
              <span>{{ getFileTypeLabel(file.type) }}</span>
              <span v-if="file.recommendedAgent">推荐: {{ file.recommendedAgent }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="test-section">
      <h2>支持的格式显示测试</h2>
      <div class="formats-display">
        <el-tag
          v-for="format in displayFormats"
          :key="format"
          size="small"
          type="info"
          effect="plain"
        >
          {{ format }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { FILE_TYPE_MAPPING } from '@/types/testCase'
import FileUpload from '@/components/FileUpload/index.vue'
import { VideoPlay, Picture, Document, DocumentCopy, Coin } from '@element-plus/icons-vue'

interface FileItem {
  uid: string
  name: string
  size: number
  type: string
  file: File
  recommendedAgent?: string
  category?: string
}

const fileUploadRef = ref()
const selectedFiles = ref<FileItem[]>([])

// 支持的文件格式显示
const displayFormats = computed(() => {
  const formats = Object.keys(FILE_TYPE_MAPPING)
  console.log('FILE_TYPE_MAPPING keys:', formats)
  
  const priorityFormats = ['.JPG', '.PNG', '.PDF', '.DOC', '.JSON', '.MP4', '.AVI', '.MOV']
  const allFormats = formats.map(ext => ext.toUpperCase())
  
  console.log('All formats (uppercase):', allFormats)
  
  const result = []
  priorityFormats.forEach(format => {
    if (allFormats.includes(format) && !result.includes(format)) {
      result.push(format)
    }
  })
  
  allFormats.forEach(format => {
    if (result.length < 8 && !result.includes(format)) {
      result.push(format)
    }
  })
  
  console.log('Display formats result:', result)
  return result
})

// 获取文件类型图标
const getFileTypeIcon = (type: string) => {
  const iconMap: Record<string, any> = {
    '.jpg': Picture,
    '.jpeg': Picture,
    '.png': Picture,
    '.gif': Picture,
    '.bmp': Picture,
    '.webp': Picture,
    '.pdf': Document,
    '.doc': Document,
    '.docx': Document,
    '.txt': Document,
    '.md': Document,
    '.json': DocumentCopy,
    '.yaml': DocumentCopy,
    '.yml': DocumentCopy,
    '.sql': Coin,
    '.db': Coin,
    '.sqlite': Coin,
    '.mp4': VideoPlay,
    '.avi': VideoPlay,
    '.mov': VideoPlay,
    '.wmv': VideoPlay,
    '.flv': VideoPlay,
    '.webm': VideoPlay
  }
  return iconMap[type] || Document
}

// 获取文件类型颜色
const getFileTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    '.jpg': '#67C23A',
    '.jpeg': '#67C23A',
    '.png': '#67C23A',
    '.gif': '#67C23A',
    '.bmp': '#67C23A',
    '.webp': '#67C23A',
    '.pdf': '#E6A23C',
    '.doc': '#409EFF',
    '.docx': '#409EFF',
    '.txt': '#909399',
    '.md': '#909399',
    '.json': '#F56C6C',
    '.yaml': '#F56C6C',
    '.yml': '#F56C6C',
    '.sql': '#9C27B0',
    '.db': '#9C27B0',
    '.sqlite': '#9C27B0',
    '.mp4': '#FF9800',
    '.avi': '#FF9800',
    '.mov': '#FF9800',
    '.wmv': '#FF9800',
    '.flv': '#FF9800',
    '.webm': '#FF9800'
  }
  return colorMap[type] || '#909399'
}

// 获取文件类型标签
const getFileTypeLabel = (type: string) => {
  const category = FILE_TYPE_MAPPING[type as keyof typeof FILE_TYPE_MAPPING]
  const labelMap: Record<string, string> = {
    image: '图片',
    document: '文档',
    api_spec: 'API规范',
    database: '数据库',
    video: '视频'
  }
  return labelMap[category] || '未知'
}

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 处理文件变化
const handleFileChange = (files: FileItem[]) => {
  selectedFiles.value = files
  console.log('Selected files:', files)
}
</script>

<style lang="scss" scoped>
.video-upload-test {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.test-section {
  margin: 30px 0;
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  
  h2 {
    margin-top: 0;
    color: #303133;
  }
}

.mapping-test {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 10px;
}

.mapping-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  
  .icon {
    font-size: 20px;
  }
  
  .color {
    font-size: 16px;
  }
}

.file-list {
  .file-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border: 1px solid #e4e7ed;
    border-radius: 6px;
    margin-bottom: 8px;
    
    .file-info {
      flex: 1;
      
      .file-name {
        font-weight: 500;
        margin-bottom: 4px;
      }
      
      .file-meta {
        font-size: 12px;
        color: #909399;
        
        span {
          margin-right: 12px;
        }
      }
    }
  }
}

.formats-display {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
