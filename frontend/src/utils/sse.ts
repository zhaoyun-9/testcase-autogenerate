// SSE (Server-Sent Events) 工具类
export class SSEClient {
  private eventSource: EventSource | null = null
  private url: string
  private listeners: Map<string, Function[]> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private isManualClose = false

  constructor(url: string) {
    this.url = url
    console.log('创建新的SSE客户端实例:', url)
  }

  // 连接SSE
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.eventSource = new EventSource(this.url)
        this.isManualClose = false

        this.eventSource.onopen = (event) => {
          console.log('SSE连接已建立:', this.url)
          this.reconnectAttempts = 0
          this.emit('connected', event)
          resolve()
        }

        this.eventSource.onerror = (event) => {
          console.error('SSE连接错误:', event)
          this.emit('error', event)
          
          if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnect()
          } else if (this.reconnectAttempts === 0) {
            reject(new Error('SSE连接失败'))
          }
        }

        this.eventSource.onmessage = (event) => {
          console.log('收到默认message事件:', event.data)

          let eventData = event.data

          // 检查是否是嵌套的SSE格式
          if (typeof eventData === 'string' && eventData.includes('event:') && eventData.includes('data:')) {
            console.log('默认消息检测到嵌套SSE格式，提取内层data')
            const dataMatches = eventData.match(/data:\s*(.+?)(?=\n|$)/g)
            if (dataMatches && dataMatches.length > 0) {
              const lastDataMatch = dataMatches[dataMatches.length - 1]
              const jsonMatch = lastDataMatch.match(/data:\s*(.+)/)
              if (jsonMatch && jsonMatch[1]) {
                eventData = jsonMatch[1].trim()
                console.log('默认消息提取的JSON数据:', eventData)
              }
            }
          }

          try {
            // 对于默认的 message 事件，尝试解析 data 字段
            const data = JSON.parse(eventData)
            this.emit('message', data)
          } catch (error) {
            // 如果不是JSON格式，可能是流式文本消息，直接传递原始数据
            console.log('收到流式文本消息:', eventData)
            this.emit('stream-text', {
              content: eventData,
              timestamp: new Date().toISOString()
            })
          }
        }

        // 监听自定义事件
        this.setupCustomEventListeners()

      } catch (error) {
        reject(error)
      }
    })
  }

  // 设置自定义事件监听器
  private setupCustomEventListeners() {
    if (!this.eventSource) return

    // 监听不同类型的事件
    const eventTypes = [
      'message', 'progress', 'stage', 'result', 'error', 'complete', 'completion',
      'heartbeat', 'final_result', 'test_case', 'mindmap'
    ]

    eventTypes.forEach(eventType => {
      this.eventSource!.addEventListener(eventType, (event: any) => {
        console.log(`收到${eventType}事件:`, event)
        console.log(`事件数据:`, event.data)

        let eventData = event.data

        // 检查是否是嵌套的SSE格式（data字段包含完整的SSE事件）
        if (typeof eventData === 'string' && eventData.includes('event:') && eventData.includes('data:')) {
          console.log('检测到嵌套SSE格式，提取内层data')
          // 提取最后一个data:后面的JSON
          const dataMatches = eventData.match(/data:\s*(.+?)(?=\n|$)/g)
          if (dataMatches && dataMatches.length > 0) {
            // 取最后一个data行
            const lastDataMatch = dataMatches[dataMatches.length - 1]
            const jsonMatch = lastDataMatch.match(/data:\s*(.+)/)
            if (jsonMatch && jsonMatch[1]) {
              eventData = jsonMatch[1].trim()
              console.log('提取的JSON数据:', eventData)
            }
          }
        }

        try {
          // 解析JSON数据
          const data = JSON.parse(eventData)
          console.log(`解析后的${eventType}数据:`, data)
          console.log(`准备发出${eventType}事件，数据:`, data)
          this.emit(eventType, data)
          console.log(`已发出${eventType}事件`)
        } catch (error) {
          // 如果不是JSON格式，可能是流式文本消息
          console.log(`收到${eventType}流式文本:`, eventData)
          console.error(`解析${eventType}事件失败:`, error)
          this.emit(`${eventType}-text`, {
            content: eventData,
            eventType,
            timestamp: new Date().toISOString()
          })
        }
      })
    })
  }

  // 重连
  private reconnect() {
    if (this.isManualClose) return

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)

    console.log(`SSE重连尝试 ${this.reconnectAttempts}/${this.maxReconnectAttempts}，${delay}ms后重试`)

    setTimeout(() => {
      if (!this.isManualClose) {
        // 保存现有的监听器
        const savedListeners = new Map(this.listeners)
        console.log('保存现有监听器，数量:', savedListeners.size)

        this.close()
        this.connect().then(() => {
          // 重新注册监听器
          console.log('重连成功，恢复监听器')
          this.listeners = savedListeners
          console.log('恢复后的监听器数量:', this.listeners.size)
        }).catch(error => {
          console.error('SSE重连失败:', error)
        })
      }
    }, delay)
  }

  // 添加事件监听器
  on(event: string, callback: Function) {
    console.log(`注册SSE事件监听器: ${event}`)
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event)!.push(callback)
    console.log(`事件${event}的监听器数量:`, this.listeners.get(event)!.length)
  }

  // 移除事件监听器
  off(event: string, callback?: Function) {
    if (!this.listeners.has(event)) return

    if (callback) {
      const callbacks = this.listeners.get(event)!
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    } else {
      this.listeners.delete(event)
    }
  }

  // 触发事件
  private emit(event: string, data?: any) {
    console.log(`SSE emit事件: ${event}，数据:`, data)
    console.log(`当前listeners Map大小:`, this.listeners.size)
    console.log(`listeners Map中的所有事件:`, Array.from(this.listeners.keys()))
    const callbacks = this.listeners.get(event)
    console.log(`事件${event}的回调数量:`, callbacks ? callbacks.length : 0)
    if (callbacks) {
      callbacks.forEach((callback, index) => {
        try {
          console.log(`执行事件${event}的第${index + 1}个回调`)
          callback(data)
          console.log(`事件${event}的第${index + 1}个回调执行成功`)
        } catch (error) {
          console.error(`SSE事件回调执行失败 (${event}):`, error)
        }
      })
    } else {
      console.warn(`没有找到事件${event}的回调函数`)
    }
  }

  // 关闭连接
  close(clearListeners: boolean = false) {
    console.log('SSE客户端关闭，clearListeners:', clearListeners)
    this.isManualClose = true
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
    if (clearListeners) {
      console.log('清空listeners')
      this.listeners.clear()
    }
    console.log('SSE连接已关闭')
  }

  // 获取连接状态
  get readyState() {
    return this.eventSource?.readyState ?? EventSource.CLOSED
  }

  // 检查是否已连接
  get isConnected() {
    return this.eventSource?.readyState === EventSource.OPEN
  }
}

// SSE连接管理器
export class SSEManager {
  private connections: Map<string, SSEClient> = new Map()

  // 创建连接
  createConnection(key: string, url: string): SSEClient {
    // 如果已存在连接，先关闭
    if (this.connections.has(key)) {
      this.connections.get(key)!.close()
    }

    const client = new SSEClient(url)
    this.connections.set(key, client)
    return client
  }

  // 获取连接
  getConnection(key: string): SSEClient | undefined {
    return this.connections.get(key)
  }

  // 关闭连接
  closeConnection(key: string) {
    const client = this.connections.get(key)
    if (client) {
      client.close()
      this.connections.delete(key)
    }
  }

  // 关闭所有连接
  closeAllConnections() {
    this.connections.forEach(client => client.close())
    this.connections.clear()
  }
}

// 全局SSE管理器实例
export const sseManager = new SSEManager()
