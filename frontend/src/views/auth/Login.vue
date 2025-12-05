<template>
  <div class="min-h-screen flex w-full">
    <!-- Left Side: TestFlow Pipeline Visualization -->
    <div class="hidden lg:flex lg:w-1/2 items-center justify-center relative">
      
      <!-- SVG Core -->
      <div class="tech-container w-[500px] h-[500px] md:w-[600px] md:h-[600px]">
        <svg viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg" class="w-full h-full">
          <defs>
            <!-- Gradients -->
            <linearGradient id="metal-top" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#3f3f46"/>
              <stop offset="50%" style="stop-color:#52525b"/>
              <stop offset="100%" style="stop-color:#27272a"/>
            </linearGradient>
            <linearGradient id="metal-left" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" style="stop-color:#27272a"/>
              <stop offset="100%" style="stop-color:#18181b"/>
            </linearGradient>
            <!-- Brand Gradients -->
            <linearGradient id="brand-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#3B82F6"/> <!-- Blue-500 -->
              <stop offset="100%" style="stop-color:#6366F1"/> <!-- Indigo-500 -->
            </linearGradient>
            <linearGradient id="glow-brand" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style="stop-color:rgba(59,130,246,0)"/>
              <stop offset="50%" style="stop-color:#3B82F6"/>
              <stop offset="100%" style="stop-color:rgba(99,102,241,0)"/>
            </linearGradient>
            <linearGradient id="glow-success" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style="stop-color:rgba(16,185,129,0)"/>
              <stop offset="50%" style="stop-color:#10B981"/> <!-- Emerald-500 -->
              <stop offset="100%" style="stop-color:rgba(16,185,129,0)"/>
            </linearGradient>
            <linearGradient id="stream-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
               <stop offset="0%" style="stop-color:rgba(59,130,246,0)"/>
               <stop offset="50%" style="stop-color:#3B82F6"/>
               <stop offset="100%" style="stop-color:rgba(99,102,241,0)"/>
            </linearGradient>
            
            <!-- Glow Filter -->
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>

          <!-- Background Grid (Subtle) -->
          <g opacity="0.1">
            <line x1="50" y1="250" x2="450" y2="250" stroke="#3B82F6" stroke-width="0.5"/>
            <line x1="250" y1="100" x2="250" y2="400" stroke="#3B82F6" stroke-width="0.5"/>
          </g>

          <!-- === INPUT PIPELINE (Left) === -->
          <g transform="translate(80, 250)">
            <!-- Input Node -->
            <circle cx="0" cy="0" r="20" fill="#18181b" stroke="url(#brand-gradient)" stroke-width="1.5"/>
            <circle cx="0" cy="0" r="8" fill="#3B82F6" opacity="0.8">
              <animate attributeName="r" values="6;10;6" dur="2s" repeatCount="indefinite"/>
              <animate attributeName="opacity" values="0.8;0.4;0.8" dur="2s" repeatCount="indefinite"/>
            </circle>
            
            <!-- Flow Line to Core -->
            <path d="M 25 0 L 100 0" stroke="url(#stream-gradient)" stroke-width="2" stroke-dasharray="8,4" opacity="0.5">
              <animate attributeName="stroke-dashoffset" from="24" to="0" dur="1s" repeatCount="indefinite"/>
            </path>
            
            <!-- Data Particle -->
            <circle r="4" fill="#3B82F6" filter="url(#glow)">
              <animateMotion path="M 25 0 L 100 0" dur="1.5s" repeatCount="indefinite"/>
              <animate attributeName="opacity" values="0;1;1;0" dur="1.5s" repeatCount="indefinite"/>
            </circle>
          </g>

          <!-- === MAIN PROCESSING CORE (Center) === -->
          <g transform="translate(250, 250)">
            
            <!-- Outer Glow Ring -->
            <ellipse cx="0" cy="60" rx="100" ry="30" fill="none" stroke="url(#brand-gradient)" stroke-width="1" opacity="0.3" stroke-dasharray="10 5">
              <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="20s" repeatCount="indefinite"/>
            </ellipse>

            <!-- Shadow -->
            <ellipse cx="0" cy="75" rx="70" ry="20" fill="#000" opacity="0.4" filter="blur(8px)"/>

            <!-- 3D Isometric Core -->
            <!-- Bottom Layer -->
            <path d="M -80 30 L 0 70 L 80 30 L 80 45 L 0 85 L -80 45 Z" fill="#0a0a0a" stroke="#27272a" stroke-width="0.5"/>
            
            <!-- Energy Band (Brand Gradient) -->
            <path d="M -80 20 L 0 60 L 80 20 L 80 30 L 0 70 L -80 30 Z" fill="url(#brand-gradient)" filter="url(#glow)"/>
            
            <!-- Main Body -->
            <g>
              <path d="M -80 -30 L 0 10 L 0 60 L -80 20 Z" fill="url(#metal-left)"/>
              <path d="M 80 -30 L 0 10 L 0 60 L 80 20 Z" fill="#3f3f46"/>
              <path d="M -80 -30 L 0 10 L 80 -30 L 0 -70 Z" fill="url(#metal-top)" stroke="#52525b" stroke-width="0.5"/>
            </g>

            <!-- Top Chip Area -->
            <g transform="translate(0, -20)">
              <!-- Recessed Area -->
              <path d="M -40 -15 L 0 5 L 40 -15 L 0 -35 Z" fill="#111"/>
              
              <!-- Processing Chip -->
              <g transform="translate(0, -10)">
                <path d="M -15 0 L 0 8 L 15 0 L 0 -8 Z" fill="#3B82F6" opacity="0.9">
                  <animate attributeName="opacity" values="0.9;0.4;0.9" dur="2s" repeatCount="indefinite"/>
                </path>
                <!-- Chip Connectors -->
                <line x1="-15" y1="0" x2="-30" y2="8" stroke="#3B82F6" stroke-width="1" opacity="0.6"/>
                <line x1="15" y1="0" x2="30" y2="8" stroke="#3B82F6" stroke-width="1" opacity="0.6"/>
                <line x1="0" y1="-8" x2="0" y2="-25" stroke="#3B82F6" stroke-width="1" opacity="0.6"/>
              </g>
            </g>

            <!-- Side Data Indicator -->
            <g transform="translate(-75, 0) skewY(26.5)">
              <rect x="5" y="5" width="0" height="2" fill="#3B82F6" opacity="0.7">
                <animate attributeName="width" values="0;25;0" dur="1.5s" repeatCount="indefinite"/>
              </rect>
            </g>

            <!-- Brand Label on Side -->
            <text x="35" y="42" fill="rgba(255,255,255,0.5)" font-family="monospace" font-size="7" transform="skewY(-26.5)">TESTFLOW</text>
          </g>

          <!-- === OUTPUT PIPELINE (Right) === -->
          <g transform="translate(420, 250)">
            <!-- Output Node (Success) -->
            <circle cx="0" cy="0" r="20" fill="#18181b" stroke="#40E0D0" stroke-width="1.5"/>
            <!-- Checkmark (Logo Style) -->
            <path d="M -6 1 L -2 5 L 7 -4" stroke="#40E0D0" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round" filter="url(#glow)"/>
            
            <!-- Flow Line from Core -->
            <path d="M -100 0 L -25 0" stroke="#40E0D0" stroke-width="2" stroke-dasharray="8,4" opacity="0.6">
              <animate attributeName="stroke-dashoffset" from="0" to="-24" dur="1s" repeatCount="indefinite"/>
            </path>
            
            <!-- Success Particle -->
            <circle r="4" fill="#40E0D0" filter="url(#glow)">
              <animateMotion path="M -100 0 L -25 0" dur="1.5s" begin="0.75s" repeatCount="indefinite"/>
              <animate attributeName="opacity" values="0;1;1;0" dur="1.5s" begin="0.75s" repeatCount="indefinite"/>
            </circle>
          </g>

          <!-- === TOP INDICATOR (Status) === -->
          <g transform="translate(250, 130)">
            <!-- Status Pulse -->
            <circle cx="0" cy="0" r="6" fill="#3B82F6" opacity="0.8">
              <animate attributeName="r" values="4;8;4" dur="3s" repeatCount="indefinite"/>
              <animate attributeName="opacity" values="0.8;0.3;0.8" dur="3s" repeatCount="indefinite"/>
            </circle>
            <text x="0" y="-15" fill="rgba(255,255,255,0.5)" font-size="9" font-family="'Outfit', sans-serif" font-weight="500" text-anchor="middle" letter-spacing="0.1em">PROCESSING</text>
          </g>

        </svg>
      </div>
    </div>

    <!-- Right Side: Login Form (Original Style) -->
    <div class="w-full lg:w-1/2 flex items-center justify-center p-4">
      <div class="glass-card w-full max-w-md p-8 rounded-3xl animate-fade-in">
        <div class="text-center mb-8">
          <div class="w-16 h-16 mx-auto mb-6 shadow-lg shadow-black/20 rounded-2xl overflow-hidden">
            <img src="@/assets/logo.svg" alt="TestFlow Logo" class="w-full h-full" />
          </div>
          <h2 class="text-2xl font-bold text-gray-900 tracking-tight">欢迎回来</h2>
          <p class="text-sm text-gray-500 mt-2">请登录以继续使用 TestFlow</p>
        </div>
        
        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="space-y-6"
          @submit.prevent="handleLogin"
        >
          <el-form-item prop="username" class="!mb-0">
            <div class="space-y-1.5 w-full">
              <label class="text-sm font-bold text-gray-700 ml-1">用户名</label>
              <el-input
                v-model="loginForm.username"
                placeholder="请输入用户名"
                size="large"
                :prefix-icon="User"
                class="custom-input w-full"
              />
            </div>
          </el-form-item>
          
          <el-form-item prop="password" class="!mb-0">
            <div class="space-y-1.5 w-full">
              <label class="text-sm font-bold text-gray-700 ml-1">密码</label>
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                :prefix-icon="Lock"
                show-password
                class="custom-input w-full"
                @keyup.enter="handleLogin"
              />
            </div>
          </el-form-item>
          
          <div class="pt-4 flex justify-center">
            <button
              type="button"
              class="w-2/3 bg-black hover:bg-gray-800 text-white py-3.5 rounded-xl font-bold shadow-lg shadow-black/20 transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2"
              :disabled="authStore.loading"
              @click="handleLogin"
            >
              <el-icon v-if="authStore.loading" class="is-loading"><Loading /></el-icon>
              <span>{{ authStore.loading ? '登录中...' : '登 录' }}</span>
            </button>
          </div>
        </el-form>
        
        <div class="mt-8 text-center space-y-6">
          <p class="text-sm text-gray-500">
            还没有账号？
            <router-link to="/register" class="text-black font-bold hover:underline">
              立即注册
            </router-link>
          </p>
          
          <div class="pt-6 border-t border-gray-200/50">
            <p class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-4">演示账号</p>
            <div class="flex gap-3 justify-center">
              <button
                class="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-xs font-bold transition-colors"
                @click="fillDemoAccount('admin')"
              >
                管理员
              </button>
              <button
                class="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-xs font-bold transition-colors"
                @click="fillDemoAccount('demo')"
              >
                普通用户
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Loading } from '@element-plus/icons-vue'

const authStore = useAuthStore()

// 表单引用
const loginFormRef = ref<FormInstance>()

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: ''
})

// 表单验证规则
const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '最少 3 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '最少 6 个字符', trigger: 'blur' }
  ]
}

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  try {
    await loginFormRef.value.validate()
    await authStore.login(loginForm)
  } catch (error: any) {
    // 显示后端返回的错误消息
    ElMessage.error(error.message || '登录失败，请重试')
  }
}

// 填充演示账号
const fillDemoAccount = (type: 'admin' | 'demo') => {
  if (type === 'admin') {
    loginForm.username = 'admin'
    loginForm.password = 'admin123'
  } else {
    loginForm.username = 'demo'
    loginForm.password = 'demo123'
  }
}
</script>

<style scoped>
/* ========== Holographic Animations ========== */

/* Core Levitation */
@keyframes stable-levitate {
  0% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
  100% { transform: translateY(0); }
}

/* Holographic Base Spin */
@keyframes holo-spin {
  from { transform: rotate(0deg) scale(1, 0.6); }
  to { transform: rotate(360deg) scale(1, 0.6); }
}

@keyframes holo-spin-reverse {
  from { transform: rotate(360deg) scale(1, 0.6); }
  to { transform: rotate(0deg) scale(1, 0.6); }
}

/* Energy Pulse */
@keyframes energy-pulse {
  0%, 100% { opacity: 0.5; stroke-width: 1; }
  50% { opacity: 1; stroke-width: 2; filter: drop-shadow(0 0 5px #3B82F6); }
}

/* Particle Float */
@keyframes particle-float {
  0% { transform: translate(0, 0); opacity: 0; }
  20% { opacity: 0.8; }
  80% { opacity: 0.8; }
  100% { transform: translate(-20px, -40px); opacity: 0; }
}

.tech-container {
  position: relative;
  animation: stable-levitate 8s infinite ease-in-out;
}

.holo-ring-1 {
  transform-origin: center;
  animation: holo-spin 10s infinite linear;
  opacity: 0.3;
}

.holo-ring-2 {
  transform-origin: center;
  animation: holo-spin-reverse 15s infinite linear;
  opacity: 0.2;
}

.energy-line {
  stroke: #3B82F6;
  fill: none;
  stroke-linecap: round;
  animation: energy-pulse 2s infinite ease-in-out;
}

.glass-surface {
  fill: rgba(59, 130, 246, 0.05);
  stroke: rgba(59, 130, 246, 0.3);
  stroke-width: 0.5;
}

.particle {
  width: 4px;
  height: 4px;
  background-color: #3B82F6;
  border-radius: 50%;
  animation: particle-float 4s infinite;
}

/* ========== Original Input Styles ========== */
:deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.6) inset;
  border-radius: 0.75rem;
  padding: 8px 16px;
  transition: all 0.2s;
  width: 100%;
}

:deep(.el-input__wrapper.is-focus) {
  background-color: #ffffff;
  box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.1) inset !important;
}

:deep(.el-input__inner) {
  height: 28px;
  color: #374151;
  font-weight: 500;
}
</style>
