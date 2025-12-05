<template>
  <div class="concurrency-settings">
    <!-- 描述 -->
    <div class="mb-6">
      <p class="text-sm text-gray-500">配置AI生成任务的并发控制参数</p>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="py-12">
      <el-skeleton :rows="4" animated />
    </div>

    <!-- 配置表单 -->
    <div v-else class="bg-white border border-gray-200 rounded-2xl p-6">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="140px"
        label-position="left"
        class="max-w-xl"
      >
        <!-- 最大并发任务数 -->
        <el-form-item label="最大并发任务数" prop="max_concurrent_tasks">
          <div class="w-full">
            <el-input-number
              v-model="formData.max_concurrent_tasks"
              :min="1"
              :max="10"
              :step="1"
              controls-position="right"
              class="w-40"
            />
            <div class="text-xs text-gray-400 mt-2">
              同时执行的AI生成任务数量上限（范围：1-10）
            </div>
          </div>
        </el-form-item>

        <!-- 任务超时时间 -->
        <el-form-item label="任务超时时间" prop="task_timeout">
          <div class="w-full">
            <el-input-number
              v-model="formData.task_timeout"
              :min="60"
              :max="600"
              :step="30"
              controls-position="right"
              class="w-40"
            />
            <span class="ml-2 text-gray-500">秒</span>
            <div class="text-xs text-gray-400 mt-2">
              单个任务的最大执行时间（范围：60-600秒，默认300秒）
            </div>
          </div>
        </el-form-item>

        <!-- 失败重试次数 -->
        <el-form-item label="失败重试次数" prop="retry_count">
          <div class="w-full">
            <el-input-number
              v-model="formData.retry_count"
              :min="0"
              :max="5"
              :step="1"
              controls-position="right"
              class="w-40"
            />
            <div class="text-xs text-gray-400 mt-2">
              任务失败后的自动重试次数（范围：0-5）
            </div>
          </div>
        </el-form-item>

        <!-- 任务队列大小 -->
        <el-form-item label="任务队列大小" prop="queue_size">
          <div class="w-full">
            <el-input-number
              v-model="formData.queue_size"
              :min="10"
              :max="1000"
              :step="10"
              controls-position="right"
              class="w-40"
            />
            <div class="text-xs text-gray-400 mt-2">
              等待执行的任务队列最大容量（范围：10-1000）
            </div>
          </div>
        </el-form-item>
      </el-form>

      <!-- 操作按钮 -->
      <div class="flex justify-end gap-3 mt-8 pt-6 border-t border-gray-100">
        <button
          @click="handleReset"
          :disabled="!hasChanges"
          class="px-6 py-2.5 rounded-xl text-gray-600 font-bold hover:bg-gray-100 transition-all border border-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          重置修改
        </button>
        <button
          @click="handleSave"
          :disabled="!hasChanges || saving"
          class="px-6 py-2.5 bg-black text-white rounded-xl font-bold hover:bg-gray-800 transition-all shadow-lg shadow-black/20 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </div>

    <!-- 配置说明 -->
    <div class="mt-6 bg-blue-50 border border-blue-100 rounded-2xl p-6">
      <h4 class="text-sm font-bold text-blue-900 mb-3 flex items-center gap-2">
        <el-icon><InfoFilled /></el-icon>
        配置说明
      </h4>
      <ul class="text-sm text-blue-800 space-y-2">
        <li>• <strong>最大并发任务数</strong>：控制同时运行的AI生成任务数量，较高的值可以提高吞吐量，但会增加系统负载</li>
        <li>• <strong>任务超时时间</strong>：单个任务的最大执行时间，超时后任务将被终止并报告错误</li>
        <li>• <strong>失败重试次数</strong>：任务失败后自动重试的次数，设为0表示不重试</li>
        <li>• <strong>任务队列大小</strong>：等待执行的任务队列容量，超出后新任务将被拒绝</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import { settingsApi, type ConcurrencyConfig } from '@/api/settings'

// 加载状态
const loading = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()

// 原始配置（用于检测变更）
const originalConfig = ref<ConcurrencyConfig | null>(null)

// 表单数据
const formData = reactive<ConcurrencyConfig>({
  max_concurrent_tasks: 3,
  task_timeout: 300,
  retry_count: 3,
  queue_size: 100
})

// 表单验证规则
const formRules: FormRules = {
  max_concurrent_tasks: [
    { required: true, message: '请输入最大并发任务数', trigger: 'blur' },
    { type: 'number', min: 1, max: 10, message: '值必须在1-10之间', trigger: 'blur' }
  ],
  task_timeout: [
    { required: true, message: '请输入任务超时时间', trigger: 'blur' },
    { type: 'number', min: 30, max: 600, message: '值必须在30-600之间', trigger: 'blur' }
  ],
  retry_count: [
    { required: true, message: '请输入失败重试次数', trigger: 'blur' },
    { type: 'number', min: 0, max: 5, message: '值必须在0-5之间', trigger: 'blur' }
  ],
  queue_size: [
    { required: true, message: '请输入任务队列大小', trigger: 'blur' },
    { type: 'number', min: 10, max: 1000, message: '值必须在10-1000之间', trigger: 'blur' }
  ]
}

// 检测是否有变更
const hasChanges = computed(() => {
  if (!originalConfig.value) return false
  return (
    formData.max_concurrent_tasks !== originalConfig.value.max_concurrent_tasks ||
    formData.task_timeout !== originalConfig.value.task_timeout ||
    formData.retry_count !== originalConfig.value.retry_count ||
    formData.queue_size !== originalConfig.value.queue_size
  )
})

// 加载配置
const loadConfig = async () => {
  loading.value = true
  try {
    const config = await settingsApi.getConcurrencyConfig()
    originalConfig.value = { ...config }
    formData.max_concurrent_tasks = config.max_concurrent_tasks
    formData.task_timeout = config.task_timeout
    formData.retry_count = config.retry_count
    formData.queue_size = config.queue_size
  } catch (error: any) {
    console.error('加载并发配置失败:', error)
    ElMessage.error('加载并发配置失败')
  } finally {
    loading.value = false
  }
}

// 保存配置
const handleSave = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  saving.value = true
  try {
    const config: ConcurrencyConfig = {
      max_concurrent_tasks: formData.max_concurrent_tasks,
      task_timeout: formData.task_timeout,
      retry_count: formData.retry_count,
      queue_size: formData.queue_size
    }
    await settingsApi.updateConcurrencyConfig(config)
    originalConfig.value = { ...config }
    ElMessage.success('配置保存成功')
  } catch (error: any) {
    console.error('保存配置失败:', error)
    const message = error.response?.data?.detail || '保存配置失败'
    ElMessage.error(message)
  } finally {
    saving.value = false
  }
}

// 重置修改
const handleReset = () => {
  if (originalConfig.value) {
    formData.max_concurrent_tasks = originalConfig.value.max_concurrent_tasks
    formData.task_timeout = originalConfig.value.task_timeout
    formData.retry_count = originalConfig.value.retry_count
    formData.queue_size = originalConfig.value.queue_size
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
:deep(.el-input-number) {
  --el-input-number-unit-width: 32px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #374151;
}
</style>
