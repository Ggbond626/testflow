<template>
  <div class="project-settings">
    <!-- 基本信息 -->
    <div class="bg-white/50 rounded-2xl border border-gray-100 p-6 mb-6">
      <h3 class="text-lg font-bold text-gray-900 mb-4">基本信息</h3>
      
      <el-form
        ref="formRef"
        :model="projectForm"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="projectForm.name" :disabled="!canEdit" />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="projectForm.description"
            type="textarea"
            :rows="4"
            :disabled="!canEdit"
          />
        </el-form-item>
        <el-form-item v-if="canEdit">
          <button
            @click="handleUpdate"
            :disabled="updating"
            class="px-6 py-2 bg-black text-white rounded-xl font-bold hover:bg-gray-800 transition-colors shadow-lg shadow-black/20"
          >
            保存更改
          </button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 危险操作 -->
    <div v-if="canEdit" class="bg-red-50 rounded-2xl border border-red-200 p-6">
      <h3 class="text-lg font-bold text-red-700 mb-2">危险操作</h3>
      <p class="text-sm text-red-600 mb-4">
        删除项目将永久删除所有相关数据，包括模块、需求、测试用例等。此操作不可恢复！
      </p>
      <button
        @click="handleDelete"
        class="px-6 py-2 bg-red-600 text-white rounded-xl font-bold hover:bg-red-700 transition-colors shadow-lg shadow-red-600/20"
      >
        删除项目
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { projectApi, type Project } from '@/api/project'

const props = defineProps<{
  projectId: number
  canEdit: boolean
}>()

const emit = defineEmits<{
  (e: 'project-updated', project: Project): void
}>()

const router = useRouter()

// 表单状态
const formRef = ref<FormInstance>()
const projectForm = ref({
  name: '',
  description: ''
})
const updating = ref(false)

// 表单验证
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 1, max: 100, message: '项目名称长度在1-100个字符', trigger: 'blur' }
  ]
}

// 加载项目信息
const loadProject = async () => {
  try {
    const project = await projectApi.getProject(props.projectId)
    projectForm.value = {
      name: project.name,
      description: project.description || ''
    }
  } catch (error: any) {
    console.error('加载项目失败:', error)
    ElMessage.error('加载项目失败')
  }
}

// 更新项目
const handleUpdate = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    updating.value = true

    const updated = await projectApi.updateProject(props.projectId, projectForm.value)
    ElMessage.success('项目更新成功')
    emit('project-updated', updated)
  } catch (error: any) {
    console.error('更新失败:', error)
    ElMessage.error(error.response?.data?.detail || '更新失败')
  } finally {
    updating.value = false
  }
}

// 删除项目
const handleDelete = async () => {
  try {
    // 第一次确认
    await ElMessageBox.confirm(
      '删除项目将永久删除所有相关数据，此操作不可恢复！',
      '确认删除',
      {
        confirmButtonText: '继续',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: '!bg-red-600 !border-red-600'
      }
    )

    // 第二次确认：输入项目名称
    const { value: inputName } = await ElMessageBox.prompt(
      `请输入项目名称 "${projectForm.value.name}" 以确认删除`,
      '二次确认',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        inputPattern: new RegExp(`^${projectForm.value.name}$`),
        inputErrorMessage: '项目名称不匹配',
        confirmButtonClass: '!bg-red-600 !border-red-600'
      }
    )

    if (inputName === projectForm.value.name) {
      await projectApi.deleteProject(props.projectId)
      ElMessage.success('项目删除成功')
      router.push('/projects')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除项目失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 初始化
onMounted(() => {
  loadProject()
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

:deep(.el-input__wrapper:disabled) {
  background-color: #f3f4f6;
}
</style>

