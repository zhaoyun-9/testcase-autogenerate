/**
 * UI组件库类型定义
 */

// 基础类型
export type Size = 'small' | 'default' | 'large'
export type Type = 'primary' | 'success' | 'warning' | 'danger' | 'info'
export type Status = 'success' | 'error' | 'warning' | 'info' | 'processing'

// 按钮组件类型
export interface ButtonProps {
  type?: Type
  size?: Size
  loading?: boolean
  disabled?: boolean
  icon?: string
  round?: boolean
  circle?: boolean
  plain?: boolean
  text?: boolean
  link?: boolean
}

// 卡片组件类型
export interface CardProps {
  title?: string
  subtitle?: string
  shadow?: 'always' | 'hover' | 'never'
  bodyStyle?: Record<string, any>
  headerStyle?: Record<string, any>
  loading?: boolean
  bordered?: boolean
}

// 表格组件类型
export interface TableColumn {
  prop: string
  label: string
  width?: string | number
  minWidth?: string | number
  fixed?: boolean | 'left' | 'right'
  sortable?: boolean
  filterable?: boolean
  align?: 'left' | 'center' | 'right'
  headerAlign?: 'left' | 'center' | 'right'
  showOverflowTooltip?: boolean
  formatter?: (row: any, column: any, cellValue: any, index: number) => any
  render?: (row: any, column: any, cellValue: any, index: number) => any
}

export interface TableProps {
  data: any[]
  columns: TableColumn[]
  loading?: boolean
  stripe?: boolean
  border?: boolean
  size?: Size
  height?: string | number
  maxHeight?: string | number
  fit?: boolean
  showHeader?: boolean
  highlightCurrentRow?: boolean
  currentRowKey?: string | number
  rowClassName?: string | ((row: any, index: number) => string)
  rowStyle?: Record<string, any> | ((row: any, index: number) => Record<string, any>)
  cellClassName?: string | ((row: any, column: any, rowIndex: number, columnIndex: number) => string)
  cellStyle?: Record<string, any> | ((row: any, column: any, rowIndex: number, columnIndex: number) => Record<string, any>)
  headerRowClassName?: string | ((row: any, index: number) => string)
  headerRowStyle?: Record<string, any> | ((row: any, index: number) => Record<string, any>)
  headerCellClassName?: string | ((row: any, column: any, rowIndex: number, columnIndex: number) => string)
  headerCellStyle?: Record<string, any> | ((row: any, column: any, rowIndex: number, columnIndex: number) => Record<string, any>)
  rowKey?: string | ((row: any) => string)
  emptyText?: string
  defaultExpandAll?: boolean
  expandRowKeys?: any[]
  defaultSort?: { prop: string; order: 'ascending' | 'descending' }
  tooltipEffect?: 'dark' | 'light'
  showSummary?: boolean
  sumText?: string
  summaryMethod?: (param: { columns: any[]; data: any[] }) => any[]
  spanMethod?: (param: { row: any; column: any; rowIndex: number; columnIndex: number }) => number[] | { rowspan: number; colspan: number }
  selectOnIndeterminate?: boolean
  indent?: number
  lazy?: boolean
  load?: (row: any, treeNode: any, resolve: (data: any[]) => void) => void
  treeProps?: { hasChildren?: string; children?: string }
}

// 表单组件类型
export interface FormItemRule {
  required?: boolean
  message?: string
  trigger?: string | string[]
  min?: number
  max?: number
  len?: number
  pattern?: RegExp
  validator?: (rule: any, value: any, callback: (error?: Error) => void) => void
  type?: 'string' | 'number' | 'boolean' | 'method' | 'regexp' | 'integer' | 'float' | 'array' | 'object' | 'enum' | 'date' | 'url' | 'hex' | 'email'
}

export interface FormItem {
  prop: string
  label: string
  type: 'input' | 'select' | 'textarea' | 'number' | 'date' | 'datetime' | 'time' | 'switch' | 'checkbox' | 'radio' | 'upload' | 'custom'
  placeholder?: string
  options?: { label: string; value: any; disabled?: boolean }[]
  rules?: FormItemRule[]
  disabled?: boolean
  readonly?: boolean
  clearable?: boolean
  filterable?: boolean
  multiple?: boolean
  size?: Size
  span?: number
  offset?: number
  push?: number
  pull?: number
  xs?: number | { span?: number; offset?: number }
  sm?: number | { span?: number; offset?: number }
  md?: number | { span?: number; offset?: number }
  lg?: number | { span?: number; offset?: number }
  xl?: number | { span?: number; offset?: number }
  component?: any
  componentProps?: Record<string, any>
  slots?: Record<string, any>
}

export interface FormProps {
  model: Record<string, any>
  items: FormItem[]
  rules?: Record<string, FormItemRule[]>
  labelWidth?: string | number
  labelPosition?: 'left' | 'right' | 'top'
  inline?: boolean
  size?: Size
  disabled?: boolean
  validateOnRuleChange?: boolean
  hideRequiredAsterisk?: boolean
  showMessage?: boolean
  inlineMessage?: boolean
  statusIcon?: boolean
  scrollToError?: boolean
  gutter?: number
  justify?: 'start' | 'end' | 'center' | 'space-around' | 'space-between'
  align?: 'top' | 'middle' | 'bottom'
}

// 上传组件类型
export interface UploadFile {
  name: string
  size: number
  type: string
  url?: string
  status?: 'ready' | 'uploading' | 'success' | 'error'
  percentage?: number
  response?: any
  error?: any
  uid: number
  raw?: File
}

export interface UploadProps {
  action?: string
  headers?: Record<string, any>
  method?: string
  multiple?: boolean
  data?: Record<string, any>
  name?: string
  withCredentials?: boolean
  showFileList?: boolean
  drag?: boolean
  accept?: string
  onPreview?: (file: UploadFile) => void
  onRemove?: (file: UploadFile, fileList: UploadFile[]) => void
  onSuccess?: (response: any, file: UploadFile, fileList: UploadFile[]) => void
  onError?: (error: any, file: UploadFile, fileList: UploadFile[]) => void
  onProgress?: (event: any, file: UploadFile, fileList: UploadFile[]) => void
  onChange?: (file: UploadFile, fileList: UploadFile[]) => void
  beforeUpload?: (file: File) => boolean | Promise<File>
  beforeRemove?: (file: UploadFile, fileList: UploadFile[]) => boolean | Promise<boolean>
  listType?: 'text' | 'picture' | 'picture-card'
  autoUpload?: boolean
  fileList?: UploadFile[]
  httpRequest?: (options: any) => void
  disabled?: boolean
  limit?: number
  onExceed?: (files: File[], fileList: UploadFile[]) => void
}

// 进度组件类型
export interface ProgressProps {
  percentage: number
  type?: 'line' | 'circle' | 'dashboard'
  strokeWidth?: number
  textInside?: boolean
  status?: 'success' | 'exception' | 'warning'
  color?: string | string[] | { color: string; percentage: number }[]
  width?: number
  showText?: boolean
  strokeLinecap?: 'butt' | 'round' | 'square'
  format?: (percentage: number) => string
}

// 标签组件类型
export interface TagProps {
  type?: Type
  closable?: boolean
  disableTransitions?: boolean
  hit?: boolean
  color?: string
  size?: Size
  effect?: 'dark' | 'light' | 'plain'
  round?: boolean
}

// 对话框组件类型
export interface DialogProps {
  modelValue: boolean
  title?: string
  width?: string | number
  fullscreen?: boolean
  top?: string
  modal?: boolean
  modalClass?: string
  appendToBody?: boolean
  lockScroll?: boolean
  customClass?: string
  openDelay?: number
  closeDelay?: number
  closeOnClickModal?: boolean
  closeOnPressEscape?: boolean
  showClose?: boolean
  beforeClose?: (done: () => void) => void
  draggable?: boolean
  center?: boolean
  alignCenter?: boolean
  destroyOnClose?: boolean
}

// 页面头部组件类型
export interface PageHeaderProps {
  title: string
  subtitle?: string
  showBack?: boolean
  breadcrumb?: { label: string; to?: string }[]
  actions?: any[]
  tabs?: { label: string; value: string; disabled?: boolean }[]
  activeTab?: string
}

// 搜索栏组件类型
export interface SearchBarProps {
  fields: FormItem[]
  model: Record<string, any>
  loading?: boolean
  showReset?: boolean
  showExpand?: boolean
  defaultExpanded?: boolean
  gutter?: number
  labelWidth?: string | number
}

// 数据表格组件类型
export interface DataTableProps extends TableProps {
  searchable?: boolean
  searchFields?: FormItem[]
  searchModel?: Record<string, any>
  pagination?: {
    page: number
    pageSize: number
    total: number
    pageSizes?: number[]
    layout?: string
    background?: boolean
    small?: boolean
    hideOnSinglePage?: boolean
  }
  selection?: boolean
  actions?: {
    label: string
    type?: Type
    size?: Size
    icon?: string
    disabled?: boolean | ((row: any) => boolean)
    show?: boolean | ((row: any) => boolean)
    handler: (row: any, index: number) => void
  }[]
  batchActions?: {
    label: string
    type?: Type
    size?: Size
    icon?: string
    disabled?: boolean
    handler: (selectedRows: any[]) => void
  }[]
}

// 状态徽章组件类型
export interface StatusBadgeProps {
  status: Status
  text?: string
  dot?: boolean
  showText?: boolean
  size?: Size
}

// 空状态组件类型
export interface EmptyStateProps {
  image?: string
  imageSize?: number
  description?: string
  actions?: {
    label: string
    type?: Type
    size?: Size
    icon?: string
    handler: () => void
  }[]
}

// 加载状态组件类型
export interface LoadingStateProps {
  loading: boolean
  text?: string
  spinner?: string
  background?: string
  customClass?: string
  size?: Size
}
