<template>
  <div class="schema-viewer-container">
    <div class="header">
      <h2>📄 생성된 스키마(XML) 관리</h2>
      <p v-if="!isDetailMode">AI가 분석하여 생성한 로그 스키마 파일 목록입니다.</p>
      <p v-else>스키마 필드를 수동으로 추가, 수정, 삭제하고 저장할 수 있습니다.</p>
    </div>

    <div v-if="!isDetailMode" class="card list-card">
      <h3>📂 스키마 파일 목록</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>타입</th>
            <th>생성 일시</th>
            <th>파일 경로</th>
            <th>액션</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="historyList.length === 0">
            <td colspan="4" class="empty-msg">생성된 파일이 없습니다.</td>
          </tr>
          <tr v-for="hist in historyList" :key="hist.id">
            <td><span class="badge">{{ hist.log_type }}</span></td>
            <td class="date-col">{{ new Date(hist.created_at).toLocaleString() }}</td>
            <td class="path-col">{{ hist.xml_file_path.split('/').pop() }}</td>
            <td>
              <button class="btn-primary" @click="openDetail(hist)">상세/수정</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="detail-wrapper">
      
      <div class="card detail-header-card">
        <div class="detail-header">
          <h3>✨ 스키마 상세 및 수정 (<span class="highlight">{{ selectedHist.log_type }}</span>)</h3>
          <div class="btn-group">
            <button class="btn-secondary" @click="closeDetail">⬅ 목록으로</button>
            <button class="btn-success" @click="saveSchema">💾 변경사항 저장</button>
          </div>
        </div>
      </div>

      <div class="xml-comparison-grid">
        <div class="xml-box">
          <h4>📄 원본 스키마 (Before)</h4>
          <pre>{{ originalXmlString }}</pre>
        </div>
        <div class="xml-box modified">
          <h4>📝 수정 후 미리보기 (After)</h4>
          <pre>{{ previewXmlString }}</pre>
        </div>
      </div>

      <div class="card edit-card">
        <h3>✏️ 스키마 필드 에디터</h3>
        <table class="data-table edit-table">
          <thead>
            <tr>
              <th>필드명 (Key)</th>
              <th>데이터 타입 (Type)</th>
              <th>AI 신뢰도 (Confidence)</th>
              <th><button class="btn-add" @click="addField">➕ 필드 추가</button></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="schemaFields.length === 0">
              <td colspan="4" class="empty-msg">등록된 필드가 없습니다.</td>
            </tr>
            <tr v-for="(field, index) in schemaFields" :key="index">
              <td>
                <input type="text" v-model="field.name" placeholder="예: src_ip" class="form-input">
              </td>
              <td>
                <select v-model="field.type" class="form-select">
                  <option value="string">문자열 (string)</option>
                  <option value="integer">숫자 (integer)</option>
                  <option value="datetime">날짜/시간 (datetime)</option>
                  <option value="ip_address">IP 주소 (ip_address)</option>
                </select>
              </td>
              <td>
                <input type="text" v-model="field.confidence" class="form-input short-input">
              </td>
              <td>
                <button class="btn-danger" @click="removeField(index)">🗑️ 삭제</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const tenantId = ref('acme')
const historyList = ref([])

// 모드 제어 상태
const isDetailMode = ref(false)
const selectedHist = ref(null)

// 데이터 상태
const schemaFields = ref([])      // 현재 편집 중인 필드들 (반응형)
const originalFields = ref([])    // 처음에 불러온 원본 필드들 (비교용)

// 목록 불러오기
const fetchHistory = async () => {
  try {
    const res = await fetch(`/api/v1/ai-schema/history?tenant_id=${tenantId.value}`)
    const data = await res.json()
    if (data.status === 'success') historyList.value = data.data
  } catch (error) {
    console.error('이력 조회 실패:', error)
  }
}

// 상세 화면 열기
const openDetail = async (hist) => {
  try {
    const res = await fetch(`/api/v1/ai-schema/schema-detail?file_path=${encodeURIComponent(hist.xml_file_path)}`)
    const data = await res.json()
    if (data.status === 'success') {
      selectedHist.value = hist
      // 깊은 복사(Deep Copy)를 통해 원본과 편집용 데이터를 완벽히 분리합니다.
      schemaFields.value = JSON.parse(JSON.stringify(data.fields))
      originalFields.value = JSON.parse(JSON.stringify(data.fields))
      isDetailMode.value = true
    } else {
      alert(data.message)
    }
  } catch (error) {
    console.error('스키마 상세 조회 실패:', error)
  }
}

// ⭐️ XML 문자열을 예쁘게 만들어주는 헬퍼 함수
const generateXml = (fields) => {
  if (!selectedHist.value) return ''
  let xml = `<LogSchema tenant="${tenantId.value}" type="${selectedHist.value.log_type}">\n`
  fields.forEach(f => {
    // 2칸 들여쓰기(Indent) 적용
    xml += `  <Field name="${f.name || ''}" type="${f.type}" confidence="${f.confidence}" />\n`
  })
  xml += `</LogSchema>`
  return xml
}

// ⭐️ 실시간 계산(Computed) 속성: 값이 바뀔 때마다 즉시 반영됩니다!
const originalXmlString = computed(() => generateXml(originalFields.value))
const previewXmlString = computed(() => generateXml(schemaFields.value))

// 목록으로 돌아가기
const closeDetail = () => {
  isDetailMode.value = false
  selectedHist.value = null
  schemaFields.value = []
  originalFields.value = []
}

// 새 필드 추가
const addField = () => {
  schemaFields.value.push({ name: 'new_field', type: 'string', confidence: 'Manual' })
}

// 필드 삭제
const removeField = (index) => {
  schemaFields.value.splice(index, 1)
}

// 수정한 내용을 백엔드에 보내 저장
const saveSchema = async () => {
  try {
    const res = await fetch('/api/v1/ai-schema/schema-detail', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file_path: selectedHist.value.xml_file_path,
        tenant_id: tenantId.value,
        log_type: selectedHist.value.log_type,
        fields: schemaFields.value
      })
    })
    const data = await res.json()
    if (data.status === 'success') {
      alert('✅ 성공적으로 파일에 덮어썼습니다!')
      // 저장 성공 시, 원본 데이터도 현재 상태로 업데이트
      originalFields.value = JSON.parse(JSON.stringify(schemaFields.value))
    } else {
      alert('저장 실패: ' + data.message)
    }
  } catch (error) {
    console.error('스키마 저장 실패:', error)
  }
}

onMounted(() => { fetchHistory() })
</script>

<style scoped>
/* 화면의 뼈대를 잡는 레이아웃 스타일만 남깁니다! */
.schema-viewer-container { padding: 10px; }
.detail-wrapper { display: flex; flex-direction: column; gap: 20px; }

/* 헤더 카드 특화 정렬 */
.detail-header-card { padding: 15px 25px; }
.detail-header { display: flex; justify-content: space-between; align-items: center; }
.highlight { color: var(--primary-color); }

/* XML 좌우 비교 뷰어 특화 레이아웃 */
.xml-comparison-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.xml-box { background: var(--bg-panel); padding: 20px; border-radius: 8px; border: 1px solid var(--border-color); box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
.xml-box h4 { margin-top: 0; color: var(--text-muted); border-bottom: 1px dashed var(--border-color); padding-bottom: 10px; margin-bottom: 15px; font-size: 1.1rem; }
.xml-box.modified h4 { color: var(--primary-color); }
.xml-box pre { min-height: 150px; }
</style>