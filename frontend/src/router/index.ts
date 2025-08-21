import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import Layout from '@/layout/index.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    meta: { hidden: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: {
          title: '仪表盘',
          icon: 'Dashboard',
          showInMenu: true
        }
      }
    ]
  },
  {
    path: '/test-case',
    component: Layout,
    redirect: '/test-case/generate',
    meta: {
      title: '测试用例',
      icon: 'Document',
      showInMenu: true
    },
    children: [
      {
        path: 'generate',
        name: 'TestCaseGenerate',
        component: () => import('@/views/test-case/generate/index.vue'),
        meta: {
          title: '用例生成',
          icon: 'Plus',
          showInMenu: true
        }
      },
      {
        path: 'test-video-upload',
        name: 'TestVideoUpload',
        component: () => import('@/views/test-video-upload.vue'),
        meta: {
          title: '视频上传测试',
          icon: 'VideoPlay',
          showInMenu: true
        }
      },

      {
        path: 'management',
        name: 'TestCaseManagement',
        component: () => import('@/views/test-case/management/index.vue'),
        meta: {
          title: '用例管理',
          icon: 'List',
          showInMenu: true
        }
      },
      {
        path: 'mindmap',
        name: 'MindmapList',
        component: () => import('@/views/test-case/mindmap/list.vue'),
        meta: {
          title: '思维导图',
          icon: 'Share',
          showInMenu: true
        }
      },
      {
        path: 'mindmap/:sessionId',
        name: 'TestCaseMindmap',
        component: () => import('@/views/test-case/mindmap/index.vue'),
        meta: {
          title: '思维导图详情',
          icon: 'Share',
          showInMenu: false
        }
      },
      {
        path: 'test-mindmap',
        name: 'TestMindmap',
        component: () => import('@/views/test-mindmap.vue'),
        meta: {
          title: '思维导图测试',
          icon: 'Share',
          showInMenu: true
        }
      },
      {
        path: 'sessions',
        name: 'SessionList',
        component: () => import('@/views/test-case/session/list.vue'),
        meta: {
          title: '会话管理',
          icon: 'Operation',
          showInMenu: true
        }
      },
      {
        path: 'session/:sessionId',
        name: 'SessionDetail',
        component: () => import('@/views/test-case/session/detail.vue'),
        meta: {
          title: '会话详情',
          icon: 'Document',
          showInMenu: false
        }
      },
      {
        path: 'detail/:id',
        name: 'TestCaseDetail',
        component: () => import('@/views/test-case/detail/index.vue'),
        meta: {
          title: '测试用例详情',
          icon: 'Document',
          showInMenu: false
        }
      },
      {
        path: 'edit/:id',
        name: 'TestCaseEdit',
        component: () => import('@/views/test-case/edit/index.vue'),
        meta: {
          title: '编辑测试用例',
          icon: 'Edit',
          showInMenu: false
        }
      },
      {
        path: 'requirements',
        name: 'RequirementManagement',
        component: () => import('@/views/requirement/RequirementManagement.vue'),
        meta: {
          title: '需求管理',
          icon: 'Files',
          showInMenu: true
        }
      }
    ]
  },
  {
    path: '/project',
    component: Layout,
    redirect: '/project/list',
    meta: {
      title: '项目管理',
      icon: 'Folder',
      showInMenu: true
    },
    children: [
      {
        path: 'list',
        name: 'ProjectList',
        component: () => import('@/views/project/index.vue'),
        meta: {
          title: '项目列表',
          icon: 'List',
          showInMenu: true
        }
      }
    ]
  },
  {
    path: '/settings',
    component: Layout,
    redirect: '/settings/system',
    meta: {
      title: '系统管理',
      icon: 'Setting',
      showInMenu: true
    },
    children: [
      {
        path: 'system',
        name: 'SystemSettings',
        component: () => import('@/views/settings/index.vue'),
        meta: {
          title: '系统设置',
          icon: 'Setting',
          showInMenu: true
        }
      },
      {
        path: 'categories',
        name: 'CategoryManagement',
        component: () => import('@/views/settings/categories.vue'),
        meta: {
          title: '分类管理',
          icon: 'Collection',
          showInMenu: true
        }
      },
      {
        path: 'tags',
        name: 'TagManagement',
        component: () => import('@/views/settings/tags.vue'),
        meta: {
          title: '标签管理',
          icon: 'PriceTag',
          showInMenu: true
        }
      },
      {
        path: 'files',
        name: 'FileManagement',
        component: () => import('@/views/settings/files.vue'),
        meta: {
          title: '文件管理',
          icon: 'Folder',
          showInMenu: true
        }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
