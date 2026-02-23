import { useState, useEffect, useCallback } from 'react';

// 🎨 다크 테마 컬러 정의
const theme = {
  bgMain: '#1e1e1e',       // 메인 배경색 (어두운 회색)
  bgSidebar: '#2c3e50',    // 사이드바 배경색 (남색 계열)
  bgCard: '#252526',       // 카드/박스 배경색 (메인보다 약간 밝음)
  textPrimary: '#ecf0f1',  // 주요 텍스트 (밝은 흰색)
  textSecondary: '#bdc3c7',// 보조 텍스트 (회색)
  accent: '#3498db',       // 강조색 (파란색)
  success: '#2ecc71',      // 성공/실행중 (초록색)
  danger: '#e74c3c',       // 위험/수동 (빨간색)
};

function App() {
  const [logs, setLogs] = useState([]);
  const [currentView, setCurrentView] = useState('main');
  const [pipelineStatus, setPipelineStatus] = useState({ input: '대기 ⚪', rule: '대기 ⚪', ml: '대기 ⚪', elastic: '대기 ⚪' });
  const [triggerStatus, setTriggerStatus] = useState("");
  const [engineMode, setEngineMode] = useState("manual");
  const [parsers, setParsers] = useState({});
  
  // ⭐️ ML 전용 상태 추가
  const [mlMetrics, setMlMetrics] = useState({ total_analyzed: 0, high_risk_count: 0, anomaly_rate: 0.0, status: '대기 중' });

  // 📄 파서 목록 가져오기 함수
  const fetchParsers = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8000/api/parsers');
      const data = await res.json();
      setParsers(data.parsers || {});
    } catch (e) { /* 무시 */ }
  }, []);

  // 🤖 ML 지표 가져오기 함수
  const fetchMlMetrics = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8000/api/ml-metrics');
      const data = await res.json();
      setMlMetrics(data);
    } catch (e) { /* 무시 */ }
  }, []);

  // 1. 초기 데이터 및 주기적 폴링 (로그, 모드)
  useEffect(() => {
    const fetchLogsAndMode = async () => {
      try {
        const logRes = await fetch('http://localhost:8000/api/logs?lines=200');
        const logData = await logRes.json();
        setLogs(logData.logs);
        updatePipelineStatus(logData.logs);

        const modeRes = await fetch('http://localhost:8000/api/mode');
        const modeData = await modeRes.json();
        setEngineMode(modeData.mode);
      } catch (e) { /* 무시 */ }
    };
    fetchLogsAndMode();
    const interval = setInterval(fetchLogsAndMode, 2000);
    return () => clearInterval(interval);
  }, []);

  // 2. 뷰가 바뀔 때마다 필요한 데이터(파서, ML 지표) 갱신
  useEffect(() => {
    if (currentView === 'parser') fetchParsers();
    if (currentView === 'ml') fetchMlMetrics();
  }, [currentView, fetchParsers, fetchMlMetrics]);

  // 🚫 스크롤 자동 이동 기능 제거됨 (새 로그가 와도 포커스 유지)

  const updatePipelineStatus = (currentLogs) => {
    const recentLogs = currentLogs.slice(-80).join(" ");
    if (recentLogs.includes('Plugin-ElasticLoad') || recentLogs.includes('History')) {
      setPipelineStatus({ input: '완료 ✅', rule: '완료 ✅', ml: '완료 ✅', elastic: '완료 ✅' });
    } else if (recentLogs.includes('Plugin-MLAnomaly')) {
      setPipelineStatus({ input: '완료 ✅', rule: '완료 ✅', ml: '진행중 🟢', elastic: '대기 ⚪' });
    } else if (recentLogs.includes('Plugin-RuleEngine') || recentLogs.includes('AbnormalTime')) {
      setPipelineStatus({ input: '완료 ✅', rule: '진행중 🟢', ml: '대기 ⚪', elastic: '대기 ⚪' });
    } else if (recentLogs.includes('Plugin-Input') || recentLogs.includes('수집')) {
      setPipelineStatus({ input: '진행중 🟢', rule: '대기 ⚪', ml: '대기 ⚪', elastic: '대기 ⚪' });
    } else {
      setPipelineStatus({ input: '대기 ⚪', rule: '대기 ⚪', ml: '대기 ⚪', elastic: '대기 ⚪' });
    }
  };

  const handleModeChange = async (newMode) => {
    try {
      const res = await fetch(`http://localhost:8000/api/mode/${newMode}`, { method: 'POST' });
      const data = await res.json();
      setEngineMode(newMode);
      setTriggerStatus(data.message);
      setTimeout(() => setTriggerStatus(""), 4000);
    } catch (e) { setTriggerStatus("❌ 모드 변경 실패"); }
  };

  const handleTrigger = async (stageId, stageLabel) => {
    if (engineMode === 'daemon') return;
    setTriggerStatus(`🚀 [${stageLabel}] 수동 실행 요청됨...`);
    try {
      await fetch(`http://localhost:8000/api/trigger/${stageId}`, { method: 'POST' });
      setTimeout(() => setTriggerStatus(""), 4000);
      
      // 실행 직후 데이터 갱신을 위해 API 재호출
      if (stageId === 'ml') setTimeout(fetchMlMetrics, 2000);
    } catch (e) { setTriggerStatus("❌ 요청 실패!"); }
  };

  const getFilteredLogs = () => {
    if (currentView === 'main') return logs.slice(-50);
    return logs.filter(log => {
      if (currentView === 'input') return log.includes('Plugin-Input') || log.includes('수집');
      if (currentView === 'rule') return log.includes('RuleEngine') || log.includes('AbnormalTime');
      if (currentView === 'ml') return log.includes('MLAnomaly');
      if (currentView === 'elastic') return log.includes('ElasticLoad') || log.includes('History');
      return true;
    });
  };

  const menuItems = [
    { id: 'main', icon: '📊', label: '메인 대시보드' },
    { id: 'input', icon: '📥', label: '1. 데이터 수집 (Input)' },
    { id: 'rule', icon: '🕵️', label: '2. 룰 기반 탐지 (Rule)' },
    { id: 'ml', icon: '🤖', label: '3. AI 이상탐지 (ML)' },
    { id: 'elastic', icon: '💾', label: '4. ES 적재 (Load)' },
    { id: 'parser', icon: '📄', label: '5. 파서 규칙 (XML)' },
  ];

  // --- 🎨 렌더링 컴포넌트 ---

  const renderMainDashboard = () => (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '20px', backgroundColor: theme.bgCard, padding: '15px', borderRadius: '10px', boxShadow: '0 4px 6px rgba(0,0,0,0.2)' }}>
        <h3 style={{ margin: '0 20px 0 0', color: theme.textPrimary }}>⚙️ 엔진 작동 모드 :</h3>
        <button onClick={() => handleModeChange('manual')} style={{ padding: '10px 20px', marginRight: '10px', backgroundColor: engineMode === 'manual' ? theme.danger : '#bdc3c7', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer', transition: '0.3s' }}>🖐️ 수동 클릭 모드</button>
        <button onClick={() => handleModeChange('daemon')} style={{ padding: '10px 20px', backgroundColor: engineMode === 'daemon' ? theme.success : '#bdc3c7', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer', transition: '0.3s' }}>🔄 30초 자동 데몬 모드</button>
        {triggerStatus && <span style={{ marginLeft: '20px', color: theme.accent, fontWeight: 'bold' }}>{triggerStatus}</span>}
      </div>

      <div style={{ display: 'flex', gap: '20px', marginBottom: '30px' }}>
        {Object.entries(pipelineStatus).map(([key, status], idx) => (
          <div key={key} style={{ flex: 1, padding: '20px', backgroundColor: theme.bgCard, borderRadius: '10px', textAlign: 'center', borderTop: status.includes('🟢') || status.includes('✅') ? `4px solid ${theme.success}` : '4px solid #555', boxShadow: '0 4px 6px rgba(0,0,0,0.2)' }}>
            <h3 style={{ margin: '0 0 10px 0', color: theme.textPrimary }}>{menuItems[idx+1].label}</h3>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: theme.textPrimary }}>{status}</div>
          </div>
        ))}
      </div>
      
      <button onClick={() => handleTrigger('all', '전체 파이프라인')} disabled={engineMode === 'daemon'} style={{ padding: '15px 30px', backgroundColor: engineMode === 'daemon' ? '#555' : theme.accent, color: 'white', border: 'none', borderRadius: '8px', fontSize: '16px', fontWeight: 'bold', cursor: engineMode === 'daemon' ? 'not-allowed' : 'pointer', marginBottom: '20px' }}>▶️ 전체 파이프라인 수동 구동 {engineMode === 'daemon' && "(자동 모드 동작 중)"}</button>
    </div>
  );

  const renderSubView = () => {
    const stageInfo = menuItems.find(m => m.id === currentView);
    return (
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ color: theme.textPrimary }}>{stageInfo.icon} {stageInfo.label} 상세 로그</h2>
        <button onClick={() => handleTrigger(stageInfo.id, stageInfo.label)} disabled={engineMode === 'daemon'} style={{ padding: '10px 20px', backgroundColor: engineMode === 'daemon' ? '#555' : theme.success, color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: 'bold', cursor: engineMode === 'daemon' ? 'not-allowed' : 'pointer' }}>▶️ 해당 단계 수동 실행 {engineMode === 'daemon' && "(자동 모드 동작 중)"}</button>
        {triggerStatus && <span style={{ marginLeft: '15px', color: theme.accent, fontWeight: 'bold' }}>{triggerStatus}</span>}
      </div>
    );
  };

  // ⭐️ ML 전용 대시보드 화면
  const renderMLView = () => (
    <div style={{ marginBottom: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ color: theme.textPrimary }}>🤖 3. AI 이상탐지 (ML) 모델 현황</h2>
        <button onClick={() => handleTrigger('ml', 'AI 이상탐지 (ML)')} disabled={engineMode === 'daemon'} style={{ padding: '10px 20px', backgroundColor: engineMode === 'daemon' ? '#555' : theme.success, color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: 'bold', cursor: engineMode === 'daemon' ? 'not-allowed' : 'pointer' }}>▶️ ML 분석 수동 실행 {engineMode === 'daemon' && "(자동 모드)"}</button>
      </div>
      <p style={{ color: theme.textSecondary }}>머신러닝 모델의 데이터 학습 및 위협 스코어링 수치화 지표입니다.</p>

      {/* 수치화 위젯 영역 */}
      <div style={{ display: 'flex', gap: '20px', marginTop: '20px' }}>
        <div style={{ flex: 1, backgroundColor: theme.bgCard, padding: '20px', borderRadius: '10px', borderLeft: `5px solid ${theme.accent}`, boxShadow: '0 4px 6px rgba(0,0,0,0.2)' }}>
          <div style={{ color: theme.textSecondary, fontSize: '14px', marginBottom: '10px' }}>총 학습/분석 데이터</div>
          <div style={{ color: theme.textPrimary, fontSize: '28px', fontWeight: 'bold' }}>{mlMetrics.total_analyzed.toLocaleString()} <span style={{ fontSize: '14px', fontWeight: 'normal' }}>건</span></div>
        </div>
        <div style={{ flex: 1, backgroundColor: theme.bgCard, padding: '20px', borderRadius: '10px', borderLeft: `5px solid ${theme.danger}`, boxShadow: '0 4px 6px rgba(0,0,0,0.2)' }}>
          <div style={{ color: theme.textSecondary, fontSize: '14px', marginBottom: '10px' }}>탐지된 고위험 이상행위</div>
          <div style={{ color: theme.danger, fontSize: '28px', fontWeight: 'bold' }}>{mlMetrics.high_risk_count.toLocaleString()} <span style={{ fontSize: '14px', fontWeight: 'normal' }}>건</span></div>
        </div>
        <div style={{ flex: 1, backgroundColor: theme.bgCard, padding: '20px', borderRadius: '10px', borderLeft: `5px solid ${theme.success}`, boxShadow: '0 4px 6px rgba(0,0,0,0.2)' }}>
          <div style={{ color: theme.textSecondary, fontSize: '14px', marginBottom: '10px' }}>현재 AI 모델 상태</div>
          <div style={{ color: theme.success, fontSize: '18px', fontWeight: 'bold', marginTop: '10px' }}>{mlMetrics.status}</div>
        </div>
      </div>

      {/* 프로그레스 바 영역 */}
      <div style={{ marginTop: '20px', backgroundColor: theme.bgCard, padding: '20px', borderRadius: '10px', boxShadow: '0 4px 6px rgba(0,0,0,0.2)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
          <span style={{ color: theme.textPrimary, fontWeight: 'bold' }}>전체 데이터 대비 이상행위 비율 (Anomaly Rate)</span>
          <span style={{ color: theme.danger, fontWeight: 'bold' }}>{mlMetrics.anomaly_rate}%</span>
        </div>
        <div style={{ width: '100%', height: '12px', backgroundColor: '#333', borderRadius: '6px', overflow: 'hidden' }}>
          <div style={{ width: `${Math.min(mlMetrics.anomaly_rate * 5, 100)}%`, height: '100%', backgroundColor: theme.danger, transition: 'width 0.5s ease-in-out' }}></div>
        </div>
      </div>
    </div>
  );

  const renderParserView = () => (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ color: theme.textPrimary }}>📄 파서 규칙 (Auto-Generated XML)</h2>
        <p style={{ color: theme.textSecondary }}>생성된 원본 로그 데이터를 분석하여 자동으로 추출한 Key-Value 기반 XML 파싱 규칙입니다.</p>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={() => handleTrigger('input', '원본 로그 재생성')} disabled={engineMode === 'daemon'} style={{ padding: '10px 20px', backgroundColor: engineMode === 'daemon' ? '#555' : '#9b59b6', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: 'bold', cursor: engineMode === 'daemon' ? 'not-allowed' : 'pointer' }}>🔄 원본 로그 데이터 갱신 (생성기 실행)</button>
          <button onClick={fetchParsers} style={{ padding: '10px 20px', backgroundColor: theme.accent, color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: 'bold', cursor: 'pointer' }}>🔄 목록 새로고침</button>
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px', paddingRight: '10px' }}>
        {Object.entries(parsers).map(([filename, xml]) => (
          <div key={filename} style={{ backgroundColor: '#282a36', padding: '20px', borderRadius: '10px', boxShadow: '0 10px 15px rgba(0,0,0,0.3)' }}>
            <h3 style={{ color: '#50fa7b', marginTop: 0, marginBottom: '15px', borderBottom: '1px solid #444', paddingBottom: '10px' }}>📜 {filename}</h3>
            <pre style={{ color: '#f8f8f2', fontSize: '14px', margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontFamily: "'Fira Code', 'Courier New', Courier, monospace" }}>{xml}</pre>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: "'Segoe UI', sans-serif", backgroundColor: theme.bgMain }}>
      {/* 사이드바 */}
      <div style={{ width: '260px', backgroundColor: theme.bgSidebar, color: theme.textPrimary, padding: '20px', display: 'flex', flexDirection: 'column' }}>
        <h2 style={{ color: theme.accent, marginBottom: '40px', textAlign: 'center' }}>🛡️ UEBA Control</h2>
        {menuItems.map(item => (
          <div key={item.id} onClick={() => setCurrentView(item.id)} style={{ padding: '15px', marginBottom: '10px', borderRadius: '8px', cursor: 'pointer', backgroundColor: currentView === item.id ? '#34495e' : 'transparent', fontWeight: currentView === item.id ? 'bold' : 'normal', borderLeft: currentView === item.id ? `4px solid ${theme.accent}` : '4px solid transparent', transition: 'all 0.2s' }}>{item.icon} <span style={{ marginLeft: '10px' }}>{item.label}</span></div>
        ))}
      </div>
      
      {/* 메인 콘텐츠 영역 (다크 테마 적용) */}
      <div style={{ flex: 1, padding: '40px', display: 'flex', flexDirection: 'column', maxHeight: '100vh', overflow: 'hidden', color: theme.textPrimary }}>
        
        {/* 라우팅: 선택된 메뉴에 따라 화면 교체 */}
        {currentView === 'main' ? renderMainDashboard() : 
         currentView === 'parser' ? renderParserView() : 
         currentView === 'ml' ? renderMLView() : 
         renderSubView()}

        {/* 파서 화면이 아닐 때만 로그 창을 출력합니다. */}
        {currentView !== 'parser' && (
          <div style={{ flex: 1, backgroundColor: '#111', padding: '20px', borderRadius: '10px', overflowY: 'auto', fontFamily: "monospace", fontSize: '14px', lineHeight: '1.6', boxShadow: 'inset 0 0 10px rgba(0,0,0,0.8)', marginTop: '20px' }}>
            
            {/* ⭐️ 최신 로그가 맨 위에 오도록 역순(reverse) 정렬 */}
            {getFilteredLogs().slice().reverse().map((log, i) => {
              let color = theme.textPrimary;
              if (log.includes('ERROR') || log.includes('❌') || log.includes('⚠️')) color = theme.danger;
              else if (log.includes('WARNING')) color = '#f1c40f';
              else if (log.includes('INFO') || log.includes('✅') || log.includes('🟢')) color = theme.success;
              return <div key={i} style={{ color, wordBreak: 'break-all' }}>{log}</div>;
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;