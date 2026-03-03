<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MODULE_NAV, TIERS } from '../nav/moduleNav'

const props = defineProps({
  tenant: { type: String, required: true },
  modules: { type: Array, required: true },
})

const route = useRoute()
const router = useRouter()

const moduleMap = computed(() => {
  const m = new Map()
  for (const row of props.modules) m.set(row.id, row)
  return m
})

const tree = computed(() => {
  return TIERS.map(t => {
    const children = MODULE_NAV
      .filter(x => x.tier === t.key)
      .map(x => ({ ...x, status: moduleMap.value.get(x.id) || null }))
      .filter(x => x.status?.enabled)  // ✅ enabled만
    return { ...t, children }
  }).filter(t => t.children.length > 0)
})

function go(path) {
  router.push(`/t/${props.tenant}/${path}`)
}

function isActive(path) {
  return route.path === `/t/${props.tenant}/${path}`
}
</script>

<template>
  <nav style="display:flex; flex-direction:column; gap:14px;">
    <div v-for="tier in tree" :key="tier.key">
      <div style="font-weight:700; margin: 6px 0 8px;">{{ tier.label }}</div>

      <div style="display:flex; flex-direction:column; gap:8px;">
        <button
          v-for="item in tier.children"
          :key="item.id"
          @click="go(item.path)"
          :style="{
            textAlign:'left',
            padding:'10px 10px',
            borderRadius:'12px',
            border:'1px solid #e5e7eb',
            background: isActive(item.path) ? '#f3f4f6' : '#fff',
            cursor:'pointer'
          }"
        >
          <div style="display:flex; align-items:center; justify-content:space-between; gap:10px;">
            <span>{{ item.label }}</span>
            <span style="font-size:12px; opacity:.75;">
              {{ item.status?.healthy ? '🟢' : '🔴' }}
            </span>
          </div>

          <div v-if="item.status" style="margin-top:8px;">
            <div style="height:6px; background:#e5e7eb; border-radius:999px; overflow:hidden;">
              <div
                :style="{
                  height:'6px',
                  width: Math.max(0, Math.min(100, item.status.trained_pct || 0)) + '%',
                  background:'#111827'
                }"
              />
            </div>
            <div style="font-size:12px; opacity:.75; margin-top:4px;">
              trained: {{ (item.status.trained_pct || 0).toFixed(1) }}%
            </div>
          </div>
        </button>
      </div>
    </div>
  </nav>
</template>