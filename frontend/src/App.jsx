import { useState, useEffect, useCallback } from 'react';

// 🎨 다크 테마 컬러 정의
const theme = {
  bgMain: '#1e1e1e',
  bgSidebar: '#2c3e50',
  bgCard: '#252526',
  textPrimary: '#ecf0f1',
  textSecondary: '#bdc3c7',
  accent: '#3498db',
  success: '#2ecc71',
  danger: '#e74c3c',
};

// 공통 입력 스타일
const inputStyle = { width: '95%', padding: '8px', backgroundColor: '#111', color: '#ecf0f1', border: '1px solid #444', borderRadius: '4px', transition: 'all 0.3s' };

function App() {
  const [logs, setLogs] = useState([]);
  const [currentView, setCurrentView] = useState('main');
  const [pipelineStatus, setPipelineStatus] = useState({ input: '대기 ⚪', rule: '대기 ⚪', ml: '대기 ⚪', elastic: '대기 ⚪' });
  const [triggerStatus, setTriggerStatus] = useState("");
  const [engineMode, setEngineMode] = useState("manual");
  const [parsers, setParsers] = useState({});
  const [mlMetrics, setMlMetrics] = useState({ total_analyzed: 0, high_risk_count: 0, anomaly_rate: 0.0, status: '대기 중' });

  // ⭐️ 상태 관리 Hooks
  const [extraRows, setExtraRows] = useState({});
  const [pendingDelete, setPendingDelete] = useState({}); // 삭제 대기 항목 관리

  // 📄 데이터 로딩 함수
  const fetchParsers = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8000/api/parsers');
      const data = await res.json();
      setParsers(data.parsers || {});
    } catch (e) { console.error(e); }
  }, []);

  const fetchMlMetrics = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8000/api/ml-metrics');
      const data = await res.json();
      setMlMetrics(data);
    } catch (e) { console.error(e); }
  }, []);

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
      } catch (e) { }
    };
    fetchLogsAndMode();
    const interval = setInterval(fetchLogsAndMode, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (currentView === 'parser') fetchParsers();
    if (currentView === 'ml') fetchMlMetrics();
  }, [currentView, fetchParsers, fetchMlMetrics]);

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

  // ⭐️ 파서 규칙 로직
  const addNewRow = (filename) => {
    setExtraRows(prev => ({
      ...prev,
      [filename]: [...(prev[filename] || []), { target: '', source: '' }]
    }));
  };

  const toggleDeleteRow = (filename, index, isExtra) => {
    if (isExtra) {
      setExtraRows(prev => ({
        ...prev,
        [filename]: prev[filename].filter((_, i) => i !== index)
      }));
    } else {
      setPendingDelete(prev => {
        const current = prev[filename] || [];
        const updated = current.includes(index) 
          ? current.filter(i => i !== index) 
          : [...current, index];
        return { ...prev, [filename]: updated };
      });
    }
  };

  const handleSaveParser = async (filename) => {
    const container = document.getElementById(`editor-${filename.replace('.', '-')}`);
    // 삭제 대기(pending-delete 클래스)가 아닌 행들만 수집
    const rows = container.querySelectorAll('.edit-row:not(.is-deleted)');
    const fields = Array.from(rows).map(row => ({
      target: row.querySelector('.input-target').value,
      source: row.querySelector('.input-source').value
    })).filter(f => f.target.trim() !== "");

    try {
      const res = await fetch('http://localhost:8000/api/parsers/update-fields', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename, fields })
      });
      const result = await res.json();
      alert(result.message);
      
      // 상태 초기화 및 재조회
      setExtraRows(prev => ({ ...prev, [filename]: [] }));
      setPendingDelete(prev => ({ ...prev, [filename]: [] }));
      fetchParsers();
    } catch (e) { alert("저장 실패"); }
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
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '20px', backgroundColor: theme.bgCard, padding: '15px', borderRadius: '10px' }}>
        <h3 style={{ margin: '0 20px 0 0', color: theme.textPrimary }}>⚙️ 엔진 작동 모드 :</h3>
        <button onClick={() => handleModeChange('manual')} style={{ padding: '10px 20px', marginRight: '10px', backgroundColor: engineMode === 'manual' ? theme.danger : '#bdc3c7', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>🖐️ 수동 클릭 모드</button>
        <button onClick={() => handleModeChange('daemon')} style={{ padding: '10px 20px', backgroundColor: engineMode === 'daemon' ? theme.success : '#bdc3c7', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>🔄 30초 자동 데몬 모드</button>
      </div>
      <div style={{ display: 'flex', gap: '20px', marginBottom: '30px' }}>
        {Object.entries(pipelineStatus).map(([key, status], idx) => (
          <div key={key} style={{ flex: 1, padding: '20px', backgroundColor: theme.bgCard, borderRadius: '10px', textAlign: 'center', borderTop: status.includes('🟢') || status.includes('✅') ? `4px solid ${theme.success}` : '4px solid #555' }}>
            <h3 style={{ margin: '0 0 10px 0', color: theme.textPrimary }}>{menuItems[idx+1].label}</h3>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: theme.textPrimary }}>{status}</div>
          </div>
        ))}
      </div>
      <button onClick={() => handleTrigger('all', '전체 파이프라인')} disabled={engineMode === 'daemon'} style={{ padding: '15px 30px', backgroundColor: theme.accent, color: 'white', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}>▶️ 전체 파이프라인 수동 구동</button>
    </div>
  );

  const renderMLView = () => (
    <div style={{ marginBottom: '20px' }}>
      <h2 style={{ color: theme.textPrimary }}>🤖 3. AI 이상탐지 (ML) 모델 현황</h2>
      <div style={{ display: 'flex', gap: '20px', marginTop: '20px' }}>
        <div style={{ flex: 1, backgroundColor: theme.bgCard, padding: '20px', borderRadius: '10px', borderLeft: `5px solid ${theme.accent}` }}>
          <div style={{ color: theme.textSecondary }}>총 학습 데이터</div>
          <div style={{ color: theme.textPrimary, fontSize: '28px', fontWeight: 'bold' }}>{mlMetrics.total_analyzed.toLocaleString()} 건</div>
        </div>
        <div style={{ flex: 1, backgroundColor: theme.bgCard, padding: '20px', borderRadius: '10px', borderLeft: `5px solid ${theme.danger}` }}>
          <div style={{ color: theme.textSecondary }}>이상행위 탐지</div>
          <div style={{ color: theme.danger, fontSize: '28px', fontWeight: 'bold' }}>{mlMetrics.high_risk_count.toLocaleString()} 건</div>
        </div>
        <div style={{ flex: 1, backgroundColor: theme.bgCard, padding: '20px', borderRadius: '10px', borderLeft: `5px solid ${theme.success}` }}>
          <div style={{ color: theme.textSecondary }}>AI 상태</div>
          <div style={{ color: theme.success, fontSize: '18px', fontWeight: 'bold' }}>{mlMetrics.status}</div>
        </div>
      </div>
    </div>
  );

  const renderParserView = () => (
    <div style={{ color: theme.textPrimary, overflowY: 'auto', flex: 1, paddingRight: '10px' }}>
      <h2 style={{ marginBottom: '20px' }}>📄 파서 규칙 상세 설정</h2>
      {Object.entries(parsers).map(([filename, xmlContent]) => {
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlContent, "text/xml");
        const fieldNodes = Array.from(xmlDoc.getElementsByTagName("field"));
        const rowsData = fieldNodes.map(node => ({
          target: node.getAttribute('target') || '',
          source: node.getAttribute('source') || ''
        }));

        return (
          <div key={filename} style={{ backgroundColor: theme.bgCard, padding: '25px', borderRadius: '12px', marginBottom: '40px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px', borderBottom: '1px solid #444', paddingBottom: '15px' }}>
              <h3 style={{ margin: 0, color: theme.success }}>📜 {filename}</h3>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button onClick={() => addNewRow(filename)} style={{ backgroundColor: '#444', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>➕ 항목 추가</button>
                <button onClick={() => handleSaveParser(filename)} style={{ backgroundColor: theme.accent, color: 'white', border: 'none', padding: '10px 25px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}>💾 저장 및 반영</button>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '20px', alignItems: 'flex-start' }}>
              {/* 왼쪽 XML 뷰 */}
              <div style={{ flex: 4 }}>
                <div style={{ fontSize: '12px', color: theme.textSecondary, marginBottom: '8px' }}>[ XML 원본 ]</div>
                <pre style={{ backgroundColor: '#111', padding: '15px', borderRadius: '8px', fontSize: '12px', color: '#f8f8f2', border: '1px solid #333', height: '400px', overflow: 'auto' }}>{xmlContent}</pre>
              </div>
              
              {/* 오른쪽 편집 테이블 */}
              <div id={`editor-${filename.replace('.', '-')}`} style={{ flex: 6 }}>
                <div style={{ fontSize: '12px', color: theme.textSecondary, marginBottom: '8px' }}>[ 필드 편집 ]</div>
                <div style={{ maxHeight: '400px', overflowY: 'auto', border: '1px solid #333', borderRadius: '8px', backgroundColor: '#1e1e1e' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead style={{ position: 'sticky', top: 0, backgroundColor: '#2c3e50', zIndex: 1 }}>
                      <tr style={{ textAlign: 'left', color: theme.textPrimary }}>
                        <th style={{ padding: '12px', borderBottom: '2px solid #444' }}>Target Key</th>
                        <th style={{ padding: '12px', borderBottom: '2px solid #444' }}>Source Value</th>
                        <th style={{ padding: '12px', borderBottom: '2px solid #444', width: '50px' }}>삭제</th>
                      </tr>
                    </thead>
                    <tbody>
                      {/* 기존 데이터 */}
                      {rowsData.map((field, idx) => {
                        const isDel = (pendingDelete[filename] || []).includes(idx);
                        return (
                          <tr key={`fixed-${idx}`} className={`edit-row ${isDel ? 'is-deleted' : ''}`} style={{ borderBottom: '1px solid #333', backgroundColor: isDel ? '#4c1d1d' : 'transparent', transition: '0.3s' }}>
                            <td style={{ padding: '8px' }}><input className="input-target" defaultValue={field.target} style={{ ...inputStyle, textDecoration: isDel ? 'line-through' : 'none' }} disabled={isDel} /></td>
                            <td style={{ padding: '8px' }}><input className="input-source" defaultValue={field.source} style={{ ...inputStyle, textDecoration: isDel ? 'line-through' : 'none' }} disabled={isDel} /></td>
                            <td style={{ padding: '8px', textAlign: 'center' }}>
                              <button onClick={() => toggleDeleteRow(filename, idx, false)} style={{ backgroundColor: 'transparent', border: 'none', color: isDel ? theme.success : theme.danger, cursor: 'pointer', fontSize: '18px' }}>
                                {isDel ? '🔄' : '🗑️'}
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                      {/* 추가 데이터 */}
                      {(extraRows[filename] || []).map((_, idx) => (
                        <tr key={`extra-${idx}`} className="edit-row" style={{ borderBottom: '1px solid #333', backgroundColor: '#2c3e50' }}>
                          <td style={{ padding: '8px' }}><input className="input-target" placeholder="새 필드명" style={inputStyle} /></td>
                          <td style={{ padding: '8px' }}><input className="input-source" placeholder="데이터 타입" style={inputStyle} /></td>
                          <td style={{ padding: '8px', textAlign: 'center' }}>
                            <button onClick={() => toggleDeleteRow(filename, idx, true)} style={{ backgroundColor: 'transparent', border: 'none', color: '#ff7675', cursor: 'pointer', fontSize: '18px' }}>❌</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: "'Segoe UI', sans-serif", backgroundColor: theme.bgMain }}>
      <div style={{ width: '260px', backgroundColor: theme.bgSidebar, color: theme.textPrimary, padding: '20px', display: 'flex', flexDirection: 'column' }}>
        <h2 style={{ color: theme.accent, marginBottom: '40px', textAlign: 'center' }}>🛡️ UEBA Control</h2>
        {menuItems.map(item => (
          <div key={item.id} onClick={() => setCurrentView(item.id)} style={{ padding: '15px', marginBottom: '10px', borderRadius: '8px', cursor: 'pointer', backgroundColor: currentView === item.id ? '#34495e' : 'transparent', borderLeft: currentView === item.id ? `4px solid ${theme.accent}` : '4px solid transparent' }}>
            {item.icon} <span style={{ marginLeft: '10px' }}>{item.label}</span>
          </div>
        ))}
      </div>
      <div style={{ flex: 1, padding: '40px', display: 'flex', flexDirection: 'column', maxHeight: '100vh', overflow: 'hidden', color: theme.textPrimary }}>
        {currentView === 'main' ? renderMainDashboard() : currentView === 'parser' ? renderParserView() : currentView === 'ml' ? renderMLView() : (
          <div>
            <h2 style={{ color: theme.textPrimary }}>{menuItems.find(m => m.id === currentView)?.label} 상세 로그</h2>
            <button onClick={() => handleTrigger(currentView, currentView)} disabled={engineMode === 'daemon'} style={{ padding: '10px 20px', backgroundColor: theme.success, color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>▶️ 단계 실행</button>
          </div>
        )}
        {currentView !== 'parser' && (
          <div style={{ flex: 1, backgroundColor: '#111', padding: '20px', borderRadius: '10px', overflowY: 'auto', fontFamily: "monospace", fontSize: '13px', marginTop: '20px' }}>
            {getFilteredLogs().slice().reverse().map((log, i) => (
              <div key={i} style={{ color: log.includes('ERROR') ? theme.danger : log.includes('INFO') ? theme.success : theme.textPrimary }}>{log}</div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;