<template>
  <el-button
    :class="[
      'tc-button',
      `tc-button--${type}`,
      `tc-button--${size}`,
      {
        'tc-button--loading': loading,
        'tc-button--disabled': disabled,
        'tc-button--round': round,
        'tc-button--circle': circle,
        'tc-button--plain': plain,
        'tc-button--text': text,
        'tc-button--link': link,
        'tc-button--gradient': gradient,
        'tc-button--shadow': shadow
      }
    ]"
    :type="type"
    :size="size"
    :loading="loading"
    :disabled="disabled"
    :round="round"
    :circle="circle"
    :plain="plain"
    :text="text"
    :link="link"
    :icon="icon"
    :autofocus="autofocus"
    :native-type="nativeType"
    @click="handleClick"
    @focus="handleFocus"
    @blur="handleBlur"
  >
    <template v-if="$slots.icon" #icon>
      <slot name="icon" />
    </template>
    
    <slot />
    
    <template v-if="$slots.loading" #loading>
      <slot name="loading" />
    </template>
  </el-button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ButtonProps } from '../types'

interface TcButtonProps extends ButtonProps {
  gradient?: boolean
  shadow?: boolean
  autofocus?: boolean
  nativeType?: 'button' | 'submit' | 'reset'
}

interface TcButtonEmits {
  (e: 'click', event: MouseEvent): void
  (e: 'focus', event: FocusEvent): void
  (e: 'blur', event: FocusEvent): void
}

const props = withDefaults(defineProps<TcButtonProps>(), {
  type: 'primary',
  size: 'default',
  loading: false,
  disabled: false,
  round: false,
  circle: false,
  plain: false,
  text: false,
  link: false,
  gradient: false,
  shadow: true,
  autofocus: false,
  nativeType: 'button'
})

const emit = defineEmits<TcButtonEmits>()

const handleClick = (event: MouseEvent) => {
  if (!props.loading && !props.disabled) {
    emit('click', event)
  }
}

const handleFocus = (event: FocusEvent) => {
  emit('focus', event)
}

const handleBlur = (event: FocusEvent) => {
  emit('blur', event)
}
</script>

<style lang="scss" scoped>
.tc-button {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
  font-weight: var(--font-weight-medium);
  border-radius: var(--border-radius);
  transition: all var(--transition-normal);
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  outline: none;
  
  // 尺寸变体
  &--small {
    padding: var(--spacing-xs) var(--spacing-md);
    font-size: var(--font-size-sm);
    min-height: 28px;
  }
  
  &--default {
    padding: var(--spacing-sm) var(--spacing-lg);
    font-size: var(--font-size-base);
    min-height: 32px;
  }
  
  &--large {
    padding: var(--spacing-md) var(--spacing-xl);
    font-size: var(--font-size-lg);
    min-height: 40px;
  }
  
  // 类型变体
  &--primary {
    background: var(--primary-color);
    border-color: var(--primary-color);
    color: var(--text-inverse);
    
    &:hover:not(.tc-button--disabled) {
      background: var(--primary-light);
      border-color: var(--primary-light);
      transform: translateY(-1px);
    }
    
    &:active:not(.tc-button--disabled) {
      background: var(--primary-dark);
      border-color: var(--primary-dark);
      transform: translateY(0);
    }
    
    &.tc-button--gradient {
      background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-light) 100%);
      border: none;
      
      &:hover:not(.tc-button--disabled) {
        background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary-color) 100%);
      }
    }
  }
  
  &--success {
    background: var(--success-color);
    border-color: var(--success-color);
    color: var(--text-inverse);
    
    &:hover:not(.tc-button--disabled) {
      opacity: 0.8;
      transform: translateY(-1px);
    }
  }
  
  &--warning {
    background: var(--warning-color);
    border-color: var(--warning-color);
    color: var(--text-inverse);
    
    &:hover:not(.tc-button--disabled) {
      opacity: 0.8;
      transform: translateY(-1px);
    }
  }
  
  &--danger {
    background: var(--error-color);
    border-color: var(--error-color);
    color: var(--text-inverse);
    
    &:hover:not(.tc-button--disabled) {
      opacity: 0.8;
      transform: translateY(-1px);
    }
  }
  
  &--info {
    background: var(--info-color);
    border-color: var(--info-color);
    color: var(--text-inverse);
    
    &:hover:not(.tc-button--disabled) {
      opacity: 0.8;
      transform: translateY(-1px);
    }
  }
  
  // 状态变体
  &--loading {
    cursor: not-allowed;
    opacity: 0.6;
    
    &:hover {
      transform: none !important;
    }
  }
  
  &--disabled {
    cursor: not-allowed;
    opacity: 0.5;
    
    &:hover {
      transform: none !important;
    }
  }
  
  // 形状变体
  &--round {
    border-radius: var(--border-radius-full);
  }
  
  &--circle {
    border-radius: 50%;
    width: 32px;
    height: 32px;
    padding: 0;
    
    &.tc-button--small {
      width: 28px;
      height: 28px;
    }
    
    &.tc-button--large {
      width: 40px;
      height: 40px;
    }
  }
  
  // 样式变体
  &--plain {
    background: transparent;
    
    &.tc-button--primary {
      color: var(--primary-color);
      border-color: var(--primary-color);
      
      &:hover:not(.tc-button--disabled) {
        background: var(--primary-color);
        color: var(--text-inverse);
      }
    }
  }
  
  &--text {
    background: transparent;
    border: none;
    padding: var(--spacing-xs) var(--spacing-sm);
    
    &.tc-button--primary {
      color: var(--primary-color);
      
      &:hover:not(.tc-button--disabled) {
        background: rgba(37, 99, 235, 0.1);
      }
    }
  }
  
  &--link {
    background: transparent;
    border: none;
    padding: 0;
    text-decoration: underline;
    
    &:hover:not(.tc-button--disabled) {
      opacity: 0.8;
    }
  }
  
  // 阴影效果
  &--shadow {
    box-shadow: var(--shadow-sm);
    
    &:hover:not(.tc-button--disabled):not(.tc-button--text):not(.tc-button--link) {
      box-shadow: var(--shadow-md);
    }
    
    &:active:not(.tc-button--disabled) {
      box-shadow: var(--shadow-xs);
    }
  }
  
  // 焦点样式
  &:focus-visible {
    outline: 2px solid var(--primary-color);
    outline-offset: 2px;
  }
  
  // 图标间距
  .el-icon {
    margin-right: var(--spacing-xs);
    
    &:last-child {
      margin-right: 0;
      margin-left: var(--spacing-xs);
    }
    
    &:only-child {
      margin: 0;
    }
  }
}

// 按钮组样式
.el-button-group {
  .tc-button {
    &:not(:first-child) {
      margin-left: -1px;
      border-top-left-radius: 0;
      border-bottom-left-radius: 0;
    }
    
    &:not(:last-child) {
      border-top-right-radius: 0;
      border-bottom-right-radius: 0;
    }
    
    &:hover {
      z-index: 1;
    }
  }
}
</style>
