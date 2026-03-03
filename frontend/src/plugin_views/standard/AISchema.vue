<template>
  <div class="ai-schema-container">
    <div class="header">
      <h2>🧠 AI 기반 로그 스키마 자동 추론 (Spark)</h2>
      <p>수집된 원시 로그를 분석하여 AI가 학습한 결과와 수치를 확인합니다.</p>
    </div>

    <div class="card control-card">
      <h3>🚀 AI 스키마 학습 실행</h3>
      <div class="control-group">
        <label>대상 로그 타입:</label>
        <select v-model="selectedLogType">
          <option value="event">보안 이벤트 로그 (event)</option>
          <option value="syslog">시스템 로그 (syslog)</option>
          <option value="resource">리소스 로그 (resource)</option>
        </select>
        <button class="btn-train" @click="runTraining" :disabled="isTraining">
          {{ isTraining ? 'Spark 클러스터 학습 중...' : '🔥 분산 학습 시작' }}
        </button>
      </div>
    </div>

    <div class="card history-card">
      <h3>📊 AI 학습 수치 및 분석 이력</h3>
      <table class="history-table">
        <thead>
          <tr>
            <th>로그 타입</th>
            <th>학습 정확도 (Accuracy)</th>
            <th>분석 처리 건수</th>
            <th>학습 완료 일시</th>
            <th>상태</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="historyList.length === 0">
            <td colspan="5" class="empty-msg">학습 이력이 없습니다.</td>
          </tr>
          <tr v-for="hist in historyList" :key="hist.id">
            <td class="badge-col"><span class="badge">{{ hist.log_type }}</span></td>
            <td class="acc-col">{{ hist.accuracy }}%</td>
            <td class="count-col">{{ hist.processed_count.toLocaleString() }} 건</td>
            <td class="date-col">{{ new Date(hist.created_at).toLocaleString() }}</td>
            <td class="status-col">✅ 스키마(XML) 생성 완료</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const tenantId = ref('acme')
const selectedLogType = ref('event')
const isTraining = ref(false)
const historyList = ref([])

const fetchHistory = async () => {
  try {
    const res = await fetch(`/api/v1/ai-schema/history?tenant_id=${tenantId.value}`)
    const data = await res.json()
    if (data.status === 'success') historyList.value = data.data
  } catch (error) {
    console.error('이력 조회 실패:', error)
  }
}

const runTraining = async () => {
  isTraining.value = true
  try {
    const res = await fetch('/api/v1/ai-schema/train', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tenant_id: tenantId.value, log_type: selectedLogType.value })
    })
    const data = await res.json()
    if (data.status === 'success') await fetchHistory()
  } catch (error) {
    console.error('학습 실행 실패:', error)
  } finally {
    isTraining.value = false
  }
}

onMounted(() => { fetchHistory() })
</script>

<style scoped>
/* 학습 화면에서 폼 컨트롤들을 옆으로 나란히 놓는 레이아웃만 남깁니다! */
.ai-schema-container { padding: 10px; }
.control-group { display: flex; gap: 10px; align-items: center; font-size: 1.05rem; }
.acc-col { font-weight: bold; color: var(--primary-color); font-size: 1.1rem; }
.count-col { font-weight: bold; }
</style>