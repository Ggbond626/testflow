import { defineStore } from 'pinia'
import { ref } from 'vue'
import { projectApi, type Project, type ProjectDetail, type ProjectListParams } from '@/api/project'
import { ElMessage } from 'element-plus'
import { useAuthStore } from './auth'

export const useProjectStore = defineStore('project', () => {
  // 状态
  const projects = ref<Project[]>([])
  const currentProject = ref<ProjectDetail | null>(null)
  const loading = ref(false)
  const total = ref(0)

  // 获取项目列表
  const getProjectList = async (params?: ProjectListParams) => {
    loading.value = true
    try {
      const authStore = useAuthStore()
      // 根据用户角色选择不同的API
      const response = authStore.user?.role === 'admin'
        ? await projectApi.getAllProjectsAdmin(params)
        : await projectApi.getProjectList(params)
      projects.value = response.projects
      total.value = response.total
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  // 获取项目详情
  const getProject = async (projectId: number) => {
    loading.value = true
    try {
      const authStore = useAuthStore()
      // 根据用户角色选择不同的API
      const project = authStore.user?.role === 'admin'
        ? await projectApi.getProjectAdmin(projectId)
        : await projectApi.getProject(projectId)
      currentProject.value = project
      return project
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  // 创建项目
  const createProject = async (projectData: { name: string; description?: string }) => {
    try {
      const authStore = useAuthStore()
      // 根据用户角色选择不同的API
      const project = authStore.user?.role === 'admin'
        ? await projectApi.createProjectAdmin(projectData)
        : await projectApi.createProject(projectData)
      projects.value.unshift(project)
      total.value += 1
      ElMessage.success('项目创建成功')
      return project
    } catch (error) {
      throw error
    }
  }

  // 更新项目
  const updateProject = async (projectId: number, updateData: { name?: string; description?: string }) => {
    try {
      const updatedProject = await projectApi.updateProject(projectId, updateData)
      
      // 更新列表中的项目
      const index = projects.value.findIndex(p => p.id === projectId)
      if (index !== -1) {
        projects.value[index] = updatedProject
      }
      
      // 更新当前项目
      if (currentProject.value && currentProject.value.id === projectId) {
        currentProject.value = { ...currentProject.value, ...updatedProject }
      }
      
      ElMessage.success('项目更新成功')
      return updatedProject
    } catch (error) {
      throw error
    }
  }

  // 删除项目
  const deleteProject = async (projectId: number) => {
    try {
      const authStore = useAuthStore()
      // 根据用户角色选择不同的API
      if (authStore.user?.role === 'admin') {
        await projectApi.deleteProjectAdmin(projectId)
      } else {
        await projectApi.deleteProject(projectId)
      }
      
      // 从列表中移除
      projects.value = projects.value.filter(p => p.id !== projectId)
      total.value -= 1
      
      // 清除当前项目
      if (currentProject.value && currentProject.value.id === projectId) {
        currentProject.value = null
      }
      
      ElMessage.success('项目删除成功')
    } catch (error) {
      throw error
    }
  }

  // 添加项目成员
  const addProjectMember = async (projectId: number, memberData: { user_id: number; role: 'member' | 'viewer' }) => {
    try {
      const member = await projectApi.addProjectMember(projectId, memberData)
      
      // 更新当前项目的成员列表
      if (currentProject.value && currentProject.value.id === projectId) {
        currentProject.value.members.push(member)
        currentProject.value.member_count += 1
      }
      
      ElMessage.success('成员添加成功')
      return member
    } catch (error) {
      throw error
    }
  }

  // 移除项目成员
  const removeProjectMember = async (projectId: number, userId: number) => {
    try {
      await projectApi.removeProjectMember(projectId, userId)
      
      // 更新当前项目的成员列表
      if (currentProject.value && currentProject.value.id === projectId) {
        currentProject.value.members = currentProject.value.members.filter(m => m.user_id !== userId)
        currentProject.value.member_count -= 1
      }
      
      ElMessage.success('成员移除成功')
    } catch (error) {
      throw error
    }
  }

  // 清除当前项目
  const clearCurrentProject = () => {
    currentProject.value = null
  }

  // 重置状态
  const reset = () => {
    projects.value = []
    currentProject.value = null
    loading.value = false
    total.value = 0
  }

  return {
    // 状态
    projects,
    currentProject,
    loading,
    total,
    
    // 方法
    getProjectList,
    getProject,
    createProject,
    updateProject,
    deleteProject,
    addProjectMember,
    removeProjectMember,
    clearCurrentProject,
    reset
  }
})
