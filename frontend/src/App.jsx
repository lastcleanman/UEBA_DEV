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
  const [isErrorModalOpen, setIsErrorModalOpen] = useState(false);
  const [extraRows, setExtraRows] = useState({});
  const [pendingDelete, setPendingDelete] = useState({}); // 삭제 대기 항목 관리
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [isAllAnomaliesModalOpen, setIsAllAnomaliesModalOpen] = useState(false);
  const [allAnomalies, setAllAnomalies] = useState([]);

  // ⭐️ 전체 내역 불러오기 함수
  const fetchAllAnomalies = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/anomalies/all');
      const result = await res.json();
      if (result.status === 'success') {
        setAllAnomalies(result.data);
        setIsAllAnomaliesModalOpen(true); // 데이터 수신 성공 시 팝업 열기
      }
    } catch (e) {
      alert("전체 내역을 불러오는데 실패했습니다.");
    }
  };

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
    // 메인 대시보드에서는 최근 50개 전체 출력
    if (currentView === 'main') return logs.slice(-50);

    return logs.filter(log => {
      const lowerLog = log.toLowerCase();
      
      // 1. 데이터 수집 (Input) 필터링
      if (currentView === 'input') {
        return lowerLog.includes('input') || lowerLog.includes('수집') || lowerLog.includes('extract');
      }
      
      // 2. 룰 기반 탐지 (Rule) 필터링
      if (currentView === 'rule') {
        return lowerLog.includes('rule') || lowerLog.includes('abnormal') || lowerLog.includes('탐지');
      }
      
      // 3. AI 이상탐지 (ML) 필터링
      if (currentView === 'ml') {
        return lowerLog.includes('mlanomaly') || lowerLog.includes('머신러닝') || lowerLog.includes('anomaly');
      }
      
      // 4. ES 적재 (Load) 필터링
      if (currentView === 'elastic') {
        return lowerLog.includes('load') || lowerLog.includes('elastic') || lowerLog.includes('적재') || lowerLog.includes('history');
      }
      
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
        {/* 수정된 고위험 이상행위 위젯 */}
        <div style={{ flex: 1, backgroundColor: theme.bgCard, padding: '20px', borderRadius: '10px', borderLeft: `5px solid ${theme.danger}`, position: 'relative' }}>
          <div style={{ color: theme.textSecondary, fontSize: '14px', marginBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>탐지된 고위험 이상행위</span>
          </div>
          <div style={{ color: theme.danger, fontSize: '28px', fontWeight: 'bold' }}>
            {mlMetrics.high_risk_count > 0 
              ? mlMetrics.high_risk_count.toLocaleString() 
              : (mlMetrics.detection_list?.length || 0).toLocaleString()} 
            <span style={{ fontSize: '14px', fontWeight: 'normal' }}> 건</span>
            
          </div>
          {/* ⭐️ 전체 보기 버튼 추가 */}
          <button onClick={fetchAllAnomalies} style={{ background: 'transparent', border: `1px solid ${theme.danger}`, color: theme.danger, borderRadius: '4px', cursor: 'pointer', fontSize: '12px', padding: '4px 8px', transition: '0.2s' }} onMouseEnter={(e) => e.target.style.background = '#4c1d1d'} onMouseLeave={(e) => e.target.style.background = 'transparent'}>
            전체 내역 보기 🔍
          </button>
        </div>
        <div style={{ flex: 1, backgroundColor: theme.bgCard, padding: '20px', borderRadius: '10px', borderLeft: `5px solid ${theme.success}` }}>
          <div style={{ color: theme.textSecondary }}>AI 상태</div>
          <div onClick={() => { if (mlMetrics.status === '에러 발생') setIsErrorModalOpen(true); }}
            style={{ 
              flex: 1, backgroundColor: theme.bgCard, padding: '20px', borderRadius: '10px', 
              borderLeft: `5px solid ${mlMetrics.status === '에러 발생' ? theme.danger : theme.success}`,
              cursor: mlMetrics.status === '에러 발생' ? 'pointer' : 'default'
            }}
          >
            <div style={{ color: mlMetrics.status === '에러 발생' ? theme.danger : theme.success, fontSize: '18px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '10px' }}>
              {mlMetrics.status}
              {mlMetrics.status === '에러 발생' && (
                <button style={{ padding: '4px 8px', fontSize: '12px', backgroundColor: theme.danger, color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                  🔍 상세보기
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
      <div style={{ marginTop: '20px', display: 'flex', gap: '20px' }}>
        {/* 실시간 탐지 내역 리스트 */}
        <div style={{ flex: 2, backgroundColor: theme.bgCard, padding: '20px', borderRadius: '10px' }}>
          <h3 style={{ color: theme.danger }}>🚨 실시간 이상징후 탐지 내역 (Top 5)</h3>
          <table style={{ width: '100%', color: theme.textPrimary, borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #444', textAlign: 'left' }}>
                <th>시간</th><th>사용자</th><th>위험점수</th><th>사유</th>
              </tr>
            </thead>
            <tbody>
              {mlMetrics.detection_list && mlMetrics.detection_list.length > 0 ? (
                mlMetrics.detection_list.map((item, idx) => (
                  <tr 
                    key={idx} 
                    onClick={() => setSelectedAnomaly(item)} // 👈 클릭 시 팝업에 데이터 전달
                    style={{ borderBottom: '1px solid #333', cursor: 'pointer' }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#333'} // 마우스 올리면 하이라이트
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <td style={{ padding: '10px 0' }}>{item.time}</td>
                    <td>{item.user}</td>
                    <td><b style={{ color: theme.danger }}>{item.risk_score}</b></td>
                    <td>{item.reason}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="4" style={{ textAlign: 'center', padding: '30px', color: theme.textSecondary }}>
                    ✅ 현재 탐지된 고위험 이상행위가 없습니다.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
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
      {isErrorModalOpen && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.7)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div style={{ backgroundColor: theme.bgCard, padding: '30px', borderRadius: '12px', width: '600px', border: `1px solid ${theme.danger}`, boxShadow: '0 4px 20px rgba(0,0,0,0.5)' }}>
            <h2 style={{ color: theme.danger, marginTop: 0, borderBottom: '1px solid #444', paddingBottom: '10px' }}>🚨 API 통신 에러 상세</h2>
            <p style={{ color: theme.textSecondary, marginBottom: '20px' }}>
              데이터베이스 연결, 쿼리 구문, 또는 파이썬 코드 실행 중 문제가 발생하여 화면에 데이터를 표시할 수 없습니다.
            </p>
            
            <div style={{ backgroundColor: '#111', padding: '15px', borderRadius: '8px', color: '#ff7675', fontFamily: 'monospace', wordBreak: 'break-all', maxHeight: '200px', overflowY: 'auto', lineHeight: '1.5' }}>
              {mlMetrics.error_detail || "알 수 없는 에러가 발생했습니다. 터미널 로그를 확인하세요."}
            </div>
            
            <div style={{ marginTop: '25px', textAlign: 'right' }}>
              <button 
                onClick={() => setIsErrorModalOpen(false)} 
                style={{ padding: '10px 25px', backgroundColor: '#555', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
      {/* ⭐️ 이상행위 상세 팝업 창 */}
      {selectedAnomaly && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.7)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div style={{ backgroundColor: theme.bgCard, padding: '30px', borderRadius: '12px', width: '450px', border: `1px solid ${theme.danger}`, boxShadow: '0 4px 20px rgba(0,0,0,0.5)' }}>
            
            <h2 style={{ color: theme.danger, marginTop: 0, borderBottom: '1px solid #444', paddingBottom: '10px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              🚨 이상행위 상세 분석
            </h2>
            
            <div style={{ marginBottom: '25px', lineHeight: '2' }}>
              <div><span style={{ color: theme.textSecondary, display: 'inline-block', width: '90px' }}>탐지 시간:</span> <b>{selectedAnomaly.time}</b></div>
              <div><span style={{ color: theme.textSecondary, display: 'inline-block', width: '90px' }}>사용자명:</span> <b style={{ fontSize: '1.2em' }}>{selectedAnomaly.user}</b></div>
              <div><span style={{ color: theme.textSecondary, display: 'inline-block', width: '90px' }}>위험 점수:</span> <b style={{ color: theme.danger, fontSize: '1.2em' }}>{selectedAnomaly.risk_score} 점</b></div>
              <div><span style={{ color: theme.textSecondary, display: 'inline-block', width: '90px' }}>상세 사유:</span> <span style={{ color: theme.accent }}>{selectedAnomaly.reason}</span></div>
            </div>
            
            <div style={{ backgroundColor: '#111', padding: '15px', borderRadius: '8px', color: theme.textSecondary, fontSize: '13px', borderLeft: `3px solid ${theme.accent}` }}>
              💡 <b>AI 권고 조치</b><br />
              해당 사용자의 단기간 다량 요청 및 민감 경로 접근이 확인되었습니다. 사내 보안 정책에 따라 즉각적인 계정 확인이 필요합니다.
            </div>
            
            <div style={{ marginTop: '25px', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button onClick={() => alert(`${selectedAnomaly.user} 사용자의 IP/계정 차단 API를 호출합니다.`)} style={{ padding: '10px 20px', backgroundColor: theme.danger, color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
                🛡️ 즉시 차단
              </button>
              <button onClick={() => setSelectedAnomaly(null)} style={{ padding: '10px 20px', backgroundColor: '#555', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
                닫기
              </button>
            </div>

          </div>
        </div>
      )}
      {/* ⭐️ 전체 이상행위 리스트 팝업 (스크롤 지원) */}
      {isAllAnomaliesModalOpen && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.8)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 999 }}>
          <div style={{ backgroundColor: theme.bgCard, padding: '30px', borderRadius: '12px', width: '800px', border: `1px solid ${theme.danger}`, boxShadow: '0 4px 20px rgba(0,0,0,0.7)', maxHeight: '80vh', display: 'flex', flexDirection: 'column' }}>
            
            {/* 팝업 헤더 */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #444', paddingBottom: '15px', marginBottom: '15px' }}>
              <h2 style={{ color: theme.danger, margin: 0 }}>🚨 전체 탐지 내역 ({allAnomalies.length}건)</h2>
              <button onClick={() => setIsAllAnomaliesModalOpen(false)} style={{ background: 'transparent', border: 'none', color: '#fff', fontSize: '24px', cursor: 'pointer' }}>✖</button>
            </div>

            {/* 스크롤 가능한 테이블 영역 */}
            <div style={{ overflowY: 'auto', flex: 1, paddingRight: '10px' }}>
              <table style={{ width: '100%', color: theme.textPrimary, borderCollapse: 'collapse' }}>
                <thead style={{ position: 'sticky', top: 0, backgroundColor: theme.bgCard, zIndex: 1 }}>
                  <tr style={{ textAlign: 'left' }}>
                    <th style={{ padding: '12px 8px', borderBottom: '2px solid #555' }}>시간</th>
                    <th style={{ padding: '12px 8px', borderBottom: '2px solid #555' }}>사용자</th>
                    <th style={{ padding: '12px 8px', borderBottom: '2px solid #555' }}>위험점수</th>
                    <th style={{ padding: '12px 8px', borderBottom: '2px solid #555' }}>사유</th>
                  </tr>
                </thead>
                <tbody>
                  {allAnomalies.map((item, idx) => (
                    <tr 
                      key={idx} 
                      style={{ borderBottom: '1px solid #333', cursor: 'pointer' }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#333'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                      onClick={() => { 
                        setIsAllAnomaliesModalOpen(false); // 이 창은 닫고
                        setSelectedAnomaly(item);          // 개별 상세 팝업 열기
                      }}
                    >
                      <td style={{ padding: '12px 8px' }}>{item.time}</td>
                      <td style={{ padding: '12px 8px', fontWeight: 'bold' }}>{item.user}</td>
                      <td style={{ padding: '12px 8px' }}><b style={{ color: theme.danger }}>{item.risk_score}</b></td>
                      <td style={{ padding: '12px 8px', color: theme.accent }}>{item.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}

export default App;