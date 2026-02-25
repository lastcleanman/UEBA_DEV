export const theme = {
  bgMain: '#1e1e1e',
  bgSidebar: '#2c3e50',
  bgCard: '#252526',
  textPrimary: '#ecf0f1',
  textSecondary: '#bdc3c7',
  accent: '#3498db',
  success: '#2ecc71',
  danger: '#e74c3c',
};

export const inputStyle = { 
  width: '95%', padding: '8px', backgroundColor: '#111', 
  color: '#ecf0f1', border: '1px solid #444', 
  borderRadius: '4px', transition: 'all 0.3s' 
};

export const menuItems = [
  { id: 'main', icon: '📊', label: '메인 대시보드' },
  { id: 'input', icon: '📥', label: '1. 데이터 수집 (Input)' },
  { id: 'rule', icon: '🕵️', label: '2. 룰 기반 탐지 (Rule)' },
  { id: 'ml', icon: '🤖', label: '3. AI 이상탐지 (ML)' },
  { id: 'elastic', icon: '💾', label: '4. ES 적재 (Load)' },
  { id: 'parser', icon: '📄', label: '5. 파서 규칙 (XML)' },
  { id: 'license', icon: '🔑', label: '6. 라이선스 관리' },
];