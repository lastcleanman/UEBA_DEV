import React, { useState, useEffect, useCallback } from 'react';
import { theme, inputStyle } from '../config/constants';

export default function ParserManager() {
  const [parsers, setParsers] = useState({});
  const [extraRows, setExtraRows] = useState({});
  const [pendingDelete, setPendingDelete] = useState({});
  
  // ⭐️ 신규 상태: 목록 뷰 vs 상세 뷰 전환을 위한 선택된 파서 상태
  const [selectedParser, setSelectedParser] = useState(null);

  const fetchParsers = useCallback(async () => {
    try {
      // ⭐️ 최신 V1 API로 변경
      const res = await fetch('http://localhost:8000/api/v1/system/parsers');
      if (!res.ok) throw new Error("API Not Ready");
      const data = await res.json();
      setParsers(data.parsers || {});
    } catch (error) { 
      console.warn("파서 API 연결 대기 중입니다.", error);
      setParsers({}); // 404 에러가 나더라도 빈 객체로 렌더링 유지
    }
  }, []);

  useEffect(() => {
    fetchParsers();
  }, [fetchParsers]);

  const addNewRow = (filename) => {
    setExtraRows(prev => ({ ...prev, [filename]: [...(prev[filename] || []), { target: '', source: '' }] }));
  };

  const toggleDeleteRow = (filename, index, isExtra) => {
    if (isExtra) {
      setExtraRows(prev => ({ ...prev, [filename]: prev[filename].filter((_, i) => i !== index) }));
    } else {
      setPendingDelete(prev => {
        const current = prev[filename] || [];
        const updated = current.includes(index) ? current.filter(i => i !== index) : [...current, index];
        return { ...prev, [filename]: updated };
      });
    }
  };

  const handleSaveParser = async (filename) => {
    const container = document.getElementById(`editor-${filename.replace('.', '-')}`);
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
      setExtraRows(prev => ({ ...prev, [filename]: [] }));
      setPendingDelete(prev => ({ ...prev, [filename]: [] }));
      fetchParsers();
    } catch { alert("저장 실패"); }
  };

  // ⭐️ XML 문자열에서 목록에 보여줄 메타데이터(타입, 장비명 등) 추출 함수
  const getParserMetadata = (filename, xmlContent) => {
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(xmlContent, "text/xml");
    const root = xmlDoc.getElementsByTagName("parser")[0] || xmlDoc.getElementsByTagName("LogParser")[0];
    
    const format = root ? (root.getAttribute('format') || root.getElementsByTagName('Format')[0]?.textContent || 'JSON') : 'UNKNOWN';
    const delimiter = root ? root.getAttribute('delimiter') : '';
    
    // 파일명에서 장비명 유추 (예: Firewall_Logs.xml -> Firewall)
    const deviceName = filename.replace('_Logs.xml', '').replace('.xml', '');
    
    // 생성일자는 임시로 오늘 날짜 표기 (추후 백엔드 DB 연동 시 대체 가능)
    const today = new Date().toISOString().split('T')[0];

    return {
      name: filename,
      deviceName: deviceName,
      type: format.toUpperCase(),
      details: delimiter ? `구분자: [ ${delimiter} ]` : '기본 필드 매핑',
      date: today
    };
  };

  // ==========================================
  // 1. [목록 뷰] 파서 전체 리스트 화면
  // ==========================================
  if (!selectedParser) {
    return (
      <div style={{ color: theme.textPrimary, overflowY: 'auto', flex: 1, paddingRight: '10px' }}>
        <h2 style={{ marginBottom: '20px' }}>📄 등록된 파서 목록</h2>
        <div style={{ backgroundColor: theme.bgCard, padding: '25px', borderRadius: '12px', minHeight: '500px' }}>
          
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead style={{ backgroundColor: theme.bgSidebar, borderBottom: `2px solid ${theme.accent}` }}>
              <tr>
                <th style={{ padding: '15px' }}>파서 파일명</th>
                <th style={{ padding: '15px' }}>장비 명 (Source)</th>
                <th style={{ padding: '15px' }}>파싱 포맷</th>
                <th style={{ padding: '15px' }}>포맷 상세</th>
                <th style={{ padding: '15px' }}>생성 일자</th>
                <th style={{ padding: '15px', textAlign: 'center' }}>관리</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(parsers).map(([filename, xmlContent], idx) => {
                const meta = getParserMetadata(filename, xmlContent);
                return (
                  <tr 
                    key={idx} 
                    style={{ borderBottom: '1px solid #333', cursor: 'pointer', transition: '0.2s' }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#333'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    onClick={() => setSelectedParser(filename)} // 행 클릭 시 상세 화면 진입
                  >
                    <td style={{ padding: '15px', fontWeight: 'bold', color: theme.success }}>📜 {meta.name}</td>
                    <td style={{ padding: '15px' }}>{meta.deviceName}</td>
                    <td style={{ padding: '15px' }}>
                      <span style={{ backgroundColor: '#444', padding: '4px 8px', borderRadius: '4px', fontSize: '12px' }}>
                        {meta.type}
                      </span>
                    </td>
                    <td style={{ padding: '15px', color: theme.textSecondary }}>{meta.details}</td>
                    <td style={{ padding: '15px', color: theme.textSecondary }}>{meta.date}</td>
                    <td style={{ padding: '15px', textAlign: 'center' }}>
                      <button 
                        onClick={(e) => { e.stopPropagation(); setSelectedParser(filename); }} 
                        style={{ backgroundColor: theme.accent, color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold' }}
                      >
                        상세 편집 ✏️
                      </button>
                    </td>
                  </tr>
                );
              })}
              {Object.keys(parsers).length === 0 && (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '50px', color: theme.textSecondary }}>
                    등록된 파서 규칙이 없습니다. 엔진 수집 데몬을 실행해 주세요.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  // ==========================================
  // 2. [상세 뷰] 특정 파서 항목 추가/수정 화면
  // ==========================================
  const xmlContent = parsers[selectedParser];
  const parser = new DOMParser();
  const xmlDoc = parser.parseFromString(xmlContent, "text/xml");
  const fieldNodes = Array.from(xmlDoc.getElementsByTagName("field"));
  const rowsData = fieldNodes.map(node => ({
    target: node.getAttribute('target') || '', source: node.getAttribute('source') || ''
  }));

  return (
    <div style={{ color: theme.textPrimary, overflowY: 'auto', flex: 1, paddingRight: '10px' }}>
      
      {/* ⭐️ 상단 뒤로가기 버튼 영역 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '20px' }}>
        <button 
          onClick={() => { setSelectedParser(null); setExtraRows({}); setPendingDelete({}); }}
          style={{ backgroundColor: '#444', color: 'white', border: 'none', padding: '8px 15px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '5px' }}
        >
          ⬅️ 목록으로
        </button>
        <h2 style={{ margin: 0 }}>파서 상세 편집</h2>
      </div>

      <div style={{ backgroundColor: theme.bgCard, padding: '25px', borderRadius: '12px', marginBottom: '40px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px', borderBottom: '1px solid #444', paddingBottom: '15px' }}>
          <h3 style={{ margin: 0, color: theme.success, fontSize: '22px' }}>📜 {selectedParser}</h3>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={() => addNewRow(selectedParser)} style={{ backgroundColor: '#444', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>➕ 항목 추가</button>
            <button onClick={() => handleSaveParser(selectedParser)} style={{ backgroundColor: theme.accent, color: 'white', border: 'none', padding: '10px 25px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>💾 저장 및 반영</button>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '20px', alignItems: 'flex-start' }}>
          <div style={{ flex: 4 }}>
            <div style={{ fontSize: '12px', color: theme.textSecondary, marginBottom: '8px' }}>[ XML 원본 ]</div>
            <pre style={{ backgroundColor: '#111', padding: '15px', borderRadius: '8px', fontSize: '12px', color: '#f8f8f2', border: '1px solid #333', height: '500px', overflow: 'auto' }}>{xmlContent}</pre>
          </div>
          <div id={`editor-${selectedParser.replace('.', '-')}`} style={{ flex: 6 }}>
            <div style={{ fontSize: '12px', color: theme.textSecondary, marginBottom: '8px' }}>[ 필드 편집 ]</div>
            <div style={{ maxHeight: '500px', overflowY: 'auto', border: '1px solid #333', borderRadius: '8px', backgroundColor: '#1e1e1e' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead style={{ position: 'sticky', top: 0, backgroundColor: '#2c3e50', zIndex: 1 }}>
                  <tr style={{ textAlign: 'left', color: theme.textPrimary }}>
                    <th style={{ padding: '12px' }}>Target Key (UML 표준)</th>
                    <th style={{ padding: '12px' }}>Source Value (원본 매핑)</th>
                    <th style={{ padding: '12px', width: '60px', textAlign: 'center' }}>삭제</th>
                  </tr>
                </thead>
                <tbody>
                  {rowsData.map((field, idx) => {
                    const isDel = (pendingDelete[selectedParser] || []).includes(idx);
                    return (
                      <tr key={`fixed-${idx}`} className={`edit-row ${isDel ? 'is-deleted' : ''}`} style={{ borderBottom: '1px solid #333', backgroundColor: isDel ? '#4c1d1d' : 'transparent' }}>
                        <td style={{ padding: '8px' }}><input className="input-target" defaultValue={field.target} style={{ ...inputStyle, textDecoration: isDel ? 'line-through' : 'none' }} disabled={isDel} /></td>
                        <td style={{ padding: '8px' }}><input className="input-source" defaultValue={field.source} style={{ ...inputStyle, textDecoration: isDel ? 'line-through' : 'none' }} disabled={isDel} /></td>
                        <td style={{ padding: '8px', textAlign: 'center' }}><button onClick={() => toggleDeleteRow(selectedParser, idx, false)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '18px' }}>{isDel ? '🔄' : '🗑️'}</button></td>
                      </tr>
                    );
                  })}
                  {(extraRows[selectedParser] || []).map((_, idx) => (
                    <tr key={`extra-${idx}`} className="edit-row" style={{ borderBottom: '1px solid #333', backgroundColor: '#2c3e50' }}>
                      <td style={{ padding: '8px' }}><input className="input-target" placeholder="새 필드명" style={inputStyle} /></td>
                      <td style={{ padding: '8px' }}><input className="input-source" placeholder="데이터 타입" style={inputStyle} /></td>
                      <td style={{ padding: '8px', textAlign: 'center' }}><button onClick={() => toggleDeleteRow(selectedParser, idx, true)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '18px' }}>❌</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}