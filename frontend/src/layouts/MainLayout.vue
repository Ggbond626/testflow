<template>
  <div class="h-screen flex overflow-hidden p-4 gap-4 bg-transparent">
    <!-- Floating Sidebar -->
    <aside 
      class="glass-sidebar rounded-3xl flex-shrink-0 flex flex-col transition-all duration-300 shadow-2xl shadow-black/20 z-20"
      :class="isCollapse ? 'w-20' : 'w-64'"
    >
      <div class="h-20 flex items-center justify-center">
        <div class="flex items-center gap-3 font-bold text-2xl tracking-tight text-black">
          <div class="w-10 h-10 shadow-lg shadow-black/20 rounded-xl overflow-hidden">
            <img src="@/assets/logo.svg" alt="TestFlow Logo" class="w-full h-full" />
          </div>
          <span v-if="!isCollapse" class="hidden lg:block animate-fade-in">TestFlow</span>
        </div>
      </div>

      <nav class="flex-1 overflow-y-auto py-6 px-4 space-y-2 custom-scrollbar">
        <!-- Regular Menu Item -->
        <template v-for="item in menuItems" :key="item.index">
          <router-link 
            v-if="!item.adminOnly || authStore.isAdmin"
            :to="item.index"
            class="flex items-center gap-4 px-4 py-3.5 rounded-2xl transition-all group"
            :class="isActive(item.index) ? 'bg-black text-white shadow-xl shadow-black/20 transform -translate-y-0.5' : 'text-gray-500 hover:text-black hover:bg-gray-100'"
          >
            <el-icon class="text-lg group-hover:scale-110 transition-transform" :class="isActive(item.index) ? 'text-white' : ''">
              <component :is="item.icon" />
            </el-icon>
            <span v-if="!isCollapse" class="font-medium hidden lg:block">{{ item.title }}</span>
          </router-link>
        </template>
      </nav>

      <div class="p-6 border-t border-gray-200/50">
        <div class="flex items-center gap-3 p-3 rounded-2xl bg-white/50 border border-white/60 shadow-sm cursor-pointer hover:bg-white/80 transition-colors" @click="toggleCollapse">
          <el-icon size="20" class="text-gray-600">
            <Expand v-if="isCollapse" />
            <Fold v-else />
          </el-icon>
          <div v-if="!isCollapse" class="flex-1 min-w-0 hidden lg:block">
            <p class="text-sm font-bold text-gray-800 truncate">收起菜单</p>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content Area -->
    <main class="flex-1 flex flex-col min-w-0 glass rounded-3xl overflow-hidden shadow-2xl shadow-black/30 relative z-10">
      
      <!-- Header -->
      <header class="h-20 flex items-center justify-between px-8 z-10 border-b border-gray-200/50 bg-white/40 backdrop-blur-sm flex-shrink-0">
        <div class="flex items-center gap-4">
          <h1 class="text-2xl font-bold text-gray-900 tracking-tight">{{ currentRouteTitle }}</h1>
        </div>
        
        <div class="flex items-center gap-4">

          
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="flex items-center gap-3 cursor-pointer pl-2">
               <div class="w-10 h-10 rounded-full bg-black text-white flex items-center justify-center font-bold shadow-lg shadow-black/20">
                  {{ authStore.user?.username?.charAt(0).toUpperCase() }}
               </div>
            </div>
            <template #dropdown>
              <el-dropdown-menu class="!rounded-xl !border-0 !shadow-xl">
                <el-dropdown-item command="profile" class="!py-3 !px-6 !font-medium">
                  <el-icon><User /></el-icon> 个人资料
                </el-dropdown-item>
                <el-dropdown-item divided command="logout" class="!py-3 !px-6 !font-medium !text-red-500">
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- Router View Content -->
      <div class="flex-1 overflow-auto p-8 custom-scrollbar relative">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessageBox } from 'element-plus'
import {
  House,
  Folder,
  Shop,
  Operation,
  User,
  Setting,
  Expand,
  Fold,
  Search,
  SwitchButton
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isCollapse = ref(false)

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const isActive = (path: string) => route.path === path

const currentRouteTitle = computed(() => route.meta.title || '仪表盘')

const menuItems = [
  { title: '仪表盘', index: '/', icon: House },
  { title: '项目管理', index: '/projects', icon: Folder },
  { title: '模型广场', index: '/model-plaza', icon: Shop, adminOnly: true },
  { title: '智能体配置', index: '/agent-config', icon: Operation, adminOnly: true },
  { title: '用户管理', index: '/users', icon: User, adminOnly: true },
  { title: '系统设置', index: '/settings', icon: Setting, adminOnly: true },
]

const handleCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '退出登录', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
          confirmButtonClass: '!bg-black !border-black',
        })
        await authStore.logout()
      } catch (error) {
        // Cancelled
      }
      break
  }
}
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Transition for router view */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

</style>
