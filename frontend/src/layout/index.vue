<template>
  <div class="layout-container">
    <!-- 侧边栏 -->
    <aside 
      class="layout-sidebar"
      :class="{ 'is-collapsed': appStore.sidebarCollapsed }"
    >
      <div class="sidebar-header">
        <div class="logo">
          <div class="logo-icon">
            <el-icon size="32">
              <Document />
            </el-icon>
          </div>
          <div v-show="!appStore.sidebarCollapsed" class="logo-content">
            <span class="logo-text gradient-text">
              TestCase
            </span>
            <span class="logo-subtitle">
              测试用例生成平台
            </span>
          </div>
        </div>
      </div>
      
      <el-menu
        :default-active="$route.path"
        :collapse="appStore.sidebarCollapsed"
        :unique-opened="true"
        router
        class="sidebar-menu"
      >
        <template v-for="menuItem in menuRoutes" :key="menuItem.path">
          <!-- 有子菜单的情况 -->
          <el-sub-menu
            v-if="menuItem.children && menuItem.children.length > 0"
            :index="menuItem.path"
          >
            <template #title>
              <el-icon v-if="menuItem.meta?.icon">
                <component :is="menuItem.meta.icon" />
              </el-icon>
              <span>{{ menuItem.meta?.title }}</span>
            </template>
            <el-menu-item
              v-for="child in menuItem.children"
              :key="child.path"
              :index="child.path"
            >
              <el-icon v-if="child.meta?.icon">
                <component :is="child.meta.icon" />
              </el-icon>
              <span>{{ child.meta?.title }}</span>
            </el-menu-item>
          </el-sub-menu>

          <!-- 顶级菜单项 -->
          <el-menu-item
            v-else
            :index="menuItem.path"
          >
            <el-icon v-if="menuItem.meta?.icon">
              <component :is="menuItem.meta.icon" />
            </el-icon>
            <span>{{ menuItem.meta?.title }}</span>
          </el-menu-item>
        </template>
      </el-menu>
    </aside>

    <!-- 主内容区 -->
    <div class="layout-main">
      <!-- 顶部导航 -->
      <header class="layout-header">
        <div class="header-left">
          <el-button
            type="link"
            @click="appStore.toggleSidebar"
            class="sidebar-toggle"
          >
            <el-icon size="20">
              <Expand v-if="appStore.sidebarCollapsed" />
              <Fold v-else />
            </el-icon>
          </el-button>
          
          <el-breadcrumb separator="/">
            <el-breadcrumb-item
              v-for="item in breadcrumbs"
              :key="item.path"
              :to="item.path"
            >
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <el-button
            type="link"
            @click="appStore.toggleTheme"
            class="theme-toggle"
          >
            <el-icon size="18">
              <Moon v-if="!appStore.isDark" />
              <Sunny v-else />
            </el-icon>
          </el-button>
          
          <el-dropdown>
            <div class="user-avatar">
              <el-avatar size="small">
                <el-icon><User /></el-icon>
              </el-avatar>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人设置</el-dropdown-item>
                <el-dropdown-item divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- 页面内容 -->
      <main class="layout-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onErrorCaptured } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores'
import {
  Document,
  Expand,
  Files,
  Fold,
  Moon,
  Sunny,
  User
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

// 错误处理
onErrorCaptured((err, vm, info) => {
  console.error('Layout组件捕获到错误:', err, info)
  // 返回false阻止错误继续传播
  return false
})

// 菜单路由
const menuRoutes = computed(() => {
  // 手动定义菜单结构，避免循环引用
  const menuItems = [
    {
      path: '/dashboard',
      meta: {
        title: '仪表盘',
        icon: 'Dashboard'
      }
    },
    {
      path: '/project',
      meta: {
        title: '项目管理',
        icon: 'Folder'
      },
      children: [
        {
          path: '/project/list',
          meta: {
            title: '项目列表',
            icon: 'List'
          }
        }
      ]
    },
    {
      path: '/test-case',
      meta: {
        title: '用例管理',
        icon: 'Document'
      },
      children: [
        {
          path: '/test-case/generate',
          meta: {
            title: '用例生成',
            icon: 'Plus'
          }
        },

        {
          path: '/test-case/management',
          meta: {
            title: '用例管理',
            icon: 'List'
          }
        },
        {
          path: '/test-case/mindmap',
          meta: {
            title: '思维导图',
            icon: 'Share'
          }
        },
        {
          path: '/test-case/sessions',
          meta: {
            title: '会话管理',
            icon: 'Operation'
          }
        },
        {
          path: '/test-case/requirements',
          meta: {
            title: '需求管理',
            icon: 'Files'
          }
        }
      ]
    },

    {
      path: '/settings',
      meta: {
        title: '系统管理',
        icon: 'Setting'
      },
      children: [
        {
          path: '/settings/system',
          meta: {
            title: '系统设置',
            icon: 'Setting'
          }
        },
        {
          path: '/settings/categories',
          meta: {
            title: '分类管理',
            icon: 'Collection'
          }
        },
        {
          path: '/settings/tags',
          meta: {
            title: '标签管理',
            icon: 'PriceTag'
          }
        },
        {
          path: '/settings/files',
          meta: {
            title: '文件管理',
            icon: 'Folder'
          }
        }
      ]
    }
  ]

  return menuItems
})

// 面包屑导航
const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta?.title)
  const breadcrumbs = []
  
  for (const match of matched) {
    if (match.path !== '/') {
      breadcrumbs.push({
        title: match.meta?.title,
        path: match.path
      })
    }
  }
  
  return breadcrumbs
})
</script>

<style lang="scss" scoped>
.layout-container {
  display: flex;
  height: 100vh;
  width: 100vw;
}

.layout-sidebar {
  width: 280px;
  background: var(--bg-primary);
  border-right: 1px solid var(--border-color);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  box-shadow: var(--shadow);
  position: relative;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(180deg, rgba(37, 99, 235, 0.02) 0%, transparent 100%);
    pointer-events: none;
  }

  &.is-collapsed {
    width: 72px;
  }

  .sidebar-header {
    height: 80px;
    display: flex;
    align-items: center;
    padding: 0 var(--spacing-lg);
    border-bottom: 1px solid var(--border-color-light);
    background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
    position: relative;

    .logo {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);

      .logo-icon {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
        border-radius: var(--border-radius-lg);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        box-shadow: var(--shadow-md);
        transition: transform 0.3s ease;

        &:hover {
          transform: scale(1.05);
        }
      }

      .logo-content {
        display: flex;
        flex-direction: column;

        .logo-text {
          font-size: 20px;
          font-weight: 700;
          line-height: 1.2;
          white-space: nowrap;
        }

        .logo-subtitle {
          font-size: 12px;
          color: var(--text-secondary);
          font-weight: 500;
          white-space: nowrap;
        }
      }
    }
  }
  
  .sidebar-menu {
    border: none;
    height: calc(100vh - 80px);
    overflow-y: auto;
    padding: var(--spacing-md);
    background: transparent;

    .el-menu-item,
    .el-sub-menu__title {
      border-radius: var(--border-radius);
      margin-bottom: var(--spacing-xs);
      transition: all 0.3s ease;
      font-weight: 500;

      &:hover {
        background: linear-gradient(135deg, var(--gray-100) 0%, var(--gray-50) 100%);
        transform: translateX(4px);
      }

      &.is-active {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-light) 100%);
        color: white;
        box-shadow: var(--shadow-md);

        .el-icon {
          color: white;
        }
      }
    }

    .el-sub-menu {
      .el-menu-item {
        margin-left: var(--spacing-md);
        font-size: 14px;
      }
    }
  }
}

.layout-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.layout-header {
  height: 72px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-xl);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(10px);
  position: relative;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, rgba(37, 99, 235, 0.02) 0%, transparent 50%, rgba(6, 182, 212, 0.02) 100%);
    pointer-events: none;
  }
  
  .header-left {
    display: flex;
    align-items: center;
    gap: var(--spacing-lg);

    .sidebar-toggle {
      width: 40px;
      height: 40px;
      border-radius: var(--border-radius);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;

      &:hover {
        background: linear-gradient(135deg, var(--gray-100) 0%, var(--gray-50) 100%);
        transform: scale(1.05);
      }
    }

    .el-breadcrumb {
      font-weight: 500;

      .el-breadcrumb__item {
        .el-breadcrumb__inner {
          color: var(--text-secondary);
          transition: color 0.2s ease;

          &:hover {
            color: var(--primary-color);
          }
        }

        &:last-child .el-breadcrumb__inner {
          color: var(--text-primary);
          font-weight: 600;
        }
      }
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);

    .theme-toggle {
      width: 40px;
      height: 40px;
      border-radius: var(--border-radius);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;

      &:hover {
        background: linear-gradient(135deg, var(--gray-100) 0%, var(--gray-50) 100%);
        transform: scale(1.05);
      }
    }

    .user-avatar {
      cursor: pointer;
      transition: transform 0.3s ease;

      &:hover {
        transform: scale(1.05);
      }

      .el-avatar {
        box-shadow: var(--shadow);
        border: 2px solid var(--border-color);
      }
    }
  }
}

.layout-content {
  flex: 1;
  overflow: auto;
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
  position: relative;

  &::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background:
      radial-gradient(circle at 20% 80%, rgba(37, 99, 235, 0.1) 0%, transparent 50%),
      radial-gradient(circle at 80% 20%, rgba(6, 182, 212, 0.1) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
  }

  > * {
    position: relative;
    z-index: 1;
  }
}

// 暗色主题
.dark {
  --bg-primary: var(--gray-900);
  --bg-secondary: var(--gray-800);
  --bg-tertiary: var(--gray-700);
  --text-primary: var(--gray-100);
  --text-secondary: var(--gray-300);
  --text-tertiary: var(--gray-400);
  --border-color: var(--gray-700);
  --border-color-light: var(--gray-600);

  .layout-sidebar {
    background: var(--bg-primary);
    border-right-color: var(--border-color);

    &::before {
      background: linear-gradient(180deg, rgba(37, 99, 235, 0.05) 0%, transparent 100%);
    }

    .sidebar-header {
      background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);

      .logo-icon {
        box-shadow: 0 4px 20px rgba(37, 99, 235, 0.3);
      }
    }

    .sidebar-menu {
      .el-menu-item,
      .el-sub-menu__title {
        color: var(--text-primary);

        &:hover {
          background: linear-gradient(135deg, var(--gray-700) 0%, var(--gray-600) 100%);
        }

        &.is-active {
          background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-light) 100%);
          box-shadow: 0 4px 20px rgba(37, 99, 235, 0.3);
        }
      }
    }
  }

  .layout-header {
    background: rgba(15, 23, 42, 0.8);
    border-bottom-color: var(--border-color);

    &::before {
      background: linear-gradient(90deg, rgba(37, 99, 235, 0.05) 0%, transparent 50%, rgba(6, 182, 212, 0.05) 100%);
    }

    .header-left {
      .sidebar-toggle:hover {
        background: linear-gradient(135deg, var(--gray-700) 0%, var(--gray-600) 100%);
      }
    }

    .header-right {
      .theme-toggle:hover {
        background: linear-gradient(135deg, var(--gray-700) 0%, var(--gray-600) 100%);
      }
    }
  }

  .layout-content {
    background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);

    &::before {
      background:
        radial-gradient(circle at 20% 80%, rgba(37, 99, 235, 0.15) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(6, 182, 212, 0.15) 0%, transparent 50%);
    }
  }
}
</style>
