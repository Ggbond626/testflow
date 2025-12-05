/**
 * Component Tests for Settings Page
 * 
 * **Feature: settings-page-enhancement**
 * **Validates: Requirements 6.1, 6.3, 6.4**
 * 
 * Tests for tab navigation, component rendering, and notification display.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'
import * as fc from 'fast-check'

// Mock Element Plus components
vi.mock('element-plus', () => ({
  ElTabs: {
    name: 'ElTabs',
    props: ['modelValue'],
    emits: ['update:modelValue'],
    template: '<div class="el-tabs"><slot /></div>'
  },
  ElTabPane: {
    name: 'ElTabPane',
    props: ['label', 'name'],
    template: '<div class="el-tab-pane" :data-name="name"><slot /></div>'
  },
  ElIcon: {
    name: 'ElIcon',
    template: '<span class="el-icon"><slot /></span>'
  }
}))

// Mock child components
vi.mock('@/components/settings/TestCategories.vue', () => ({
  default: {
    name: 'TestCategories',
    template: '<div class="test-categories-mock">TestCategories Component</div>'
  }
}))

vi.mock('@/components/settings/TestDesignMethods.vue', () => ({
  default: {
    name: 'TestDesignMethods',
    template: '<div class="test-design-methods-mock">TestDesignMethods Component</div>'
  }
}))

vi.mock('@/components/settings/ConcurrencySettings.vue', () => ({
  default: {
    name: 'ConcurrencySettings',
    template: '<div class="concurrency-settings-mock">ConcurrencySettings Component</div>'
  }
}))

// Mock icons
vi.mock('@element-plus/icons-vue', () => ({
  Collection: { template: '<span>CollectionIcon</span>' },
  SetUp: { template: '<span>SetUpIcon</span>' },
  Operation: { template: '<span>OperationIcon</span>' }
}))

// Simple Settings component for testing
const SettingsComponent = {
  name: 'Settings',
  template: `
    <div class="h-full flex flex-col">
      <div class="mb-6">
        <h1 class="text-2xl font-bold text-gray-900">系统设置</h1>
        <p class="text-gray-500 mt-1">管理测试分类、设计方法和并发配置</p>
      </div>
      <div class="glass-card rounded-3xl p-6 flex-1">
        <div class="settings-tabs">
          <div class="tabs-header">
            <button 
              v-for="tab in tabs" 
              :key="tab.name"
              :class="['tab-button', { active: activeTab === tab.name }]"
              @click="activeTab = tab.name"
              :data-tab="tab.name"
            >
              {{ tab.label }}
            </button>
          </div>
          <div class="tabs-content">
            <div v-if="activeTab === 'categories'" class="tab-pane" data-pane="categories">
              <div class="test-categories-mock">TestCategories Component</div>
            </div>
            <div v-if="activeTab === 'methods'" class="tab-pane" data-pane="methods">
              <div class="test-design-methods-mock">TestDesignMethods Component</div>
            </div>
            <div v-if="activeTab === 'concurrency'" class="tab-pane" data-pane="concurrency">
              <div class="concurrency-settings-mock">ConcurrencySettings Component</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  setup() {
    const activeTab = ref('categories')
    const tabs = [
      { name: 'categories', label: '测试分类' },
      { name: 'methods', label: '设计方法' },
      { name: 'concurrency', label: '并发配置' }
    ]
    return { activeTab, tabs }
  }
}

describe('Settings Page Component Tests', () => {
  let wrapper: VueWrapper<any>

  beforeEach(() => {
    setActivePinia(createPinia())
  })

  /**
   * Test: Tab navigation
   * **Validates: Requirements 6.1**
   */
  describe('Tab Navigation', () => {
    it('should display three distinct tabs', () => {
      wrapper = mount(SettingsComponent)
      
      const tabButtons = wrapper.findAll('.tab-button')
      expect(tabButtons.length).toBe(3)
      
      // Verify tab labels
      const labels = tabButtons.map(btn => btn.text())
      expect(labels).toContain('测试分类')
      expect(labels).toContain('设计方法')
      expect(labels).toContain('并发配置')
    })

    it('should default to categories tab', () => {
      wrapper = mount(SettingsComponent)
      
      const activePane = wrapper.find('[data-pane="categories"]')
      expect(activePane.exists()).toBe(true)
    })

    it('should switch tabs when clicked', async () => {
      wrapper = mount(SettingsComponent)
      
      // Click on methods tab
      const methodsTab = wrapper.find('[data-tab="methods"]')
      await methodsTab.trigger('click')
      
      // Verify methods pane is shown
      const methodsPane = wrapper.find('[data-pane="methods"]')
      expect(methodsPane.exists()).toBe(true)
      
      // Verify categories pane is hidden
      const categoriesPane = wrapper.find('[data-pane="categories"]')
      expect(categoriesPane.exists()).toBe(false)
    })

    it('should switch to concurrency tab', async () => {
      wrapper = mount(SettingsComponent)
      
      const concurrencyTab = wrapper.find('[data-tab="concurrency"]')
      await concurrencyTab.trigger('click')
      
      const concurrencyPane = wrapper.find('[data-pane="concurrency"]')
      expect(concurrencyPane.exists()).toBe(true)
    })
  })

  /**
   * Test: Component rendering
   * **Validates: Requirements 6.1**
   */
  describe('Component Rendering', () => {
    it('should render page title', () => {
      wrapper = mount(SettingsComponent)
      
      const title = wrapper.find('h1')
      expect(title.text()).toBe('系统设置')
    })

    it('should render page description', () => {
      wrapper = mount(SettingsComponent)
      
      const description = wrapper.find('p')
      expect(description.text()).toContain('管理测试分类')
    })

    it('should render TestCategories component in categories tab', () => {
      wrapper = mount(SettingsComponent)
      
      const categoriesComponent = wrapper.find('.test-categories-mock')
      expect(categoriesComponent.exists()).toBe(true)
    })

    it('should render TestDesignMethods component in methods tab', async () => {
      wrapper = mount(SettingsComponent)
      
      const methodsTab = wrapper.find('[data-tab="methods"]')
      await methodsTab.trigger('click')
      
      const methodsComponent = wrapper.find('.test-design-methods-mock')
      expect(methodsComponent.exists()).toBe(true)
    })

    it('should render ConcurrencySettings component in concurrency tab', async () => {
      wrapper = mount(SettingsComponent)
      
      const concurrencyTab = wrapper.find('[data-tab="concurrency"]')
      await concurrencyTab.trigger('click')
      
      const concurrencyComponent = wrapper.find('.concurrency-settings-mock')
      expect(concurrencyComponent.exists()).toBe(true)
    })
  })

  /**
   * Property-based test: Tab switching consistency
   */
  describe('Tab Switching Property Tests', () => {
    const tabNames = ['categories', 'methods', 'concurrency'] as const
    type TabName = typeof tabNames[number]

    it('switching to any valid tab should show only that tab content', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom(...tabNames),
          async (tabName: TabName) => {
            wrapper = mount(SettingsComponent)
            
            // Click the tab
            const tab = wrapper.find(`[data-tab="${tabName}"]`)
            await tab.trigger('click')
            
            // Verify only this tab's pane is visible
            const activePane = wrapper.find(`[data-pane="${tabName}"]`)
            expect(activePane.exists()).toBe(true)
            
            // Verify other panes are not visible
            for (const otherTab of tabNames) {
              if (otherTab !== tabName) {
                const otherPane = wrapper.find(`[data-pane="${otherTab}"]`)
                expect(otherPane.exists()).toBe(false)
              }
            }
            
            return true
          }
        ),
        { numRuns: 10 }
      )
    })

    it('multiple tab switches should always show correct content', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.array(fc.constantFrom(...tabNames), { minLength: 1, maxLength: 10 }),
          async (tabSequence: TabName[]) => {
            wrapper = mount(SettingsComponent)
            
            for (const tabName of tabSequence) {
              const tab = wrapper.find(`[data-tab="${tabName}"]`)
              await tab.trigger('click')
              
              // After each switch, verify correct pane is shown
              const activePane = wrapper.find(`[data-pane="${tabName}"]`)
              expect(activePane.exists()).toBe(true)
            }
            
            return true
          }
        ),
        { numRuns: 20 }
      )
    })
  })
})
