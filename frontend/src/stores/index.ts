import { defineStore } from 'pinia'

// 应用全局状态
export const useAppStore = defineStore('app', {
  state: () => ({
    // 侧边栏折叠状态
    sidebarCollapsed: false,
    // 主题模式
    isDark: false,
    // 当前用户信息
    userInfo: null as any,
    // 全局加载状态
    loading: false
  }),

  getters: {
    // 获取侧边栏状态
    getSidebarCollapsed: (state) => state.sidebarCollapsed,
    // 获取主题模式
    getIsDark: (state) => state.isDark
  },

  actions: {
    // 切换侧边栏
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
    
    // 设置侧边栏状态
    setSidebarCollapsed(collapsed: boolean) {
      this.sidebarCollapsed = collapsed
    },

    // 切换主题
    toggleTheme() {
      this.isDark = !this.isDark
      document.documentElement.classList.toggle('dark', this.isDark)
    },

    // 设置加载状态
    setLoading(loading: boolean) {
      this.loading = loading
    },

    // 设置用户信息
    setUserInfo(userInfo: any) {
      this.userInfo = userInfo
    }
  },

  persist: {
    key: 'app-store',
    storage: localStorage,
    paths: ['sidebarCollapsed', 'isDark', 'userInfo']
  }
})
