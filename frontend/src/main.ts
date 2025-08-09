import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus, { ID_INJECTION_KEY } from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import App from './App.vue'
import router from './router'
import './styles/index.scss'

const app = createApp(App)

// 修复setAttribute错误的monkey patch
const originalSetAttribute = Element.prototype.setAttribute
Element.prototype.setAttribute = function(name: string, value: string) {
  // 检查属性名是否有效
  if (typeof name !== 'string' || name === '' || /^\d/.test(name)) {
    console.warn('无效的属性名:', name, '值:', value)
    // 如果属性名以数字开头，添加前缀
    if (/^\d/.test(name)) {
      name = 'data-' + name
    } else {
      // 其他无效属性名，直接返回
      return
    }
  }

  try {
    return originalSetAttribute.call(this, name, value)
  } catch (error) {
    console.warn('setAttribute失败:', name, value, error)
  }
}

// 全局错误处理，捕获setAttribute错误
window.addEventListener('error', (event) => {
  if (event.error && event.error.message && event.error.message.includes('setAttribute')) {
    console.error('setAttribute错误详情:', {
      message: event.error.message,
      stack: event.error.stack,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno
    })
    // 阻止错误冒泡，避免影响用户体验
    event.preventDefault()
    return false
  }
})

// 配置Vue全局属性
app.config.warnHandler = (msg, vm, trace) => {
  // 抑制Element Plus内部的slot警告
  if (msg.includes('Slot "default" invoked outside of the render function')) {
    return
  }
  // 其他警告正常显示
  console.warn(`[Vue warn]: ${msg}`, vm, trace)
}

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 配置Element Plus ID注入，确保生成的ID不会以数字开头
app.provide(ID_INJECTION_KEY, {
  prefix: 1000 + Math.floor(Math.random() * 9000), // 确保前缀是4位数字，不会以0开头
  current: 0
})

app.use(createPinia())
app.use(router)
app.use(ElementPlus, {
  locale: zhCn,
})

app.mount('#app')
