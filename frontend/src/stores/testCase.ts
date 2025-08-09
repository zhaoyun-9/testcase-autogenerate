import { defineStore } from 'pinia'
import type { TestCase, TestCaseSession, GenerationProgress } from '@/types/testCase'

// 测试用例相关状态管理
export const useTestCaseStore = defineStore('testCase', {
  state: () => ({
    // 当前会话信息
    currentSession: null as TestCaseSession | null,
    // 生成进度
    generationProgress: null as GenerationProgress | null,
    // 测试用例列表
    testCases: [] as TestCase[],
    // 当前选中的测试用例
    selectedTestCases: [] as string[],
    // 过滤条件
    filters: {
      search: '',
      testType: [] as string[],
      testLevel: [] as string[],
      priority: [] as string[],
      status: [] as string[],
      tags: [] as string[]
    },
    // 分页信息
    pagination: {
      page: 1,
      pageSize: 20,
      total: 0
    },
    // SSE连接状态
    sseConnected: false,
    // 思维导图数据
    mindmapData: null as any
  }),

  getters: {
    // 获取当前会话ID
    getCurrentSessionId: (state) => state.currentSession?.sessionId,
    
    // 获取生成状态
    getGenerationStatus: (state) => state.generationProgress?.status || 'idle',
    
    // 获取过滤后的测试用例数量
    getFilteredTestCasesCount: (state) => state.testCases.length,
    
    // 获取选中的测试用例数量
    getSelectedTestCasesCount: (state) => state.selectedTestCases.length
  },

  actions: {
    // 设置当前会话
    setCurrentSession(session: TestCaseSession) {
      this.currentSession = session
    },

    // 更新生成进度
    updateGenerationProgress(progress: GenerationProgress) {
      this.generationProgress = progress
    },

    // 设置测试用例列表
    setTestCases(testCases: TestCase[]) {
      this.testCases = testCases
    },

    // 添加测试用例
    addTestCase(testCase: TestCase) {
      this.testCases.unshift(testCase)
    },

    // 更新测试用例
    updateTestCase(testCase: TestCase) {
      const index = this.testCases.findIndex(tc => tc.id === testCase.id)
      if (index !== -1) {
        this.testCases[index] = testCase
      }
    },

    // 删除测试用例
    removeTestCase(testCaseId: string) {
      const index = this.testCases.findIndex(tc => tc.id === testCaseId)
      if (index !== -1) {
        this.testCases.splice(index, 1)
      }
    },

    // 设置选中的测试用例
    setSelectedTestCases(selectedIds: string[]) {
      this.selectedTestCases = selectedIds
    },

    // 切换测试用例选中状态
    toggleTestCaseSelection(testCaseId: string) {
      const index = this.selectedTestCases.indexOf(testCaseId)
      if (index === -1) {
        this.selectedTestCases.push(testCaseId)
      } else {
        this.selectedTestCases.splice(index, 1)
      }
    },

    // 设置过滤条件
    setFilters(filters: Partial<typeof this.filters>) {
      this.filters = { ...this.filters, ...filters }
    },

    // 设置分页信息
    setPagination(pagination: Partial<typeof this.pagination>) {
      this.pagination = { ...this.pagination, ...pagination }
    },

    // 设置SSE连接状态
    setSseConnected(connected: boolean) {
      this.sseConnected = connected
    },

    // 设置思维导图数据
    setMindmapData(data: any) {
      this.mindmapData = data
    },

    // 重置状态
    reset() {
      this.currentSession = null
      this.generationProgress = null
      this.selectedTestCases = []
      this.sseConnected = false
    }
  }
})
