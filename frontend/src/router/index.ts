import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/auth/Login.vue'),
      meta: { requiresAuth: false, title: '登录' }
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/auth/Register.vue'),
      meta: { requiresAuth: false, title: '注册' }
    },
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue'),
          meta: { title: '仪表盘' }
        },
        {
          path: '/projects',
          name: 'Projects',
          component: () => import('@/views/project/ProjectList.vue'),
          meta: { title: '项目管理' }
        },
        {
          path: '/projects/:id',
          name: 'ProjectDetail',
          component: () => import('@/views/project/ProjectDetailNew.vue'),
          meta: { title: '项目详情' }
        },
        {
          path: '/projects/:projectId/modules/:moduleId',
          name: 'ModuleDetail',
          component: () => import('@/views/module/ModuleDetail.vue'),
          meta: { title: '模块详情' }
        },
        {
          path: '/users',
          name: 'Users',
          component: () => import('@/views/user/UserList.vue'),
          meta: { title: '用户管理', requiresAdmin: true }
        },
        {
          path: '/profile',
          name: 'Profile',
          component: () => import('@/views/user/Profile.vue'),
          meta: { title: '个人资料' }
        },
        {
          path: '/model-plaza',
          name: 'ModelPlaza',
          component: () => import('@/views/ModelPlaza.vue'),
          meta: { title: '模型广场', requiresAdmin: true }
        },
        {
          path: '/agent-config',
          name: 'AgentConfig',
          component: () => import('@/views/AgentConfig.vue'),
          meta: { title: '智能体配置', requiresAdmin: true }
        },
        {
          path: '/settings',
          name: 'Settings',
          component: () => import('@/views/Settings.vue'),
          meta: { title: '系统设置', requiresAdmin: true }
        }
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/NotFound.vue'),
      meta: { title: '页面不存在' }
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} · TestFlow`
  }

  // 检查是否需要认证
  if (to.meta.requiresAuth !== false) {
    if (!authStore.isAuthenticated) {
      ElMessage.warning('请先登录')
      next('/login')
      return
    }

    // 如果有token但没有用户信息，尝试获取用户信息
    if (!authStore.user) {
      try {
        await authStore.initUser()
      } catch (error) {
        next('/login')
        return
      }
    }

    // 检查管理员权限
    if (to.meta.requiresAdmin && !authStore.isAdmin) {
      ElMessage.error('权限不足')
      next('/')
      return
    }
  }

  // 如果已登录用户访问登录/注册页面，重定向到首页
  if ((to.name === 'Login' || to.name === 'Register') && authStore.isAuthenticated) {
    next('/')
    return
  }

  next()
})

export default router
