<template>
  <div class="tc-page-header">
    <!-- 背景装饰 -->
    <div class="tc-page-header__background">
      <div class="decoration-circle decoration-circle--1"></div>
      <div class="decoration-circle decoration-circle--2"></div>
      <div class="decoration-circle decoration-circle--3"></div>
    </div>

    <!-- 主要内容 -->
    <div class="tc-page-header__content">
      <!-- 左侧内容 -->
      <div class="tc-page-header__main">
        <!-- 返回按钮 -->
        <el-button
          v-if="showBack"
          type="text"
          :icon="ArrowLeft"
          class="tc-page-header__back"
          @click="handleBack"
        >
          返回
        </el-button>

        <!-- 面包屑导航 -->
        <el-breadcrumb
          v-if="breadcrumb && breadcrumb.length > 0"
          class="tc-page-header__breadcrumb"
          separator="/"
        >
          <el-breadcrumb-item
            v-for="(item, index) in breadcrumb"
            :key="index"
            :to="item.to"
          >
            {{ item.label }}
          </el-breadcrumb-item>
        </el-breadcrumb>

        <!-- 标题区域 -->
        <div class="tc-page-header__title-wrapper">
          <h1 class="tc-page-header__title gradient-text">
            <slot name="title">{{ title }}</slot>
          </h1>
          <p v-if="subtitle || $slots.subtitle" class="tc-page-header__subtitle">
            <slot name="subtitle">{{ subtitle }}</slot>
          </p>
        </div>

        <!-- 标签页 -->
        <el-tabs
          v-if="tabs && tabs.length > 0"
          v-model="activeTabValue"
          class="tc-page-header__tabs"
          @tab-change="handleTabChange"
        >
          <el-tab-pane
            v-for="tab in tabs"
            :key="tab.value"
            :label="tab.label"
            :name="tab.value"
            :disabled="tab.disabled"
          />
        </el-tabs>
      </div>

      <!-- 右侧操作区域 -->
      <div v-if="actions && actions.length > 0 || $slots.actions" class="tc-page-header__actions">
        <slot name="actions">
          <template v-for="(action, index) in actions" :key="index">
            <el-button
              v-if="action.type === 'button'"
              :type="action.buttonType || 'primary'"
              :size="action.size || 'default'"
              :icon="action.icon"
              :loading="action.loading"
              :disabled="action.disabled"
              @click="action.handler"
            >
              {{ action.label }}
            </el-button>
            
            <el-dropdown
              v-else-if="action.type === 'dropdown'"
              @command="action.handler"
            >
              <el-button
                :type="action.buttonType || 'default'"
                :size="action.size || 'default'"
                :icon="action.icon"
              >
                {{ action.label }}
                <el-icon class="el-icon--right">
                  <ArrowDown />
                </el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    v-for="(item, itemIndex) in action.items"
                    :key="itemIndex"
                    :command="item.command"
                    :disabled="item.disabled"
                    :divided="item.divided"
                  >
                    <el-icon v-if="item.icon">
                      <component :is="item.icon" />
                    </el-icon>
                    {{ item.label }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </slot>
      </div>
    </div>

    <!-- 额外内容插槽 -->
    <div v-if="$slots.extra" class="tc-page-header__extra">
      <slot name="extra" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, ArrowDown } from '@element-plus/icons-vue'
import type { PageHeaderProps } from '../types'

interface ActionItem {
  type: 'button' | 'dropdown'
  label: string
  buttonType?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'text'
  size?: 'large' | 'default' | 'small'
  icon?: any
  loading?: boolean
  disabled?: boolean
  handler: (command?: any) => void
  items?: {
    label: string
    command: any
    icon?: any
    disabled?: boolean
    divided?: boolean
  }[]
}

interface TcPageHeaderProps extends PageHeaderProps {
  actions?: ActionItem[]
}

interface TcPageHeaderEmits {
  (e: 'back'): void
  (e: 'tab-change', value: string): void
}

const props = withDefaults(defineProps<TcPageHeaderProps>(), {
  showBack: false
})

const emit = defineEmits<TcPageHeaderEmits>()

const router = useRouter()

// 当前激活的标签页
const activeTabValue = ref(props.activeTab || (props.tabs?.[0]?.value || ''))

// 监听 activeTab 属性变化
watch(() => props.activeTab, (newValue) => {
  if (newValue) {
    activeTabValue.value = newValue
  }
})

// 处理返回按钮点击
const handleBack = () => {
  emit('back')
  // 如果没有监听 back 事件，则默认使用路由返回
  if (!emit('back')) {
    router.back()
  }
}

// 处理标签页切换
const handleTabChange = (value: string) => {
  activeTabValue.value = value
  emit('tab-change', value)
}
</script>

<style lang="scss" scoped>
.tc-page-header {
  position: relative;
  margin-bottom: var(--spacing-2xl);
  padding: var(--spacing-2xl) var(--spacing-xl);
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-lg);
  overflow: hidden;

  // 背景装饰
  &__background {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
    z-index: 0;

    .decoration-circle {
      position: absolute;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
      opacity: 0.1;
      animation: pulse 3s ease-in-out infinite;

      &--1 {
        width: 120px;
        height: 120px;
        top: -60px;
        right: -60px;
        animation-delay: 0s;
      }

      &--2 {
        width: 80px;
        height: 80px;
        top: 20px;
        right: 100px;
        animation-delay: 1s;
      }

      &--3 {
        width: 60px;
        height: 60px;
        bottom: -30px;
        right: 50px;
        animation-delay: 2s;
      }
    }
  }

  // 主要内容
  &__content {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--spacing-xl);
  }

  // 左侧主要内容
  &__main {
    flex: 1;
    min-width: 0;
  }

  // 返回按钮
  &__back {
    margin-bottom: var(--spacing-md);
    color: var(--text-secondary);
    
    &:hover {
      color: var(--primary-color);
    }
  }

  // 面包屑导航
  &__breadcrumb {
    margin-bottom: var(--spacing-lg);
    
    :deep(.el-breadcrumb__item) {
      .el-breadcrumb__inner {
        color: var(--text-secondary);
        font-weight: var(--font-weight-normal);
        
        &:hover {
          color: var(--primary-color);
        }
      }
      
      &:last-child .el-breadcrumb__inner {
        color: var(--text-primary);
        font-weight: var(--font-weight-medium);
      }
    }
  }

  // 标题区域
  &__title-wrapper {
    margin-bottom: var(--spacing-lg);
  }

  &__title {
    font-size: var(--font-size-3xl);
    font-weight: var(--font-weight-bold);
    margin: 0 0 var(--spacing-sm) 0;
    line-height: var(--line-height-tight);
  }

  &__subtitle {
    font-size: var(--font-size-base);
    color: var(--text-secondary);
    margin: 0;
    line-height: var(--line-height-normal);
    max-width: 600px;
  }

  // 标签页
  &__tabs {
    :deep(.el-tabs__header) {
      margin: 0;
      border-bottom: 1px solid var(--border-color-light);
    }
    
    :deep(.el-tabs__nav-wrap) {
      &::after {
        display: none;
      }
    }
    
    :deep(.el-tabs__item) {
      padding: var(--spacing-md) var(--spacing-lg);
      font-weight: var(--font-weight-medium);
      color: var(--text-secondary);
      border-radius: var(--border-radius) var(--border-radius) 0 0;
      transition: all var(--transition-normal);
      
      &:hover {
        color: var(--primary-color);
        background: rgba(37, 99, 235, 0.05);
      }
      
      &.is-active {
        color: var(--primary-color);
        background: var(--bg-primary);
        border-bottom: 2px solid var(--primary-color);
      }
    }
  }

  // 右侧操作区域
  &__actions {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    flex-shrink: 0;
  }

  // 额外内容
  &__extra {
    position: relative;
    z-index: 1;
    margin-top: var(--spacing-xl);
    padding-top: var(--spacing-xl);
    border-top: 1px solid var(--border-color-light);
  }
}

// 动画效果
@keyframes pulse {
  0%, 100% {
    opacity: 0.1;
    transform: scale(1);
  }
  50% {
    opacity: 0.2;
    transform: scale(1.1);
  }
}

// 渐变文字效果
.gradient-text {
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

// 响应式设计
@media (max-width: 768px) {
  .tc-page-header {
    padding: var(--spacing-lg);
    
    &__content {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-lg);
    }
    
    &__title {
      font-size: var(--font-size-2xl);
    }
    
    &__actions {
      justify-content: flex-end;
    }
  }
}

@media (max-width: 480px) {
  .tc-page-header {
    &__actions {
      flex-direction: column;
      align-items: stretch;
      
      .el-button {
        width: 100%;
      }
    }
  }
}
</style>
