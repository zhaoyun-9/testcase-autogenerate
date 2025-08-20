<template>
  <div class="mindmap-list">
    <div class="page-header">
      <h1>思维导图管理</h1>
      <p>创建和管理您的思维导图</p>
    </div>

    <div class="action-bar">
      <el-button type="primary" @click="createNewMindmap">
        <el-icon><Plus /></el-icon>
        创建思维导图
      </el-button>
    </div>

    <div class="mindmap-grid">
      <div 
        v-for="mindmap in mindmaps" 
        :key="mindmap.id"
        class="mindmap-card"
        @click="openMindmap(mindmap)"
      >
        <div class="card-header">
          <h3>{{ mindmap.title }}</h3>
          <div class="card-actions">
            <el-button size="small" text @click.stop="editMindmap(mindmap)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button size="small" text type="danger" @click.stop="deleteMindmap(mindmap)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
        
        <div class="card-preview">
          <div class="preview-placeholder">
            <el-icon><Share /></el-icon>
            <span>{{ mindmap.nodeCount }} 个节点</span>
          </div>
        </div>
        
        <div class="card-footer">
          <span class="update-time">{{ formatTime(mindmap.updatedAt) }}</span>
          <el-tag size="small" :type="getStatusType(mindmap.status)">
            {{ mindmap.status }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEditing ? '编辑思维导图' : '创建思维导图'"
      width="500px"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="请输入思维导图标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入描述（可选）" 
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveMindmap">
          {{ isEditing ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Share } from '@element-plus/icons-vue'

const router = useRouter()

// 响应式数据
const mindmaps = ref([
  {
    id: 1,
    title: '财会速度V4.47.0项目',
    description: '财会速度平台代办中审对接企业一期项目思维导图',
    nodeCount: 15,
    status: '进行中',
    updatedAt: new Date(),
    data: {
      mind_map_data: {
        id: 'center',
        label: '财会速度V4.47.0 平台代办中审对接企业一期',
        type: 'center',
        level: 0,
        children: [
          {
            id: 'version',
            label: '版本说明',
            type: 'branch',
            level: 1,
            side: 'left',
            children: []
          },
          {
            id: 'docs',
            label: '文档记录',
            type: 'branch',
            level: 1,
            side: 'left',
            children: []
          },
          {
            id: 'natural-person',
            label: '自然人信息',
            type: 'branch',
            level: 1,
            side: 'right',
            children: [
              {
                id: 'person-interface',
                label: '对接示企接口',
                type: 'leaf',
                level: 2,
                children: [
                  {
                    id: 'person-query',
                    label: '自然人查档(明细)',
                    type: 'leaf',
                    level: 3,
                    children: []
                  }
                ]
              }
            ]
          },
          {
            id: 'project-mgmt',
            label: '项目管理',
            type: 'branch',
            level: 1,
            side: 'right',
            children: [
              {
                id: 'page',
                label: '页面',
                type: 'leaf',
                level: 2,
                children: []
              }
            ]
          }
        ]
      }
    }
  },
  {
    id: 2,
    title: '项目管理系统',
    description: '通用项目管理系统架构设计',
    nodeCount: 8,
    status: '已完成',
    updatedAt: new Date(Date.now() - 86400000),
    data: {
      mind_map_data: {
        id: 'center',
        label: '项目管理系统',
        type: 'center',
        level: 0,
        children: [
          {
            id: 'planning',
            label: '项目规划',
            type: 'branch',
            level: 1,
            side: 'left',
            children: []
          },
          {
            id: 'development',
            label: '开发阶段',
            type: 'branch',
            level: 1,
            side: 'right',
            children: []
          }
        ]
      }
    }
  }
])

const dialogVisible = ref(false)
const isEditing = ref(false)
const currentMindmap = ref<any>(null)

const form = ref({
  title: '',
  description: ''
})

// 方法
const createNewMindmap = () => {
  isEditing.value = false
  form.value = { title: '', description: '' }
  dialogVisible.value = true
}

const editMindmap = (mindmap: any) => {
  isEditing.value = true
  currentMindmap.value = mindmap
  form.value = {
    title: mindmap.title,
    description: mindmap.description
  }
  dialogVisible.value = true
}

const saveMindmap = () => {
  if (!form.value.title.trim()) {
    ElMessage.warning('请输入思维导图标题')
    return
  }

  if (isEditing.value && currentMindmap.value) {
    // 编辑现有思维导图
    currentMindmap.value.title = form.value.title
    currentMindmap.value.description = form.value.description
    currentMindmap.value.updatedAt = new Date()
    ElMessage.success('思维导图已更新')
  } else {
    // 创建新思维导图
    const newMindmap = {
      id: Date.now(),
      title: form.value.title,
      description: form.value.description,
      nodeCount: 1,
      status: '草稿',
      updatedAt: new Date(),
      data: {
        mind_map_data: {
          id: 'center',
          label: form.value.title,
          type: 'center',
          level: 0,
          children: []
        }
      }
    }
    mindmaps.value.unshift(newMindmap)
    ElMessage.success('思维导图已创建')
  }

  dialogVisible.value = false
}

const deleteMindmap = async (mindmap: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除思维导图"${mindmap.title}"吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const index = mindmaps.value.findIndex(m => m.id === mindmap.id)
    if (index > -1) {
      mindmaps.value.splice(index, 1)
      ElMessage.success('思维导图已删除')
    }
  } catch {
    // 用户取消删除
  }
}

const openMindmap = (mindmap: any) => {
  // 将数据存储到 sessionStorage 中，然后跳转
  sessionStorage.setItem(`mindmap_${mindmap.id}`, JSON.stringify(mindmap.data))

  router.push({
    name: 'MindmapDetail',
    params: { id: mindmap.id.toString() }
  })
}

const formatTime = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) {
    return '今天'
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString()
  }
}

const getStatusType = (status: string) => {
  switch (status) {
    case '进行中': return 'primary'
    case '已完成': return 'success'
    case '草稿': return 'info'
    default: return 'info'
  }
}

onMounted(() => {
  // 组件挂载时的初始化逻辑
})
</script>

<style lang="scss" scoped>
.mindmap-list {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100vh;

  .page-header {
    margin-bottom: 24px;

    h1 {
      margin: 0 0 8px 0;
      font-size: 28px;
      font-weight: 600;
      color: #1f2937;
    }

    p {
      margin: 0;
      color: #6b7280;
      font-size: 16px;
    }
  }

  .action-bar {
    margin-bottom: 24px;
    display: flex;
    justify-content: flex-start;
  }

  .mindmap-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 20px;

    .mindmap-card {
      background: white;
      border-radius: 12px;
      padding: 20px;
      cursor: pointer;
      transition: all 0.3s ease;
      border: 1px solid #e5e7eb;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        border-color: #3b82f6;
      }

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 16px;

        h3 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
          color: #1f2937;
          flex: 1;
          line-height: 1.4;
        }

        .card-actions {
          display: flex;
          gap: 4px;
          opacity: 0;
          transition: opacity 0.2s ease;
        }
      }

      &:hover .card-actions {
        opacity: 1;
      }

      .card-preview {
        margin-bottom: 16px;
        height: 80px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f9fafb;
        border-radius: 8px;
        border: 2px dashed #d1d5db;

        .preview-placeholder {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          color: #6b7280;

          .el-icon {
            font-size: 24px;
          }

          span {
            font-size: 14px;
          }
        }
      }

      .card-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .update-time {
          font-size: 14px;
          color: #6b7280;
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .mindmap-list {
    padding: 16px;

    .mindmap-grid {
      grid-template-columns: 1fr;
    }
  }
}
</style>
