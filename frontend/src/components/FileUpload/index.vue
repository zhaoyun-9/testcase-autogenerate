<template>
  <div class="file-upload-container">
    <!-- 文件上传区域 -->
    <div
      class="upload-area"
      :class="{
        'is-dragover': isDragOver,
        'is-disabled': disabled
      }"
      @drop="handleDrop"
      @dragover="handleDragOver"
      @dragenter="handleDragEnter"
      @dragleave="handleDragLeave"
      @click="triggerFileInput"
    >
      <input
        ref="fileInputRef"
        type="file"
        :accept="acceptedTypes"
        :multiple="multiple"
        style="display: none"
        @change="handleFileSelect"
      />
      
      <div class="upload-content">
        <el-icon class="upload-icon" size="48" color="#C0C4CC">
          <UploadFilled />
        </el-icon>
        
        <div class="upload-text">
          <p class="upload-title">
            {{ uploadTitle }}
          </p>
          <p class="upload-subtitle">
            {{ uploadSubtitle }}
          </p>
        </div>
        
        <div class="supported-formats">
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

    <!-- 文件列表 -->
    <div v-if="fileList.length > 0" class="file-list">
      <div class="file-list-header">
        <span>已选择文件 ({{ fileList.length }})</span>
        <el-button
          type="text"
          size="small"
          @click="clearFiles"
          :disabled="disabled"
        >
          清空
        </el-button>
      </div>
      
      <div class="file-items">
        <div
          v-for="(file, index) in fileList"
          :key="file.uid"
          class="file-item"
        >
          <div class="file-info">
            <el-icon class="file-icon" :color="getFileTypeColor(file.type)">
              <component :is="getFileTypeIcon(file.type)" />
            </el-icon>
            
            <div class="file-details">
              <div class="file-name" :title="file.name">
                {{ file.name }}
              </div>
              <div class="file-meta">
                <span class="file-size">{{ formatFileSize(file.size) }}</span>
                <span class="file-type">{{ getFileTypeLabel(file.type) }}</span>
                <span v-if="file.recommendedAgent" class="recommended-agent">
                  推荐: {{ file.recommendedAgent }}
                </span>
              </div>
            </div>
          </div>
          
          <div class="file-actions">
            <el-button
              type="text"
              size="small"
              @click="removeFile(index)"
              :disabled="disabled"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 文件描述输入 -->
    <div v-if="showDescription && fileList.length > 0" class="file-description">
      <el-input
        v-model="description"
        type="textarea"
        :rows="3"
        placeholder="请输入文件描述或分析要求（可选）"
        :disabled="disabled"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { FILE_TYPE_MAPPING } from '@/types/testCase'
import { fileApi } from '@/api/testCase'

interface FileItem {
  uid: string
  name: string
  size: number
  type: string
  file: File
  recommendedAgent?: string
  category?: string
}

interface Props {
  multiple?: boolean
  disabled?: boolean
  maxSize?: number // MB
  maxCount?: number
  acceptedTypes?: string
  showDescription?: boolean
  uploadTitle?: string
  uploadSubtitle?: string
}

interface Emits {
  (e: 'change', files: FileItem[], description?: string): void
  (e: 'remove', file: FileItem, index: number): void
  (e: 'clear'): void
}

const props = withDefaults(defineProps<Props>(), {
  multiple: true,
  disabled: false,
  maxSize: 50,
  maxCount: 10,
  acceptedTypes: '',
  showDescription: true,
  uploadTitle: '点击或拖拽文件到此区域上传',
  uploadSubtitle: '支持多种文件格式，智能识别文件类型并推荐最佳处理方式'
})

const emit = defineEmits<Emits>()

const fileInputRef = ref<HTMLInputElement>()
const isDragOver = ref(false)
const fileList = ref<FileItem[]>([])
const description = ref('')

// 支持的文件格式显示
const displayFormats = computed(() => {
  const formats = Object.keys(FILE_TYPE_MAPPING)
  return formats.slice(0, 8).map(ext => ext.toUpperCase())
})

// 监听文件列表变化
watch([fileList, description], () => {
  emit('change', fileList.value, description.value)
}, { deep: true })

// 触发文件选择
const triggerFileInput = () => {
  if (!props.disabled) {
    fileInputRef.value?.click()
  }
}

// 处理文件选择
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files || [])
  processFiles(files)
  // 清空input值，允许重复选择同一文件
  target.value = ''
}

// 处理拖拽相关事件
const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  if (!props.disabled) {
    isDragOver.value = true
  }
}

const handleDragEnter = (event: DragEvent) => {
  event.preventDefault()
  if (!props.disabled) {
    isDragOver.value = true
  }
}

const handleDragLeave = (event: DragEvent) => {
  event.preventDefault()
  // 只有当离开整个拖拽区域时才设置为false
  if (!event.currentTarget?.contains(event.relatedTarget as Node)) {
    isDragOver.value = false
  }
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
  
  if (props.disabled) return
  
  const files = Array.from(event.dataTransfer?.files || [])
  processFiles(files)
}

// 处理文件
const processFiles = async (files: File[]) => {
  if (files.length === 0) return
  
  // 检查文件数量限制
  if (!props.multiple && files.length > 1) {
    ElMessage.warning('只能选择一个文件')
    return
  }
  
  if (fileList.value.length + files.length > props.maxCount) {
    ElMessage.warning(`最多只能选择 ${props.maxCount} 个文件`)
    return
  }
  
  const validFiles: FileItem[] = []
  
  for (const file of files) {
    // 检查文件大小
    if (file.size > props.maxSize * 1024 * 1024) {
      ElMessage.warning(`文件 ${file.name} 超过大小限制 ${props.maxSize}MB`)
      continue
    }
    
    // 检查文件类型
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    if (props.acceptedTypes && !props.acceptedTypes.includes(fileExtension)) {
      ElMessage.warning(`不支持的文件类型: ${file.name}`)
      continue
    }
    
    const fileItem: FileItem = {
      uid: 'file_' + Date.now() + '_' + Math.random().toString(36).substr(2),
      name: file.name,
      size: file.size,
      type: fileExtension,
      file
    }
    
    // 分析文件并获取推荐智能体
    try {
      const analysis = await fileApi.analyzeFile(file)
      fileItem.recommendedAgent = analysis.recommendedAgent
      fileItem.category = analysis.fileCategory
    } catch (error) {
      console.warn('文件分析失败:', error)
    }
    
    validFiles.push(fileItem)
  }
  
  if (validFiles.length > 0) {
    if (props.multiple) {
      fileList.value.push(...validFiles)
    } else {
      fileList.value = validFiles
    }
    ElMessage.success(`成功添加 ${validFiles.length} 个文件`)
  }
}

// 移除文件
const removeFile = (index: number) => {
  const removedFile = fileList.value[index]
  fileList.value.splice(index, 1)
  emit('remove', removedFile, index)
}

// 清空文件
const clearFiles = () => {
  fileList.value = []
  description.value = ''
  emit('clear')
}

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 获取文件类型图标
const getFileTypeIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    '.jpg': 'Picture',
    '.jpeg': 'Picture',
    '.png': 'Picture',
    '.gif': 'Picture',
    '.bmp': 'Picture',
    '.webp': 'Picture',
    '.pdf': 'Document',
    '.doc': 'Document',
    '.docx': 'Document',
    '.txt': 'Document',
    '.md': 'Document',
    '.json': 'DocumentCopy',
    '.yaml': 'DocumentCopy',
    '.yml': 'DocumentCopy',
    '.sql': 'Coin',
    '.db': 'Coin',
    '.sqlite': 'Coin',
    '.mp4': 'VideoCamera',
    '.avi': 'VideoCamera',
    '.mov': 'VideoCamera',
    '.wmv': 'VideoCamera',
    '.flv': 'VideoCamera',
    '.webm': 'VideoCamera'
  }
  return iconMap[type] || 'Document'
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

// 暴露方法给父组件
defineExpose({
  clearFiles,
  getFiles: () => fileList.value,
  getDescription: () => description.value
})
</script>

<style lang="scss" scoped>
.file-upload-container {
  .upload-area {
    border: 2px dashed var(--el-border-color);
    border-radius: 8px;
    padding: 40px 20px;
    text-align: center;
    transition: all 0.3s ease;
    cursor: pointer;
    background-color: var(--el-fill-color-extra-light);
    
    &:hover:not(.is-disabled) {
      border-color: var(--el-color-primary);
      background-color: var(--el-color-primary-light-9);
    }
    
    &.is-dragover {
      border-color: var(--el-color-primary);
      background-color: var(--el-color-primary-light-8);
    }
    
    &.is-disabled {
      cursor: not-allowed;
      opacity: 0.6;
    }
    
    .upload-content {
      .upload-icon {
        margin-bottom: 16px;
      }
      
      .upload-text {
        margin-bottom: 16px;
        
        .upload-title {
          font-size: 16px;
          color: var(--el-text-color-primary);
          margin-bottom: 8px;
        }
        
        .upload-subtitle {
          font-size: 14px;
          color: var(--el-text-color-regular);
        }
      }
      
      .supported-formats {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 8px;
      }
    }
  }
  
  .file-list {
    margin-top: 20px;
    
    .file-list-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      font-size: 14px;
      color: var(--el-text-color-regular);
    }
    
    .file-items {
      .file-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px;
        border: 1px solid var(--el-border-color-light);
        border-radius: 6px;
        margin-bottom: 8px;
        background-color: var(--el-fill-color-extra-light);
        
        .file-info {
          display: flex;
          align-items: center;
          flex: 1;
          min-width: 0;
          
          .file-icon {
            margin-right: 12px;
            flex-shrink: 0;
          }
          
          .file-details {
            flex: 1;
            min-width: 0;
            
            .file-name {
              font-size: 14px;
              color: var(--el-text-color-primary);
              margin-bottom: 4px;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            }
            
            .file-meta {
              font-size: 12px;
              color: var(--el-text-color-regular);
              display: flex;
              gap: 12px;
              
              .recommended-agent {
                color: var(--el-color-primary);
              }
            }
          }
        }
        
        .file-actions {
          flex-shrink: 0;
        }
      }
    }
  }
  
  .file-description {
    margin-top: 16px;
  }
}
</style>
