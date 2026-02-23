import { useState, useEffect, useRef } from 'react';

function App() {
  const [logs, setLogs] = useState([]);
  const [currentView, setCurrentView] = useState('main');
  const [pipelineStatus, setPipelineStatus] = useState({ input: '대기 ⚪', rule: '대기 ⚪', ml: '대기 ⚪', elastic: '대기 ⚪' });
  const [triggerStatus, setTriggerStatus] = useState("");
  const [engineMode, setEngineMode] = useState("manual"); // ⭐️ 현재 엔진 모드 상태
  const endOfLogsRef = useRef(null);

  // 1. 로그 및 모드 가져오기 주기적 폴링
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

  //useEffect(() => {
  //  endOfLogsRef.current?.scrollIntoView({ behavior: "smooth" });
  //}, [logs, currentView]);

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

  // ⭐️ 모드 변경 핸들러
  const handleModeChange = async (newMode) => {
    try {
      const res = await fetch(`http://localhost:8000/api/mode/${newMode}`, { method: 'POST' });
      const data = await res.json();
      setEngineMode(newMode);
      setTriggerStatus(data.message);
      setTimeout(() => setTriggerStatus(""), 4000);
    } catch (e) {
      setTriggerStatus("❌ 모드 변경 실패");
    }
  };

  const handleTrigger = async (stageId, stageLabel) => {
    if (engineMode === 'daemon') return; // 자동 모드일 땐 클릭 방지
    setTriggerStatus(`🚀 [${stageLabel}] 수동 실행 요청됨...`);
    try {
      await fetch(`http://localhost:8000/api/trigger/${stageId}`, { method: 'POST' });
      setTimeout(() => setTriggerStatus(""), 4000);
    } catch (e) {
      setTriggerStatus("❌ 요청 실패!");
    }
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
  ];

  const renderMainDashboard = () => (
    <div>
      {/* ⭐️ 모드 스위치 UI */}
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '20px', backgroundColor: 'white', padding: '15px', borderRadius: '10px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)' }}>
        <h3 style={{ margin: '0 20px 0 0', color: '#2c3e50' }}>⚙️ 엔진 작동 모드 :</h3>
        <button 
          onClick={() => handleModeChange('manual')}
          style={{ padding: '10px 20px', marginRight: '10px', backgroundColor: engineMode === 'manual' ? '#e74c3c' : '#bdc3c7', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer', transition: '0.3s' }}>
          🖐️ 수동 클릭 모드
        </button>
        <button 
          onClick={() => handleModeChange('daemon')}
          style={{ padding: '10px 20px', backgroundColor: engineMode === 'daemon' ? '#2ecc71' : '#bdc3c7', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer', transition: '0.3s' }}>
          🔄 30초 자동 데몬 모드
        </button>
        {triggerStatus && <span style={{ marginLeft: '20px', color: '#e67e22', fontWeight: 'bold' }}>{triggerStatus}</span>}
      </div>

      <div style={{ display: 'flex', gap: '20px', marginBottom: '30px' }}>
        {Object.entries(pipelineStatus).map(([key, status], idx) => (
          <div key={key} style={{ flex: 1, padding: '20px', backgroundColor: 'white', borderRadius: '10px', textAlign: 'center', borderTop: status.includes('🟢') || status.includes('✅') ? '4px solid #2ecc71' : '4px solid #bdc3c7', boxShadow: '0 4px 6px rgba(0,0,0,0.05)' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#2c3e50' }}>{menuItems[idx+1].label}</h3>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#7f8c8d' }}>{status}</div>
          </div>
        ))}
      </div>
      
      <button 
        onClick={() => handleTrigger('all', '전체 파이프라인')}
        disabled={engineMode === 'daemon'}
        style={{ padding: '15px 30px', backgroundColor: engineMode === 'daemon' ? '#95a5a6' : '#3498db', color: 'white', border: 'none', borderRadius: '8px', fontSize: '16px', fontWeight: 'bold', cursor: engineMode === 'daemon' ? 'not-allowed' : 'pointer', marginBottom: '20px' }}>
        ▶️ 전체 파이프라인 수동 구동 {engineMode === 'daemon' && "(자동 모드 동작 중)"}
      </button>
    </div>
  );

  const renderSubView = () => {
    const stageInfo = menuItems.find(m => m.id === currentView);
    return (
      <div style={{ marginBottom: '20px' }}>
        <h2>{stageInfo.icon} {stageInfo.label} 상세 로그</h2>
        <button 
          onClick={() => handleTrigger(stageInfo.id, stageInfo.label)}
          disabled={engineMode === 'daemon'}
          style={{ padding: '10px 20px', backgroundColor: engineMode === 'daemon' ? '#95a5a6' : '#2ecc71', color: 'white', border: 'none', borderRadius: '6px', fontSize: '14px', fontWeight: 'bold', cursor: engineMode === 'daemon' ? 'not-allowed' : 'pointer' }}>
          ▶️ 해당 단계 수동 실행 {engineMode === 'daemon' && "(자동 모드 동작 중)"}
        </button>
        {triggerStatus && <span style={{ marginLeft: '15px', color: '#e67e22', fontWeight: 'bold' }}>{triggerStatus}</span>}
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', minHeight: '90vh', fontFamily: "'Segoe UI', sans-serif", backgroundColor: '#f4f7f6' }}>
      <div style={{ width: '260px', backgroundColor: '#2c3e50', color: '#ecf0f1', padding: '20px', display: 'flex', flexDirection: 'column' }}>
        <h2 style={{ color: '#3498db', marginBottom: '40px', textAlign: 'center' }}>🛡️ UEBA Control</h2>
        {menuItems.map(item => (
          <div key={item.id} onClick={() => setCurrentView(item.id)}
            style={{ padding: '15px', marginBottom: '10px', borderRadius: '8px', cursor: 'pointer', backgroundColor: currentView === item.id ? '#34495e' : 'transparent', fontWeight: currentView === item.id ? 'bold' : 'normal', borderLeft: currentView === item.id ? '4px solid #3498db' : '4px solid transparent', transition: 'all 0.2s' }}>
            {item.icon} <span style={{ marginLeft: '10px' }}>{item.label}</span>
          </div>
        ))}
      </div>
      <div style={{ flex: 1, padding: '40px', display: 'flex', flexDirection: 'column', maxHeight: '90vh', overflow: 'hidden' }}>
        {currentView === 'main' ? renderMainDashboard() : renderSubView()}
        <div style={{ flex: 1, backgroundColor: '#1e1e1e', padding: '20px', borderRadius: '10px', overflowY: 'auto', fontFamily: "monospace", fontSize: '14px', lineHeight: '1.6', boxShadow: 'inset 0 0 10px rgba(0,0,0,0.5)' }}>
          {getFilteredLogs().map((log, i) => {
            let color = '#ecf0f1';
            if (log.includes('ERROR') || log.includes('❌')) color = '#e74c3c';
            else if (log.includes('WARNING') || log.includes('⚠️')) color = '#f1c40f';
            else if (log.includes('INFO') || log.includes('✅')) color = '#2ecc71';
            return <div key={i} style={{ color, wordBreak: 'break-all' }}>{log}</div>;
          })}
          <div ref={endOfLogsRef} />
        </div>
      </div>
    </div>
  );
}

export default App;