<template>
  <div class="model-plaza">
    <div class="mb-6 flex justify-between items-center">
      <p class="text-gray-500">浏览和管理AI模型，配置不同的语言模型以满足您的测试需求</p>
      <button @click="showCreateDialog = true" class="bg-black hover:bg-gray-800 text-white px-6 py-2.5 rounded-xl font-bold shadow-lg shadow-black/20 transition-all transform hover:-translate-y-0.5 flex items-center gap-2">
        <el-icon><Plus /></el-icon>
        添加模型
      </button>
    </div>

    <!-- 模型列表 -->
    <div v-loading="loading" class="min-h-[200px]">
      <div v-if="models.length === 0 && !loading" class="text-center py-16">
        <el-empty description="暂无模型配置" :image-size="120" />
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div 
          v-for="model in models" 
          :key="model.id" 
          class="glass-card rounded-3xl p-6 flex flex-col hover:-translate-y-1 transition-transform duration-300"
        >
          <!-- 卡片头部 -->
          <div class="flex justify-between items-start mb-6">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 bg-black/5 rounded-2xl flex items-center justify-center text-xl">
                <el-icon class="text-black"><Connection /></el-icon>
              </div>
              <div>
                <h3 class="font-bold text-lg text-gray-900 line-clamp-1" :title="model.name">{{ model.name }}</h3>
                <span class="text-xs font-medium px-2 py-0.5 rounded-md bg-gray-100 text-gray-500 uppercase">
                  {{ model.provider }}
                </span>
              </div>
            </div>
            <span class="px-2 py-1 rounded-lg text-xs font-bold" 
              :class="model.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'">
              {{ model.is_active ? '已激活' : '未激活' }}
            </span>
          </div>

          <!-- 卡片内容 -->
          <div class="flex-1 space-y-4 mb-6">
            <!-- 模型ID -->
            <div class="p-3 rounded-xl bg-white/40 border border-gray-100">
              <div class="text-xs text-gray-500 mb-1">模型ID</div>
              <div class="font-mono text-sm font-bold text-gray-900 break-all">{{ model.model_id }}</div>
            </div>

            <!-- API地址 -->
            <div class="p-3 rounded-xl bg-white/40 border border-gray-100">
              <div class="text-xs text-gray-500 mb-1">API地址</div>
              <div class="text-sm text-gray-900 truncate" :title="model.base_url">{{ model.base_url }}</div>
            </div>

            <!-- 参数信息 -->
            <div class="flex gap-3">
              <div class="flex-1 p-3 rounded-xl bg-white/40 border border-gray-100">
                <div class="text-xs text-gray-500 mb-1">最大令牌</div>
                <div class="font-mono text-sm font-bold text-gray-900">{{ model.max_tokens }}</div>
              </div>
              <div class="flex-1 p-3 rounded-xl bg-white/40 border border-gray-100">
                <div class="text-xs text-gray-500 mb-1">温度参数</div>
                <div class="font-mono text-sm font-bold text-gray-900">{{ model.temperature }}</div>
              </div>
            </div>
          </div>

          <!-- 卡片操作 -->
          <div class="grid grid-cols-3 gap-3">
            <button 
              @click="testModel(model)" 
              :disabled="testingModelId === model.id"
              class="py-2 bg-white hover:bg-gray-50 text-gray-700 border border-gray-200 rounded-xl font-bold transition-colors flex items-center justify-center gap-1 text-sm"
            >
              <el-icon v-if="testingModelId === model.id" class="is-loading"><Loading /></el-icon>
              <el-icon v-else><MagicStick /></el-icon>
              测试
            </button>
            <button 
              @click="editModel(model)"
              class="py-2 bg-black hover:bg-gray-800 text-white rounded-xl font-bold transition-colors flex items-center justify-center gap-1 text-sm shadow-lg shadow-black/10"
            >
              <el-icon><Edit /></el-icon>
              编辑
            </button>
            <button 
              @click="deleteModel(model)"
              class="py-2 bg-red-50 hover:bg-red-100 text-red-600 border border-red-100 rounded-xl font-bold transition-colors flex items-center justify-center gap-1 text-sm"
            >
              <el-icon><Delete /></el-icon>
              删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑模型对话框 -->
    <el-dialog 
      v-model="showCreateDialog" 
      :title="editingModel ? '编辑模型' : '添加模型'" 
      width="700px"
      @close="resetForm"
      class="!rounded-3xl"
    >
      <el-form 
        ref="formRef"
        :model="modelForm" 
        :rules="formRules"
        label-width="120px"
        class="mt-4"
      >
        <el-form-item label="模型名称" prop="name">
          <el-input 
            v-model="modelForm.name" 
            placeholder="请输入模型显示名称，如：GPT-4 Turbo"
            class="custom-input"
          />
        </el-form-item>
        
        <el-form-item label="模型提供商" prop="provider">
          <el-select 
            v-model="modelForm.provider" 
            placeholder="请选择模型提供商"
            style="width: 100%"
            class="w-full"
          >
            <el-option label="OpenAI" value="openai" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="模型ID" prop="model_id">
          <el-input 
            v-model="modelForm.model_id" 
            placeholder="请输入模型ID，如：gpt-4-turbo-preview"
            class="custom-input"
          />
        </el-form-item>
        
        <el-form-item label="API地址" prop="base_url">
          <el-input 
            v-model="modelForm.base_url" 
            placeholder="请输入OpenAI兼容的API地址，如：https://api.openai.com/v1"
            class="custom-input"
          />
        </el-form-item>
        
        <el-form-item label="API密钥" prop="api_key">
          <el-input 
            v-model="modelForm.api_key" 
            type="password" 
            placeholder="请输入API密钥（可选）"
            show-password
            clearable
            class="custom-input"
          />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最大令牌" prop="max_tokens">
              <el-input-number 
                v-model="modelForm.max_tokens" 
                :min="100" 
                :max="128000" 
                :step="100"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="温度参数" prop="temperature">
              <el-input-number 
                v-model="modelForm.temperature" 
                :min="0" 
                :max="2" 
                :step="0.1"
                :precision="1"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="流式支持">
          <el-switch 
            v-model="modelForm.stream_support" 
            active-text="支持" 
            inactive-text="不支持" 
          />
        </el-form-item>
        
        <el-form-item label="状态">
          <el-switch 
            v-model="modelForm.is_active" 
            active-text="激活" 
            inactive-text="停用" 
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="flex justify-end gap-3">
          <button @click="cancelEdit" class="px-5 py-2 rounded-xl text-gray-600 font-bold hover:bg-gray-100 transition-colors">取消</button>
          <button @click="saveModel" :disabled="saving" class="px-5 py-2 bg-black text-white rounded-xl font-bold hover:bg-gray-800 transition-colors shadow-lg shadow-black/20">
            {{ editingModel ? '更新' : '创建' }}
          </button>
        </div>
      </template>
    </el-dialog>

    <!-- 测试结果对话框 -->
    <el-dialog 
      v-model="showTestDialog" 
      title="模型测试结果" 
      width="600px"
      class="!rounded-3xl"
    >
      <div class="test-result">
        <el-alert 
          v-if="testResult.success"
          title="测试成功" 
          type="success" 
          :description="testResult.message"
          show-icon
          :closable="false"
          class="!rounded-xl"
        />
        <el-alert 
          v-else
          title="测试失败" 
          type="error" 
          :description="testResult.message"
          show-icon
          :closable="false"
          class="!rounded-xl"
        />
        
        <div v-if="testResult.response" class="mt-6 p-4 bg-gray-50 rounded-xl border border-gray-100">
          <h4 class="text-sm font-bold text-gray-700 mb-2">响应详情：</h4>
          <pre class="text-xs text-gray-600 overflow-auto max-h-60 bg-white p-3 rounded-lg border border-gray-200">{{ JSON.stringify(testResult.response, null, 2) }}</pre>
        </div>
      </div>
      
      <template #footer>
        <div class="flex justify-end">
          <button @click="showTestDialog = false" class="px-5 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-bold transition-colors">关闭</button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Loading, Connection, MagicStick, Edit, Delete } from '@element-plus/icons-vue'
import { aiModelApi } from '@/api/aiModel'

// 接口定义
interface AIModel {
  id?: number
  name: string
  provider: string
  model_id: string
  base_url: string
  api_key?: string  // 编辑时需要，列表显示时不需要
  max_tokens: number
  temperature: number
  stream_support: boolean
  is_active: boolean
}

interface TestResult {
  success: boolean
  message: string
  response?: any
}

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const testingModelId = ref<number | null>(null)
const models = ref<AIModel[]>([])
const showCreateDialog = ref(false)
const showTestDialog = ref(false)
const editingModel = ref<AIModel | null>(null)
const formRef = ref<FormInstance>()

// 表单数据
const modelForm = ref<AIModel>({
  name: '',
  provider: 'openai',
  model_id: '',
  base_url: '',
  api_key: '',
  max_tokens: 4000,
  temperature: 0.7,
  stream_support: true,
  is_active: true
})

// 测试结果
const testResult = ref<TestResult>({
  success: false,
  message: '',
  response: null
})

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' },
    { min: 1, max: 100, message: '模型名称长度在1-100个字符', trigger: 'blur' }
  ],
  model_id: [
    { required: true, message: '请输入模型ID', trigger: 'blur' },
    { min: 1, max: 100, message: '模型ID长度在1-100个字符', trigger: 'blur' }
  ],
  base_url: [
    { required: true, message: '请输入API地址', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL地址', trigger: 'blur' }
  ],
  api_key: [
    // API密钥可选，无长度限制
  ],
  max_tokens: [
    { required: true, message: '请输入最大令牌数', trigger: 'blur' }
  ],
  temperature: [
    { required: true, message: '请输入温度参数', trigger: 'blur' }
  ]
}

// 方法
const refreshModels = async () => {
  loading.value = true
  try {
    const response = await aiModelApi.getAIModels()
    models.value = response
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取模型列表失败')
  } finally {
    loading.value = false
  }
}

const testModel = async (model: AIModel) => {
  if (!model.id) return
  
  testingModelId.value = model.id
  try {
    const response = await aiModelApi.testAIModel(model.id, {
      message: 'Hello, this is a test message.'
    })
    
    testResult.value = response
    showTestDialog.value = true
  } catch (error: any) {
    testResult.value = {
      success: false,
      message: error.response?.data?.detail || '模型测试失败，请检查配置',
      response: null
    }
    showTestDialog.value = true
  } finally {
    testingModelId.value = null
  }
}

const editModel = async (model: AIModel) => {
  if (!model.id) return
  
  try {
    // 获取包含API密钥的完整模型信息
    const fullModel = await aiModelApi.getAIModelDetail(model.id)
    editingModel.value = model
    modelForm.value = { ...fullModel }
    showCreateDialog.value = true
  } catch (error: any) {
    ElMessage.error('获取模型详情失败')
  }
}

const deleteModel = async (model: AIModel) => {
  if (!model.id) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除模型 "${model.name}" 吗？`,
      '确认删除',
      { 
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: '!bg-black !border-black',
      }
    )
    
    await aiModelApi.deleteAIModel(model.id)
    ElMessage.success('删除成功')
    refreshModels()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const saveModel = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    saving.value = true
    
    if (editingModel.value && editingModel.value.id) {
      // 更新模型
      await aiModelApi.updateAIModel(editingModel.value.id, modelForm.value)
      ElMessage.success('模型更新成功')
    } else {
      // 创建模型
      const createData = {
        ...modelForm.value,
        api_key: modelForm.value.api_key || ''
      }
      await aiModelApi.createAIModel(createData)
      ElMessage.success('模型创建成功')
    }
    
    cancelEdit()
    refreshModels()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const cancelEdit = () => {
  showCreateDialog.value = false
  editingModel.value = null
  resetForm()
}

const resetForm = () => {
  modelForm.value = {
    name: '',
    provider: 'openai',
    model_id: '',
    base_url: '',
    api_key: '',
    max_tokens: 4000,
    temperature: 0.7,
    stream_support: true,
    is_active: true
  }
  formRef.value?.resetFields()
}

// 生命周期
onMounted(() => {
  refreshModels()
})
</script>

<style scoped>
:deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.6) inset;
  border-radius: 0.75rem;
  padding: 8px 16px;
  transition: all 0.2s;
}
:deep(.el-input__wrapper.is-focus) {
  background-color: #ffffff;
  box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.1) inset !important;
}
</style>
