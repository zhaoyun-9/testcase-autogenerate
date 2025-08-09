/**
 * UI组件库工具函数
 */

import type { Type, Size, Status } from './types'

/**
 * 获取类型对应的颜色
 */
export const getTypeColor = (type: Type): string => {
  const colorMap: Record<Type, string> = {
    primary: 'var(--primary-color)',
    success: 'var(--success-color)',
    warning: 'var(--warning-color)',
    danger: 'var(--error-color)',
    info: 'var(--info-color)'
  }
  return colorMap[type] || colorMap.primary
}

/**
 * 获取状态对应的类型
 */
export const getStatusType = (status: Status): Type => {
  const typeMap: Record<Status, Type> = {
    success: 'success',
    error: 'danger',
    warning: 'warning',
    info: 'info',
    processing: 'primary'
  }
  return typeMap[status] || 'info'
}

/**
 * 获取状态对应的图标
 */
export const getStatusIcon = (status: Status): string => {
  const iconMap: Record<Status, string> = {
    success: 'CircleCheck',
    error: 'CircleClose',
    warning: 'Warning',
    info: 'InfoFilled',
    processing: 'Loading'
  }
  return iconMap[status] || 'InfoFilled'
}

/**
 * 获取尺寸对应的数值
 */
export const getSizeValue = (size: Size): number => {
  const sizeMap: Record<Size, number> = {
    small: 12,
    default: 14,
    large: 16
  }
  return sizeMap[size] || sizeMap.default
}

/**
 * 生成唯一ID
 */
export const generateId = (prefix = 'tc'): string => {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

/**
 * 防抖函数
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number,
  immediate = false
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout | null = null
  
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null
      if (!immediate) func(...args)
    }
    
    const callNow = immediate && !timeout
    
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(later, wait)
    
    if (callNow) func(...args)
  }
}

/**
 * 节流函数
 */
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean
  
  return function executedFunction(...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

/**
 * 深拷贝
 */
export const deepClone = <T>(obj: T): T => {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj.getTime()) as unknown as T
  if (obj instanceof Array) return obj.map(item => deepClone(item)) as unknown as T
  if (typeof obj === 'object') {
    const clonedObj = {} as T
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key])
      }
    }
    return clonedObj
  }
  return obj
}

/**
 * 格式化文件大小
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化时间
 */
export const formatTime = (time: string | number | Date): string => {
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const minute = 60 * 1000
  const hour = minute * 60
  const day = hour * 24
  const week = day * 7
  const month = day * 30
  const year = day * 365
  
  if (diff < minute) {
    return '刚刚'
  } else if (diff < hour) {
    return Math.floor(diff / minute) + '分钟前'
  } else if (diff < day) {
    return Math.floor(diff / hour) + '小时前'
  } else if (diff < week) {
    return Math.floor(diff / day) + '天前'
  } else if (diff < month) {
    return Math.floor(diff / week) + '周前'
  } else if (diff < year) {
    return Math.floor(diff / month) + '个月前'
  } else {
    return Math.floor(diff / year) + '年前'
  }
}

/**
 * 验证邮箱
 */
export const validateEmail = (email: string): boolean => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}

/**
 * 验证手机号
 */
export const validatePhone = (phone: string): boolean => {
  const re = /^1[3-9]\d{9}$/
  return re.test(phone)
}

/**
 * 验证URL
 */
export const validateUrl = (url: string): boolean => {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

/**
 * 获取文件扩展名
 */
export const getFileExtension = (filename: string): string => {
  return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2)
}

/**
 * 获取文件类型图标
 */
export const getFileTypeIcon = (filename: string): string => {
  const ext = getFileExtension(filename).toLowerCase()
  const iconMap: Record<string, string> = {
    // 图片
    jpg: 'Picture',
    jpeg: 'Picture',
    png: 'Picture',
    gif: 'Picture',
    bmp: 'Picture',
    webp: 'Picture',
    svg: 'Picture',
    
    // 文档
    pdf: 'Document',
    doc: 'Document',
    docx: 'Document',
    txt: 'Document',
    md: 'Document',
    rtf: 'Document',
    
    // 表格
    xls: 'Grid',
    xlsx: 'Grid',
    csv: 'Grid',
    
    // 演示文稿
    ppt: 'Present',
    pptx: 'Present',
    
    // 压缩文件
    zip: 'FolderZip',
    rar: 'FolderZip',
    '7z': 'FolderZip',
    tar: 'FolderZip',
    gz: 'FolderZip',
    
    // 代码文件
    js: 'DocumentCode',
    ts: 'DocumentCode',
    vue: 'DocumentCode',
    html: 'DocumentCode',
    css: 'DocumentCode',
    scss: 'DocumentCode',
    less: 'DocumentCode',
    json: 'DocumentCode',
    xml: 'DocumentCode',
    yaml: 'DocumentCode',
    yml: 'DocumentCode',
    py: 'DocumentCode',
    java: 'DocumentCode',
    cpp: 'DocumentCode',
    c: 'DocumentCode',
    php: 'DocumentCode',
    rb: 'DocumentCode',
    go: 'DocumentCode',
    rs: 'DocumentCode',
    
    // 视频
    mp4: 'VideoPlay',
    avi: 'VideoPlay',
    mov: 'VideoPlay',
    wmv: 'VideoPlay',
    flv: 'VideoPlay',
    mkv: 'VideoPlay',
    
    // 音频
    mp3: 'Headphone',
    wav: 'Headphone',
    flac: 'Headphone',
    aac: 'Headphone',
    
    // 数据库
    sql: 'Coin',
    db: 'Coin',
    sqlite: 'Coin',
    mdb: 'Coin'
  }
  
  return iconMap[ext] || 'Document'
}

/**
 * 颜色工具函数
 */
export const colorUtils = {
  /**
   * 十六进制转RGB
   */
  hexToRgb: (hex: string): { r: number; g: number; b: number } | null => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null
  },
  
  /**
   * RGB转十六进制
   */
  rgbToHex: (r: number, g: number, b: number): string => {
    return '#' + [r, g, b].map(x => {
      const hex = x.toString(16)
      return hex.length === 1 ? '0' + hex : hex
    }).join('')
  },
  
  /**
   * 调整颜色亮度
   */
  adjustBrightness: (hex: string, percent: number): string => {
    const rgb = colorUtils.hexToRgb(hex)
    if (!rgb) return hex
    
    const adjust = (color: number) => {
      const adjusted = Math.round(color * (100 + percent) / 100)
      return Math.max(0, Math.min(255, adjusted))
    }
    
    return colorUtils.rgbToHex(
      adjust(rgb.r),
      adjust(rgb.g),
      adjust(rgb.b)
    )
  }
}

/**
 * 数组工具函数
 */
export const arrayUtils = {
  /**
   * 数组去重
   */
  unique: <T>(arr: T[]): T[] => {
    return [...new Set(arr)]
  },
  
  /**
   * 数组分组
   */
  groupBy: <T>(arr: T[], key: keyof T): Record<string, T[]> => {
    return arr.reduce((groups, item) => {
      const group = String(item[key])
      groups[group] = groups[group] || []
      groups[group].push(item)
      return groups
    }, {} as Record<string, T[]>)
  },
  
  /**
   * 数组排序
   */
  sortBy: <T>(arr: T[], key: keyof T, order: 'asc' | 'desc' = 'asc'): T[] => {
    return [...arr].sort((a, b) => {
      const aVal = a[key]
      const bVal = b[key]
      
      if (aVal < bVal) return order === 'asc' ? -1 : 1
      if (aVal > bVal) return order === 'asc' ? 1 : -1
      return 0
    })
  }
}
