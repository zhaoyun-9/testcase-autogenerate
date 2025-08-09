<template>
  <el-card
    :class="[
      'tc-card',
      {
        'tc-card--loading': loading,
        'tc-card--bordered': bordered,
        'tc-card--hoverable': hoverable,
        'tc-card--glass': glass,
        'tc-card--gradient': gradient
      }
    ]"
    :shadow="shadow"
    :body-style="computedBodyStyle"
    :header-style="computedHeaderStyle"
  >
    <template v-if="$slots.header || title || subtitle || $slots.extra" #header>
      <div class="tc-card__header">
        <div class="tc-card__header-content">
          <slot name="header">
            <div v-if="title || subtitle" class="tc-card__title-wrapper">
              <h3 v-if="title" class="tc-card__title">{{ title }}</h3>
              <p v-if="subtitle" class="tc-card__subtitle">{{ subtitle }}</p>
            </div>
          </slot>
        </div>
        <div v-if="$slots.extra" class="tc-card__header-extra">
          <slot name="extra" />
        </div>
      </div>
    </template>

    <div class="tc-card__body">
      <div v-if="loading" class="tc-card__loading">
        <el-skeleton :rows="skeletonRows" animated />
      </div>
      <div v-else class="tc-card__content">
        <slot />
      </div>
    </div>

    <template v-if="$slots.footer" #footer>
      <div class="tc-card__footer">
        <slot name="footer" />
      </div>
    </template>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CardProps } from '../types'

interface TcCardProps extends CardProps {
  hoverable?: boolean
  glass?: boolean
  gradient?: boolean
  skeletonRows?: number
}

const props = withDefaults(defineProps<TcCardProps>(), {
  shadow: 'hover',
  loading: false,
  bordered: true,
  hoverable: false,
  glass: false,
  gradient: false,
  skeletonRows: 3
})

const computedBodyStyle = computed(() => {
  const defaultStyle = {
    padding: 'var(--spacing-lg)'
  }
  return { ...defaultStyle, ...props.bodyStyle }
})

const computedHeaderStyle = computed(() => {
  const defaultStyle = {
    padding: 'var(--spacing-lg)',
    borderBottom: '1px solid var(--border-color-light)',
    background: 'var(--bg-secondary)'
  }
  return { ...defaultStyle, ...props.headerStyle }
})
</script>

<style lang="scss" scoped>
.tc-card {
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  transition: all var(--transition-normal);
  overflow: hidden;
  
  // 悬停效果
  &--hoverable {
    cursor: pointer;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-lg);
    }
  }
  
  // 边框样式
  &--bordered {
    border: 1px solid var(--border-color);
  }
  
  // 玻璃态效果
  &--glass {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  }
  
  // 渐变背景
  &--gradient {
    background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
  }
  
  // 加载状态
  &--loading {
    .tc-card__content {
      opacity: 0.5;
    }
  }
  
  // 头部样式
  .tc-card__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--spacing-md);
    
    .tc-card__header-content {
      flex: 1;
      min-width: 0;
    }
    
    .tc-card__header-extra {
      flex-shrink: 0;
    }
    
    .tc-card__title-wrapper {
      .tc-card__title {
        font-size: var(--font-size-lg);
        font-weight: var(--font-weight-semibold);
        color: var(--text-primary);
        margin: 0 0 var(--spacing-xs) 0;
        line-height: var(--line-height-tight);
      }
      
      .tc-card__subtitle {
        font-size: var(--font-size-sm);
        color: var(--text-secondary);
        margin: 0;
        line-height: var(--line-height-normal);
      }
    }
  }
  
  // 主体样式
  .tc-card__body {
    position: relative;
    
    .tc-card__loading {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 1;
      background: rgba(255, 255, 255, 0.8);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: var(--spacing-lg);
    }
    
    .tc-card__content {
      transition: opacity var(--transition-normal);
    }
  }
  
  // 底部样式
  .tc-card__footer {
    padding: var(--spacing-lg);
    border-top: 1px solid var(--border-color-light);
    background: var(--bg-secondary);
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: var(--spacing-md);
  }
}

// Element Plus 样式覆盖
:deep(.el-card__header) {
  padding: 0;
  border-bottom: none;
  background: transparent;
}

:deep(.el-card__body) {
  padding: 0;
}

// 响应式设计
@media (max-width: 768px) {
  .tc-card {
    .tc-card__header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--spacing-sm);
      
      .tc-card__header-extra {
        width: 100%;
        display: flex;
        justify-content: flex-end;
      }
    }
  }
}

// 特殊卡片样式
.tc-card {
  // 成功状态卡片
  &.tc-card--success {
    border-left: 4px solid var(--success-color);
    
    .tc-card__title {
      color: var(--success-color);
    }
  }
  
  // 警告状态卡片
  &.tc-card--warning {
    border-left: 4px solid var(--warning-color);
    
    .tc-card__title {
      color: var(--warning-color);
    }
  }
  
  // 错误状态卡片
  &.tc-card--error {
    border-left: 4px solid var(--error-color);
    
    .tc-card__title {
      color: var(--error-color);
    }
  }
  
  // 信息状态卡片
  &.tc-card--info {
    border-left: 4px solid var(--info-color);
    
    .tc-card__title {
      color: var(--info-color);
    }
  }
}

// 卡片组合样式
.tc-card-group {
  display: grid;
  gap: var(--spacing-lg);
  
  &.tc-card-group--cols-2 {
    grid-template-columns: repeat(2, 1fr);
  }
  
  &.tc-card-group--cols-3 {
    grid-template-columns: repeat(3, 1fr);
  }
  
  &.tc-card-group--cols-4 {
    grid-template-columns: repeat(4, 1fr);
  }
  
  @media (max-width: 1200px) {
    &.tc-card-group--cols-4 {
      grid-template-columns: repeat(3, 1fr);
    }
  }
  
  @media (max-width: 768px) {
    &.tc-card-group--cols-3,
    &.tc-card-group--cols-4 {
      grid-template-columns: repeat(2, 1fr);
    }
  }
  
  @media (max-width: 480px) {
    &.tc-card-group--cols-2,
    &.tc-card-group--cols-3,
    &.tc-card-group--cols-4 {
      grid-template-columns: 1fr;
    }
  }
}
</style>
