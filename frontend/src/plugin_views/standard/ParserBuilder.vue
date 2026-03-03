<template>
  <div class="parser-builder">
    <div class="header-section">
      <h2>⚙️ Parser Builder (데이터 정제 룰 설정)</h2>
      <p>수집된 원시 로그를 의미 있는 데이터로 쪼개는 규칙을 만듭니다.</p>
    </div>

    <div class="card">
      <h3>1. 샘플 로그 입력</h3>
      <textarea v-model="sampleLog" placeholder="여기에 원시 로그를 붙여넣으세요..."></textarea>
    </div>

    <div class="card">
      <h3>2. 파싱 규칙 설정</h3>
      <div class="form-group">
        <label>파싱 방식:</label>
        <select v-model="parseType">
          <option value="kv">Key-Value 쌍 (예: user=admin)</option>
          <option value="regex">정규표현식 (Regex)</option>
        </select>
      </div>

      <div v-if="parseType === 'kv'" class="form-group inline-group">
        <div>
          <label>구분자(Delimiter):</label>
          <input v-model="kvDelimiter" type="text" placeholder="예: 공백 (스페이스바 한 칸)">
          <small>단어 사이를 띄우는 문자</small>
        </div>
        <div>
          <label>연결자(Separator):</label>
          <input v-model="kvSeparator" type="text" placeholder="예: =">
          <small>키와 값을 연결하는 문자</small>
        </div>
      </div>

      <div v-if="parseType === 'regex'" class="form-group">
        <label>정규식 패턴:</label>
        <input v-model="regexPattern" type="text" placeholder="예: ^\[(.*?)\] (.*)$">
        <small>괄호 () 를 사용하여 추출할 그룹을 지정하세요.</small>
      </div>

      <button class="btn-test" @click="testParse">🧪 파싱 테스트 해보기</button>
    </div>

    <div class="card result-card" v-if="parsedResult">
      <h3>3. 파싱 결과 미리보기 (JSON)</h3>
      <pre>{{ parsedResult }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const sampleLog = ref('timestamp=2026-02-27 11:30:00 machine=UEBA-MFD-001 user=admin rulename=DDoS_HTTP_Flood action=차단 priority=3')
const parseType = ref('kv')
const kvDelimiter = ref(' ')
const kvSeparator = ref('=')
const regexPattern = ref('')
const parsedResult = ref(null)

const testParse = () => {
  // 프론트엔드 단에서 가볍게 시뮬레이션 (이후 백엔드 API 연동으로 교체 예정)
  if (parseType.value === 'kv') {
    const result = {}
    const pairs = sampleLog.value.split(kvDelimiter.value)
    pairs.forEach(pair => {
      const parts = pair.split(kvSeparator.value)
      if (parts.length >= 2) {
        const key = parts[0].trim()
        const value = parts.slice(1).join(kvSeparator.value).trim()
        if (key) result[key] = value
      }
    })
    parsedResult.value = JSON.stringify(result, null, 2)
  } else {
    parsedResult.value = "{\n  \"message\": \"정규식 파싱 테스트는 백엔드 연동 후 완벽하게 지원됩니다.\"\n}"
  }
}
</script>

<style scoped>
/* 정규식, 구분자 입력 폼을 옆으로 배치하는 특수 레이아웃만 남깁니다! */
.parser-builder { padding: 10px; }
.form-group { margin-bottom: 20px; }
.inline-group { display: flex; gap: 30px; }
.inline-group > div { display: flex; flex-direction: column; gap: 8px; }
small { color: var(--text-muted); font-size: 0.85rem; }
textarea { height: 60px; }
</style>