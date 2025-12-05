<template>
  <div class="test-design-methods">
    <!-- 操作栏 -->
    <div class="mb-6 flex justify-between items-center">
      <p class="text-sm text-gray-500">配置测试用例生成时使用的设计方法论</p>
      <div class="flex gap-3">
        <button
          @click="handleResetDefaults"
          class="px-4 py-2 border border-gray-200 text-gray-700 rounded-xl text-sm font-bold hover:bg-gray-50 transition-colors flex items-center gap-2"
        >
          <el-icon><RefreshRight /></el-icon>
          重置默认
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="py-12">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 空状态 -->
    <div v-else-if="methods.length === 0" class="text-center py-16">
      <el-empty description="暂无测试设计方法">
        <button
          @click="handleAdd"
          class="mt-4 px-6 py-2 bg-black text-white rounded-xl text-sm font-bold hover:bg-gray-800 transition-colors"
        >
          添加第一个方法
        </button>
      </el-empty>
    </div>

    <!-- 方法列表表格 -->
    <div v-else class="bg-white border border-gray-200 rounded-2xl overflow-hidden">
      <el-table
        :data="methods"
        row-key="id"
        style="width: 100%"
      >

        <el-table-column prop="name" label="名称" width="200">
          <template #default="{ row }">
            <span class="font-medium">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="code" label="代码" width="260">
          <template #default="{ row }">
            <code class="px-2 py-1 bg-gray-100 rounded text-sm">{{ row.code }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="260">
          <template #default="{ row }">
            <span class="text-gray-600">{{ row.description || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              @change="handleToggleActive(row)"
              :loading="row._updating"
            />
          </template>
        </el-table-column>
        <el-table-column prop="is_default" label="默认" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="info" size="small">默认</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <div class="flex items-center justify-center gap-2">
              <button
                @click="handleEdit(row)"
                class="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600 hover:text-black"
                title="编辑"
              >
                <el-icon><Edit /></el-icon>
              </button>
              <button
                @click="handleDelete(row)"
                :disabled="row.is_default"
                :class="[
                  'p-2 rounded-lg transition-colors',
                  row.is_default 
                    ? 'text-gray-300 cursor-not-allowed' 
                    : 'hover:bg-red-50 text-gray-600 hover:text-red-600'
                ]"
                :title="row.is_default ? '默认方法不可删除' : '删除'"
              >
                <el-icon><Delete /></el-icon>
              </button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingMethod ? '编辑测试设计方法' : '添加测试设计方法'"
      width="500px"
      :close-on-click-modal="false"
      align-center
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="80px"
        class="pr-4"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入方法名称" />
        </el-form-item>
        <el-form-item label="代码" prop="code">
          <el-input
            v-model="formData.code"
            placeholder="请输入唯一代码（英文）"
            :disabled="!!editingMethod"
          />
          <div class="text-xs text-gray-400 mt-1">代码用于系统内部标识，创建后不可修改</div>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入方法描述（可选）"
          />
        </el-form-item>
        <el-form-item label="启用" prop="is_active">
          <el-switch v-model="formData.is_active" />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="flex justify-end gap-3">
          <button
            @click="dialogVisible = false"
            class="px-6 py-2.5 rounded-xl text-gray-600 font-bold hover:bg-gray-100 transition-all border border-gray-200"
          >
            取消
          </button>
          <button
            @click="handleSubmit"
            :disabled="submitting"
            class="px-6 py-2.5 bg-black text-white rounded-xl font-bold hover:bg-gray-800 transition-all shadow-lg shadow-black/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ submitting ? '保存中...' : '保存' }}
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Edit, Delete, RefreshRight } from '@element-plus/icons-vue'
import { settingsApi, type TestDesignMethodResponse, type TestDesignMethodCreate, type TestDesignMethodUpdate } from '@/api/settings'

// 方法列表
const methods = ref<(TestDesignMethodResponse & { _updating?: boolean })[]>([])
const loading = ref(false)

// 对话框状态
const dialogVisible = ref(false)
const editingMethod = ref<TestDesignMethodResponse | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

// 表单数据
const formData = reactive({
  name: '',
  code: '',
  description: '',
  is_active: true,
  order_index: 0
})

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入方法名称', trigger: 'blur' },
    { min: 1, max: 50, message: '名称长度应在1-50个字符之间', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入方法代码', trigger: 'blur' },
    { pattern: /^[a-z][a-z0-9_]*$/, message: '代码必须以小写字母开头，只能包含小写字母、数字和下划线', trigger: 'blur' }
  ]
}

// 加载方法列表
const loadMethods = async () => {
  loading.value = true
  try {
    const data = await settingsApi.getDesignMethods()
    methods.value = data.sort((a, b) => a.order_index - b.order_index)
  } catch (error: any) {
    console.error('加载测试设计方法失败:', error)
    ElMessage.error('加载测试设计方法失败')
  } finally {
    loading.value = false
  }
}

// 添加方法
const handleAdd = () => {
  editingMethod.value = null
  formData.name = ''
  formData.code = ''
  formData.description = ''
  formData.is_active = true
  formData.order_index = methods.value.length
  dialogVisible.value = true
}

// 编辑方法
const handleEdit = (row: TestDesignMethodResponse) => {
  editingMethod.value = row
  formData.name = row.name
  formData.code = row.code
  formData.description = row.description || ''
  formData.is_active = row.is_active
  formData.order_index = row.order_index
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    if (editingMethod.value) {
      // 更新
      const updateData: TestDesignMethodUpdate = {
        name: formData.name,
        description: formData.description || null,
        is_active: formData.is_active,
        order_index: formData.order_index
      }
      await settingsApi.updateDesignMethod(editingMethod.value.id, updateData)
      ElMessage.success('更新成功')
    } else {
      // 创建
      const createData: TestDesignMethodCreate = {
        name: formData.name,
        code: formData.code,
        description: formData.description || null,
        is_active: formData.is_active,
        order_index: formData.order_index
      }
      await settingsApi.createDesignMethod(createData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadMethods()
  } catch (error: any) {
    console.error('保存失败:', error)
    const message = error.response?.data?.detail || '保存失败'
    ElMessage.error(message)
  } finally {
    submitting.value = false
  }
}

// 切换启用状态
const handleToggleActive = async (row: TestDesignMethodResponse & { _updating?: boolean }) => {
  row._updating = true
  try {
    await settingsApi.updateDesignMethod(row.id, { is_active: row.is_active })
    ElMessage.success(row.is_active ? '已启用' : '已禁用')
  } catch (error: any) {
    console.error('更新状态失败:', error)
    row.is_active = !row.is_active // 回滚
    ElMessage.error('更新状态失败')
  } finally {
    row._updating = false
  }
}

// 删除方法
const handleDelete = async (row: TestDesignMethodResponse) => {
  // 默认方法不允许删除
  if (row.is_default) {
    ElMessage.warning('默认方法不可删除')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除方法"${row.name}"吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await settingsApi.deleteDesignMethod(row.id)
    ElMessage.success('删除成功')
    loadMethods()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 重置为默认
const handleResetDefaults = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重置为默认方法吗？这将恢复系统预设的测试设计方法。',
      '确认重置',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await settingsApi.resetDesignMethods()
    ElMessage.success('已重置为默认方法')
    loadMethods()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('重置失败:', error)
      ElMessage.error('重置失败')
    }
  }
}

onMounted(() => {
  loadMethods()
})
</script>

<style scoped>
:deep(.el-table) {
  --el-table-border-color: #e5e7eb;
  --el-table-header-bg-color: #f9fafb;
}

:deep(.el-table th) {
  font-weight: 600;
  color: #374151;
}
</style>
