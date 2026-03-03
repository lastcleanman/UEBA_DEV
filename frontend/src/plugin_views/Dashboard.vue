<template>
  <div class="dashboard-container">
    <div class="header">
      <h2>📊 통합 보안 대시보드</h2>
      <p>데이터 파이프라인의 전체 흐름과 실시간 수집 상태를 모니터링합니다.</p>
    </div>

    <div class="card pipeline-card">
      <h3>🚀 Pipeline Status</h3>
      <div class="pipeline-flow">
        
        <div class="node active">
          <div class="icon-circle">📡</div>
          <div class="node-info">
            <h4>1. 데이터 수집</h4>
            <span class="status healthy">🟢 정상 수집 중</span>
          </div>
        </div>

        <div class="arrow">➔</div>

        <div class="node active">
          <div class="icon-circle">🧹</div>
          <div class="node-info">
            <h4>2. 정규화/정제</h4>
            <span class="status healthy">🟢 XML 파서 동작</span>
          </div>
        </div>

        <div class="arrow">➔</div>

        <div class="node warning">
          <div class="icon-circle">🧠</div>
          <div class="node-info">
            <h4>3. 위협 탐지</h4>
            <span class="status pending">🟡 ML 학습 대기</span>
          </div>
        </div>

        <div class="arrow">➔</div>

        <div class="node idle">
          <div class="icon-circle">🛡️</div>
          <div class="node-info">
            <h4>4. 자동화 대응</h4>
            <span class="status offline">⚪ 정책 대기 중</span>
          </div>
        </div>

      </div>
    </div>

    <div class="terminal-section">
      <LogTerminal />
    </div>

  </div>
</template>

<script setup>
import LogTerminal from '@/components/LogTerminal.vue'
</script>

<style scoped>
.dashboard-container { padding: 10px; }

/* 파이프라인 흐름도 CSS */
.pipeline-card { padding: 25px; margin-bottom: 25px; }
.pipeline-flow {
  display: flex; align-items: center; justify-content: space-between; 
  margin-top: 20px; overflow-x: auto; padding-bottom: 10px;
}
.node {
  flex: 1; display: flex; align-items: center; gap: 15px; 
  background: var(--bg-base); padding: 15px 20px; 
  border-radius: 12px; border: 1px solid var(--border-color);
  min-width: 200px;
}
.icon-circle {
  font-size: 1.8rem; background: var(--bg-panel); 
  width: 50px; height: 50px; display: flex; 
  justify-content: center; align-items: center; 
  border-radius: 50%; border: 1px solid var(--border-color);
}
.node-info h4 { margin: 0 0 5px 0; color: var(--text-main); font-size: 1.05rem; }
.status { font-size: 0.9rem; font-weight: bold; }
.status.healthy { color: #4ade80; }
.status.pending { color: #facc15; }
.status.offline { color: var(--text-muted); }

.arrow { font-size: 1.5rem; color: var(--text-muted); font-weight: bold; }

/* 상태별 테두리 하이라이트 */
.node.active { border-bottom: 3px solid #3b82f6; }
.node.warning { border-bottom: 3px solid #facc15; }
.node.idle { border-bottom: 3px solid var(--border-color); opacity: 0.8; }
</style>