<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import SideNav from '@/core_components/nav/SideNav.vue'
import TenantSelector from '@/components/TenantSelector.vue'
import { fetchModules } from '@/api/modules'

// ⭐️ 추가: 테마 설정 및 토글 함수 가져오기
import { currentTheme, toggleTheme } from '@/config/theme.js'

const route = useRoute()
const router = useRouter()

const tenant = computed(() => route.params.tenant || 'acme')
const modules = ref([])
const loading = ref(false)
const error = ref('')

async function loadModules() {
  loading.value = true
  error.value = ''
  try {
    const result = await fetchModules(tenant.value)
    modules.value = Array.isArray(result) ? result : []
  } catch (e) {
    error.value = e?.message || 'failed to load modules'
    modules.value = []
  } finally {
    loading.value = false
  }
}

watch(tenant, () => loadModules(), { immediate: true })

// ⭐️ 복구: 테넌트 변경 함수 (에러 해결!)
function onChangeTenant(nextTenant) {
  const rest = route.fullPath.replace(/^\/t\/[^/]+/, '')
  router.push(`/t/${nextTenant}${rest}`)
}
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="topbar">
        <TenantSelector
          :value="tenant"
          :tenants="['acme','bravo']"
          @change="onChangeTenant"
        />
        
        <div class="action-buttons">
          <button class="btn theme-btn" @click="toggleTheme">
            {{ currentTheme === 'dark' ? '☀️' : '🌙' }}
          </button>
          <button class="btn" @click="loadModules">Refresh</button>
        </div>
      </div>

      <SideNav :menu-groups="modules" />
    </aside>

    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
/* ⭐️ 수정: 하드코딩된 색상(#1e1e1e 등)을 var(--변수명)으로 변경하여 테마 시스템에 연동 */
.layout { display:grid; grid-template-columns: 300px 1fr; min-height:100vh; }
.sidebar { 
  border-right: 1px solid var(--border-color); 
  padding: 16px; 
  background-color: var(--bg-panel); 
  transition: background-color 0.3s ease, border-color 0.3s ease;
} 
.content { padding: 18px; }
.topbar { display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:12px; }
.action-buttons { display: flex; gap: 8px; }

.btn { 
  padding: 6px 10px; 
  border-radius: 8px; 
  border: 1px solid var(--border-color); 
  background: var(--btn-bg); 
  color: var(--btn-text);
  cursor: pointer; 
  transition: 0.2s;
}
.btn:hover { 
  background: var(--btn-hover); 
}
.theme-btn { font-size: 1.1rem; padding: 4px 8px; }

.muted { opacity:.7; }
.error { color:#b91c1c; }
</style>