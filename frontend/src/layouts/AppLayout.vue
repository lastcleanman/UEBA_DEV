<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import TenantSelector from '../components/TenantSelector.vue'
import SideNavTree from '../components/SideNavTree.vue'
import { fetchModules } from '../api/modules'

const route = useRoute()
const tenant = computed(() => route.params.tenant || 'acme')

const modules = ref([])
const loading = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    modules.value = await fetchModules(tenant.value)
  } catch (e) {
    error.value = e?.message || 'failed to load modules'
    modules.value = []
  } finally {
    loading.value = false
  }
}

watch(tenant, () => load(), { immediate: true })
</script>

<template>
  <div style="display:grid; grid-template-columns: 300px 1fr; min-height: 100vh;">
    <aside style="padding:16px; border-right:1px solid #e5e7eb;">
      <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:14px;">
        <TenantSelector :tenants="['acme','bravo']" />
        <button @click="load" style="padding:6px 10px; border-radius:10px; border:1px solid #e5e7eb; background:#fff; cursor:pointer;">
          Refresh
        </button>
      </div>

      <div v-if="loading" style="opacity:.7;">Loading modules...</div>
      <div v-else-if="error" style="color:#b91c1c;">{{ error }}</div>
      <SideNavTree v-else :tenant="tenant" :modules="modules" />
    </aside>

    <main style="padding:18px;">
      <router-view />
    </main>
  </div>
</template>