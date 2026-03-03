<template>
  <div class="log-terminal-container">
    <div class="header">
      <div class="title">
        <h3>📡 실시간 로그 수집 모니터링</h3>
        <span class="status-dot" :class="{ bad: !allHealthy }"></span>
      </div>

      <div class="controls">
        <label class="ctl">
          read_from
          <select v-model="readFrom">
            <option value="end">end (tail)</option>
            <option value="begin">begin (from start)</option>
          </select>
        </label>

        <label class="ctl">
          source
          <select v-model="sourceId">
            <option value="file_event">file_event</option>
            <option value="syslog_event">syslog_event</option>
          </select>
        </label>

        <button class="btn" @click="applyReadFrom">Apply</button>
      </div>
    </div>

    <div class="terminal-window" ref="terminalBody">
      <div v-if="logs.length === 0" class="empty-msg">대기 중... 로그 데이터가 없습니다.</div>
      <div v-for="(log, index) in logs" :key="index" class="log-line">
        <span class="tenant">[{{ log.tenant_id }}]</span>
        <span class="source">[{{ log.source_id }}]</span>
        <span class="text">{{ log.raw_data }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'

const logs = ref([])
const terminalBody = ref(null)
let intervalId = null

const tenantId = ref('acme')
const sourceId = ref('file_event')
const readFrom = ref('end')
const allHealthy = ref(true)

const fetchStatus = async () => {
  try {
    const r = await fetch('/api/v1/collectors/status')
    const j = await r.json()
    if (j.status === 'success') {
      // 하나라도 unhealthy면 점을 빨갛게
      allHealthy.value = j.collectors.every(c => c.healthy && c.running)

      // 현재 선택된 source의 config(read_from) UI 동기화
      const cur = j.collectors.find(c => c.tenant_id === tenantId.value && c.source_id === sourceId.value)
      if (cur?.config?.read_from) {
        readFrom.value = cur.config.read_from
      }
    }
  } catch (e) {
    allHealthy.value = false
  }
}

const fetchLogs = async () => {
  try {
    const response = await fetch('/api/v1/collectors/stream?limit=50')
    const result = await response.json()

    if (result.status === 'success') {
      // 선택한 source만 보고 싶으면 필터
      logs.value = result.data.filter(x => x.tenant_id === tenantId.value && x.source_id === sourceId.value)

      nextTick(() => {
        if (terminalBody.value) {
          terminalBody.value.scrollTop = terminalBody.value.scrollHeight
        }
      })
    }
  } catch (error) {
    console.error("로그 수집 스트림 연결 실패:", error)
  }
}

const applyReadFrom = async () => {
  try {
    const res = await fetch('/api/v1/collectors/config/read_from', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tenant_id: tenantId.value,
        source_id: sourceId.value,
        read_from: readFrom.value,
      }),
    })
    const j = await res.json()
    if (j.status !== 'success') {
      console.error('applyReadFrom failed:', j)
    }
    await fetchStatus()
  } catch (e) {
    console.error('applyReadFrom error:', e)
  }
}

onMounted(() => {
  fetchStatus()
  fetchLogs()
  intervalId = setInterval(async () => {
    await fetchStatus()
    await fetchLogs()
  }, 1000)
})

onUnmounted(() => {
  clearInterval(intervalId)
})
</script>

<style scoped>
.log-terminal-container { background-color: var(--bg-panel); border-radius: 8px; overflow: hidden; border: 1px solid var(--border-color); box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; transition: all 0.3s ease; }
.header { background-color: var(--bg-base); border-bottom: 1px solid var(--border-color); padding: 12px 15px; display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.title { display: flex; align-items: center; gap: 10px; }
.header h3 { margin: 0; font-size: 1.1rem; color: var(--text-main); }

.controls { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.ctl { display: flex; align-items: center; gap: 6px; font-size: 0.95rem; color: var(--text-main); font-weight: 500;}
select { background: var(--bg-panel); color: var(--text-main); border: 1px solid var(--border-color); border-radius: 6px; padding: 6px 10px; font-size: 0.95rem; }
.btn { background: var(--btn-bg); color: var(--btn-text); border: 1px solid var(--border-color); border-radius: 6px; padding: 6px 12px; cursor: pointer; transition: 0.2s; font-weight: bold; }
.btn:hover { background: var(--btn-hover); }

.status-dot { width: 12px; height: 12px; background-color: #4ade80; border-radius: 50%; box-shadow: 0 0 8px #4ade80; animation: pulse 1.5s infinite; }
.status-dot.bad { background-color: #f87171; box-shadow: 0 0 8px #f87171; }

.terminal-window { height: 400px; padding: 15px; overflow-y: auto; background-color: var(--code-bg); color: var(--code-text); font-size: 0.95rem; line-height: 1.5; font-family: 'Courier New', Courier, monospace;}
.log-line { margin-bottom: 4px; word-break: break-all; }
.tenant { color: #3b82f6; font-weight: bold; margin-right: 5px; }
.source { color: #f59e0b; margin-right: 8px; }
.text { color: var(--text-main); }
.empty-msg { color: var(--text-muted); font-style: italic; }

@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
</style>