<script setup>
import { reactive, watch } from 'vue'

// ⭐️ 백엔드에서 전달받은 메뉴 데이터
const props = defineProps({
  menuGroups: {
    type: Array,
    default: () => []
  }
})

// 메뉴 접힘/열림 상태 관리
const open = reactive({})

// 메뉴 데이터가 로드되면 기본적으로 모든 그룹을 열어둡니다.
watch(() => props.menuGroups, (newGroups) => {
  newGroups.forEach(g => {
    if (!(g.key in open)) {
      open[g.key] = true 
    }
  })
}, { immediate: true, deep: true })

function toggle(key) { 
  open[key] = !open[key] 
}
</script>

<template>
  <nav class="nav">
    <router-link class="top" to="/dashboard">📊 통합 대시보드</router-link>

    <div class="divider"></div>

    <section v-for="g in menuGroups" :key="g.key" class="group">
      <button class="groupBtn" type="button" @click="toggle(g.key)">
        <span class="chev" :class="{ open: open[g.key] }">▸</span>
        <span class="label">{{ g.label }}</span>
      </button>

      <div v-show="open[g.key]" class="items">
        <router-link 
          v-for="it in g.items" 
          :key="it.id" 
          class="item" 
          :to="it.to"
        >
          {{ it.label }}
        </router-link>
      </div>
    </section>
  </nav>
</template>

<style scoped>
/* (이전과 동일한 CSS 유지 - 하드코딩 없음, 테마 변수 100% 적용) */
.nav { display:flex; flex-direction:column; gap:10px; font-size: 1.05rem; }
.top { color: var(--text-main); text-decoration:none; padding:12px 10px; border-radius:10px; background: transparent; transition: background 0.2s; font-weight: bold; }
.top:hover { background: var(--btn-hover); }
.top.router-link-active { background: var(--btn-bg); font-weight:800; color: var(--primary-color); }
.divider { height:1px; background: var(--border-color); margin: 6px 0; }
.group { display:flex; flex-direction:column; gap:6px; }
.groupBtn{ display:flex; align-items:center; gap:8px; width:100%; font-size: 1.05rem; border:0; background:transparent; color: var(--text-main); padding:10px 8px; border-radius:10px; cursor:pointer; text-align:left; transition: background 0.2s; }
.groupBtn:hover { background: var(--btn-hover); }
.chev { display:inline-block; transition: transform 0.12s ease; opacity:0.9; }
.chev.open { transform: rotate(90deg); }
.label { font-weight:bold; }
.items { display:flex; flex-direction:column; gap:6px; padding-left: 18px; margin-top: 4px; }
.item { color: var(--text-muted); text-decoration:none; padding:8px 10px; border-radius:10px; transition: all 0.2s; font-size: 0.95rem; }
.item:hover { color: var(--text-main); background: var(--btn-hover); }
.item.router-link-active { color: var(--primary-color); background: var(--btn-bg); font-weight:bold; }
</style>