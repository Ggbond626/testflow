<template>
  <div class="agent-config">
    <div class="page-header mb-6 flex justify-between items-center">
      <p class="text-gray-500">配置和管理AI智能体，设置不同的智能体角色和参数以优化测试生成效果</p>
      <button @click="refreshAgents" class="bg-white hover:bg-gray-50 text-gray-900 px-4 py-2 rounded-xl font-bold border border-gray-200 transition-colors flex items-center gap-2">
        <el-icon><Refresh /></el-icon>
        刷新
      </button>
    </div>

    <!-- 智能体列表 -->
    <div v-loading="loading" class="min-h-[200px]">
      <div v-if="agents.length === 0 && !loading" class="text-center py-16">
        <el-empty description="暂无智能体配置" :image-size="120" />
      </div>
      
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div 
          v-for="agent in agents" 
          :key="agent.id" 
          class="glass-card rounded-3xl p-6 flex flex-col h-full hover:-translate-y-1 transition-transform duration-300"
        >
          <!-- 卡片头部 -->
          <div class="flex justify-between items-start mb-6">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-2xl flex items-center justify-center text-xl" 
                :class="getAgentIconBg(agent.type)">
                <el-icon :class="getAgentIconColor(agent.type)">
                  <component :is="getAgentIcon(agent.type)" />
                </el-icon>
              </div>
              <div>
                <h3 class="font-bold text-lg text-gray-900">{{ getAgentDisplayName(agent.type) }}</h3>
                <span class="text-xs font-medium px-2 py-0.5 rounded-md bg-gray-100 text-gray-500">
                  {{ getAgentTypeName(agent.type) }}
                </span>
              </div>
            </div>
            <div class="flex flex-col items-end gap-2">
              <span class="px-2 py-1 rounded-lg text-xs font-bold" 
                :class="agent.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'">
                {{ agent.is_active ? '已激活' : '未激活' }}
              </span>
            </div>
          </div>
          
          <!-- 卡片内容 -->
          <div class="flex-1 space-y-4 mb-6">
            <!-- 关联模型 -->
            <div class="flex justify-between items-center p-3 rounded-xl bg-white/40 border border-gray-100">
              <div class="flex items-center gap-2 text-sm text-gray-600 font-medium">
                <el-icon><Connection /></el-icon>
                关联模型
              </div>
              <div class="font-bold text-sm text-gray-900">
                {{ agent.ai_model_name || '未设置' }}
              </div>
            </div>
            
            <!-- 温度参数 -->
            <div class="p-3 rounded-xl bg-white/40 border border-gray-100">
              <div class="flex justify-between items-center mb-2">
                <div class="flex items-center gap-2 text-sm text-gray-600 font-medium">
                  <el-icon><Sunny /></el-icon>
                  温度参数
                </div>
                <span class="font-mono text-sm font-bold text-gray-900">{{ agent.temperature }}</span>
              </div>
              <div class="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div class="h-full bg-black rounded-full" :style="{ width: `${(agent.temperature / 2) * 100}%` }"></div>
              </div>
            </div>
            
            <!-- 最大令牌数 -->
            <div class="flex justify-between items-center p-3 rounded-xl bg-white/40 border border-gray-100">
              <div class="flex items-center gap-2 text-sm text-gray-600 font-medium">
                <el-icon><Coin /></el-icon>
                最大令牌
              </div>
              <div class="font-mono text-sm font-bold text-gray-900">
                {{ agent.max_tokens }}
              </div>
            </div>
            
            <!-- 系统提示词预览 -->
            <div v-if="agent.system_prompt" class="p-3 rounded-xl bg-white/40 border border-gray-100">
              <div class="flex items-center gap-2 text-sm text-gray-600 font-medium mb-2">
                <el-icon><Document /></el-icon>
                系统提示词
              </div>
              <p class="text-xs text-gray-500 line-clamp-2 leading-relaxed">
                {{ agent.system_prompt }}
              </p>
            </div>
          </div>
          
          <!-- 卡片操作 -->
          <button 
            @click="editAgent(agent)"
            class="w-full py-2.5 bg-black hover:bg-gray-800 text-white rounded-xl font-bold transition-colors flex items-center justify-center gap-2 shadow-lg shadow-black/10"
          >
            <el-icon><Edit /></el-icon>
            编辑配置
          </button>
        </div>
      </div>
    </div>

    <!-- 编辑智能体对话框 -->
    <el-dialog 
      v-model="showEditDialog" 
      title="编辑智能体配置" 
      width="700px"
      class="!rounded-3xl"
    >
      <el-form :model="agentForm" label-width="120px" class="mt-4">

        
        <el-form-item label="智能体类型">
          <div class="px-3 py-1.5 bg-gray-100 rounded-lg text-sm font-bold text-gray-700 inline-block">
            {{ getAgentTypeName(agentForm.type) }}
          </div>
        </el-form-item>
        
        <el-form-item label="关联模型">
          <el-select v-model="agentForm.ai_model_id" placeholder="请选择AI模型" class="w-full">
            <el-option 
              v-for="model in availableModels" 
              :key="model.id" 
              :label="model.name" 
              :value="model.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="温度参数">
          <div class="flex items-center gap-4 w-full">
            <el-slider v-model="agentForm.temperature" :min="0" :max="2" :step="0.1" class="flex-1" />
            <span class="font-mono font-bold w-12 text-right">{{ agentForm.temperature }}</span>
          </div>
        </el-form-item>
        
        <el-form-item label="最大令牌数">
          <el-input-number v-model="agentForm.max_tokens" :min="100" :max="128000" :step="100" class="!w-full" />
        </el-form-item>
        
        <el-form-item label="系统提示词">
          <el-input 
            v-model="agentForm.system_prompt" 
            type="textarea" 
            :rows="8"
            placeholder="请输入系统提示词，定义智能体的角色和输出格式要求..."
            class="custom-input"
          />
          <div class="text-xs text-gray-400 mt-1">定义AI的角色、任务和JSON输出格式（用户提示词模板由系统统一管理）</div>
        </el-form-item>
        
        <el-form-item label="状态">
          <div class="flex flex-col gap-2">
            <el-switch 
              v-model="agentForm.is_active" 
              active-text="激活" 
              inactive-text="停用" 
            />
            <div class="flex items-center gap-2 text-xs text-gray-400 bg-gray-50 p-2 rounded-lg">
              <el-icon><InfoFilled /></el-icon>
              <span>需要先关联AI模型才能激活智能体</span>
            </div>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="flex justify-end gap-3">
          <button @click="cancelEdit" class="px-5 py-2 rounded-xl text-gray-600 font-bold hover:bg-gray-100 transition-colors">取消</button>
          <button @click="saveAgent" :disabled="saving" class="px-5 py-2 bg-black text-white rounded-xl font-bold hover:bg-gray-800 transition-colors shadow-lg shadow-black/20">
            保存配置
          </button>
        </div>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Edit, Connection, Sunny, Coin, Document, InfoFilled, Cpu, DataAnalysis, List, MagicStick } from '@element-plus/icons-vue'
import { aiModelApi } from '@/api/aiModel'
import api from '@/api/index'
import { useAuthStore } from '@/stores/auth'

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const agents = ref<any[]>([])
const availableModels = ref<any[]>([])
const showEditDialog = ref(false)
const editingAgent = ref<any>(null)

// 认证store
const authStore = useAuthStore()

// 表单数据
const agentForm = ref({
  name: '',
  type: '',
  ai_model_id: null,
  temperature: 0.7,
  max_tokens: 2000,
  system_prompt: '',
  is_active: false
})

// 方法
const refreshAgents = async () => {
  loading.value = true
  try {
    // 检查认证状态
    if (!authStore.isAuthenticated) {
      console.warn('用户未认证，无法获取智能体列表')
      agents.value = []
      return
    }
    
    // 使用统一的API实例获取智能体列表
    const data = await api.get('/api/ai/agents') as any[]
    agents.value = Array.isArray(data) ? data : []
  } catch (error: any) {
    console.error('获取智能体列表失败:', error)
    agents.value = []
  } finally {
    loading.value = false
  }
}

// 加载可用的AI模型
const loadAvailableModels = async () => {
  try {
    const models = await aiModelApi.getAIModels({ is_active: true })
    availableModels.value = models
  } catch (error) {
    console.error('获取AI模型列表失败:', error)
    availableModels.value = []
  }
}

const editAgent = (agent: any) => {
  editingAgent.value = agent
  agentForm.value = { ...agent }
  showEditDialog.value = true
}

const saveAgent = async () => {
  saving.value = true
  try {
    // 使用统一的API实例更新智能体配置
    await api.put(`/api/ai/agents/${editingAgent.value.id}`, {
      ai_model_id: agentForm.value.ai_model_id,
      temperature: agentForm.value.temperature,
      max_tokens: agentForm.value.max_tokens,
      system_prompt: agentForm.value.system_prompt,
      is_active: agentForm.value.is_active
    })
    
    ElMessage.success('配置保存成功')
    cancelEdit()
    refreshAgents()
  } catch (error: any) {
    console.error('保存智能体配置失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const cancelEdit = () => {
  showEditDialog.value = false
  editingAgent.value = null
  agentForm.value = {
    name: '',
    type: '',
    ai_model_id: null,
    temperature: 0.7,
    max_tokens: 2000,
    system_prompt: '',
    is_active: false
  }
}

const getAgentTypeName = (type: string) => {
  const names: Record<string, string> = {
    requirement_splitter: '需求分析',
    test_point_generator: '测试分析',
    test_case_designer: '用例设计',
    test_case_optimizer: '用例优化'
  }
  return names[type] || type
}

const getAgentDisplayName = (type: string) => {
  const names: Record<string, string> = {
    requirement_splitter: '需求分析',
    test_point_generator: '测试分析',
    test_case_designer: '用例设计',
    test_case_optimizer: '用例优化'
  }
  return names[type] || type
}

const getAgentIcon = (type: string) => {
  const icons: Record<string, any> = {
    requirement_splitter: 'List',
    test_point_generator: 'DataAnalysis',
    test_case_designer: 'Edit',
    test_case_optimizer: 'MagicStick'
  }
  return icons[type] || 'Cpu'
}

const getAgentIconBg = (type: string) => {
  const bgs: Record<string, string> = {
    requirement_splitter: 'bg-gray-100',
    test_point_generator: 'bg-gray-100',
    test_case_designer: 'bg-gray-100',
    test_case_optimizer: 'bg-gray-100'
  }
  return bgs[type] || 'bg-gray-50'
}

const getAgentIconColor = (type: string) => {
  const colors: Record<string, string> = {
    requirement_splitter: 'text-gray-900',
    test_point_generator: 'text-gray-900',
    test_case_designer: 'text-gray-900',
    test_case_optimizer: 'text-gray-900'
  }
  return colors[type] || 'text-gray-500'
}

// 生命周期
onMounted(() => {
  refreshAgents()
  loadAvailableModels()
})
</script>

<style scoped>
:deep(.el-input__wrapper) {
  background-color: #f9fafb;
  box-shadow: 0 0 0 1px #e5e7eb inset;
  border-radius: 0.75rem;
  padding: 4px 12px;
}
:deep(.el-input__wrapper.is-focus) {
  background-color: #ffffff;
  box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.1) inset !important;
}
</style>
