<template>
  <el-dialog
    v-model="visible"
    title="导出思维导图"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="export-options">
      <el-form
        ref="formRef"
        :model="exportConfig"
        label-width="100px"
        class="export-form"
      >
        <el-form-item label="导出格式" required>
          <el-radio-group v-model="exportConfig.format">
            <el-radio label="png">PNG 图片</el-radio>
            <el-radio label="svg">SVG 矢量图</el-radio>
            <el-radio label="pdf">PDF 文档</el-radio>
            <el-radio label="json">JSON 数据</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="isImageFormat" label="图片质量">
          <el-slider
            v-model="exportConfig.quality"
            :min="0.1"
            :max="1"
            :step="0.1"
            show-tooltip
            :format-tooltip="formatQualityTooltip"
          />
        </el-form-item>

        <el-form-item v-if="isImageFormat" label="图片尺寸">
          <el-radio-group v-model="exportConfig.size">
            <el-radio label="original">原始尺寸</el-radio>
            <el-radio label="2x">2倍尺寸</el-radio>
            <el-radio label="custom">自定义</el-radio>
          </el-radio-group>
          
          <div v-if="exportConfig.size === 'custom'" class="custom-size">
            <el-input-number
              v-model="exportConfig.width"
              :min="100"
              :max="5000"
              placeholder="宽度"
              style="width: 120px"
            />
            <span class="size-separator">×</span>
            <el-input-number
              v-model="exportConfig.height"
              :min="100"
              :max="5000"
              placeholder="高度"
              style="width: 120px"
            />
          </div>
        </el-form-item>

        <el-form-item label="包含内容">
          <el-checkbox-group v-model="exportConfig.includes">
            <el-checkbox label="title">标题</el-checkbox>
            <el-checkbox label="description">描述</el-checkbox>
            <el-checkbox label="steps">测试步骤</el-checkbox>
            <el-checkbox label="tags">标签</el-checkbox>
            <el-checkbox label="metadata">元数据</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item v-if="exportConfig.format === 'pdf'" label="页面设置">
          <el-select v-model="exportConfig.pageSize" style="width: 150px">
            <el-option label="A4" value="a4" />
            <el-option label="A3" value="a3" />
            <el-option label="Letter" value="letter" />
            <el-option label="Legal" value="legal" />
          </el-select>
          
          <el-select v-model="exportConfig.orientation" style="width: 100px; margin-left: 12px">
            <el-option label="竖向" value="portrait" />
            <el-option label="横向" value="landscape" />
          </el-select>
        </el-form-item>

        <el-form-item label="文件名">
          <el-input
            v-model="exportConfig.filename"
            placeholder="请输入文件名"
            :suffix="`.${exportConfig.format}`"
          />
        </el-form-item>
      </el-form>

      <!-- 预览区域 -->
      <div v-if="showPreview" class="preview-section">
        <div class="preview-header">
          <span>预览</span>
          <el-button type="text" size="small" @click="togglePreview">
            {{ showPreview ? '隐藏' : '显示' }}预览
          </el-button>
        </div>
        
        <div class="preview-content">
          <div class="preview-placeholder">
            <el-icon size="48" color="#C0C4CC">
              <Picture />
            </el-icon>
            <p>预览功能开发中...</p>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleExport" :loading="exporting">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'

interface Props {
  modelValue: boolean
  mindmapData: any
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'export', format: string, options: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref()
const exporting = ref(false)
const showPreview = ref(false)

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 导出配置
const exportConfig = reactive({
  format: 'png',
  quality: 0.9,
  size: 'original',
  width: 1200,
  height: 800,
  includes: ['title', 'description', 'steps', 'tags'],
  pageSize: 'a4',
  orientation: 'landscape',
  filename: 'mindmap'
})

// 计算属性
const isImageFormat = computed(() => {
  return ['png', 'svg'].includes(exportConfig.format)
})

// 监听格式变化，自动调整文件名
watch(() => exportConfig.format, (newFormat) => {
  if (exportConfig.filename && !exportConfig.filename.includes('.')) {
    // 如果文件名没有扩展名，保持原样
    return
  }
  
  // 更新文件名扩展名
  const baseName = exportConfig.filename.replace(/\.[^/.]+$/, '')
  exportConfig.filename = baseName || 'mindmap'
})

// 格式化质量提示
const formatQualityTooltip = (value: number) => {
  return `${Math.round(value * 100)}%`
}

// 切换预览
const togglePreview = () => {
  showPreview.value = !showPreview.value
}

// 导出处理
const handleExport = async () => {
  if (!props.mindmapData) {
    ElMessage.warning('没有可导出的数据')
    return
  }

  if (!exportConfig.filename.trim()) {
    ElMessage.warning('请输入文件名')
    return
  }

  try {
    exporting.value = true

    // 构建导出选项
    const options = {
      ...exportConfig,
      data: props.mindmapData
    }

    // 根据格式执行不同的导出逻辑
    switch (exportConfig.format) {
      case 'png':
        await exportAsPNG(options)
        break
      case 'svg':
        await exportAsSVG(options)
        break
      case 'pdf':
        await exportAsPDF(options)
        break
      case 'json':
        await exportAsJSON(options)
        break
      default:
        throw new Error('不支持的导出格式')
    }

    emit('export', exportConfig.format, options)
    ElMessage.success('导出成功')
    handleClose()

  } catch (error: any) {
    console.error('导出失败:', error)
    ElMessage.error(error.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

// PNG导出
const exportAsPNG = async (options: any) => {
  // 这里实现PNG导出逻辑
  // 可以使用html2canvas或类似库
  console.log('导出PNG:', options)
  
  // 模拟导出过程
  await new Promise(resolve => setTimeout(resolve, 1000))
}

// SVG导出
const exportAsSVG = async (options: any) => {
  // 这里实现SVG导出逻辑
  console.log('导出SVG:', options)
  
  // 模拟导出过程
  await new Promise(resolve => setTimeout(resolve, 1000))
}

// PDF导出
const exportAsPDF = async (options: any) => {
  // 这里实现PDF导出逻辑
  // 可以使用jsPDF或类似库
  console.log('导出PDF:', options)
  
  // 模拟导出过程
  await new Promise(resolve => setTimeout(resolve, 1500))
}

// JSON导出
const exportAsJSON = async (options: any) => {
  const jsonData = JSON.stringify(options.data, null, 2)
  const blob = new Blob([jsonData], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  
  const link = document.createElement('a')
  link.href = url
  link.download = `${options.filename}.json`
  link.click()
  
  URL.revokeObjectURL(url)
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  showPreview.value = false
}

// 重置配置
const resetConfig = () => {
  Object.assign(exportConfig, {
    format: 'png',
    quality: 0.9,
    size: 'original',
    width: 1200,
    height: 800,
    includes: ['title', 'description', 'steps', 'tags'],
    pageSize: 'a4',
    orientation: 'landscape',
    filename: 'mindmap'
  })
}

// 监听对话框打开
watch(visible, (newVisible) => {
  if (newVisible) {
    resetConfig()
  }
})
</script>

<style lang="scss" scoped>
.export-options {
  .export-form {
    .custom-size {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 8px;
      
      .size-separator {
        color: var(--el-text-color-regular);
      }
    }
  }
  
  .preview-section {
    margin-top: 24px;
    border-top: 1px solid var(--el-border-color-light);
    padding-top: 16px;
    
    .preview-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      
      span {
        font-weight: 500;
        color: var(--el-text-color-primary);
      }
    }
    
    .preview-content {
      border: 1px solid var(--el-border-color-light);
      border-radius: 6px;
      height: 200px;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: var(--el-fill-color-extra-light);
      
      .preview-placeholder {
        text-align: center;
        color: var(--el-text-color-placeholder);
        
        p {
          margin-top: 8px;
          font-size: 14px;
        }
      }
    }
  }
}

.dialog-footer {
  text-align: right;
  
  .el-button {
    margin-left: 12px;
  }
}
</style>
