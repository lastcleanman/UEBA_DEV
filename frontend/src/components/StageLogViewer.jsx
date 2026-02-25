import React, { useState, useEffect } from 'react';
import { theme, menuItems } from '../config/constants';

export default function StageLogViewer({ currentView }) {
  const [logDates, setLogDates] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileLogs, setFileLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const stageLabel = menuItems.find(m => m.id === currentView)?.label || currentView;

  // ⭐️ 최신 v1 API로 변경 및 에러 방어 코드(Fallback) 추가
  useEffect(() => {
    fetch('http://localhost:8000/api/v1/system/log-dates')
      .then(res => {
        if (!res.ok) throw new Error("API not ready");
        return res.json();
      })
      .then(data => setLogDates(data.dates || []))
      .catch(err => {
        console.warn("로그 날짜 목록 조회 실패 (백엔드 API 미구현 상태):", err);
        // 더미 데이터로 화면 깨짐 방지
        setLogDates([{ date: "Today", file: "sample_log.txt", size: "0.0 MB" }]);
      });
  }, [currentView]);

  const handleLoadLogs = async (file) => {
    setIsLoading(true);
    setSelectedFile(file);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/system/logs?file=${file}`);
      if (!res.ok) throw new Error("API not ready");
      const data = await res.json();
      setFileLogs(data.logs || []);
    } catch {
      setFileLogs(["아직 해당 단계의 백엔드 로그 API(/api/v1/system/logs)가 연동되지 않았습니다.", "엔진 컨트롤 센터의 [파이프라인 가동]을 통해 먼저 데이터를 생성해주세요."]);
    }
    setIsLoading(false);
  };

  if (!selectedFile) {
    return (
      <div style={{ color: theme.textPrimary, flex: 1 }}>
        <h2 style={{ marginBottom: '20px' }}>{stageLabel} 이력 목록</h2>
        <div style={{ backgroundColor: theme.bgCard, padding: '25px', borderRadius: '12px' }}>
          <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
            <thead style={{ backgroundColor: theme.bgSidebar, borderBottom: `2px solid ${theme.accent}` }}>
              <tr>
                <th style={{ padding: '15px' }}>날짜</th>
                <th style={{ padding: '15px' }}>로그 파일명</th>
                <th style={{ padding: '15px', textAlign: 'center' }}>상세 보기</th>
              </tr>
            </thead>
            <tbody>
              {logDates.map((item, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #333' }}>
                  <td style={{ padding: '15px', color: theme.success }}>📅 {item.date}</td>
                  <td style={{ padding: '15px', color: theme.textSecondary }}>{item.file}</td>
                  <td style={{ padding: '15px', textAlign: 'center' }}>
                    <button onClick={() => handleLoadLogs(item.file)} style={{ backgroundColor: theme.accent, color: 'white', padding: '6px 12px', borderRadius: '4px', border: 'none', cursor: 'pointer' }}>로그 확인 🔍</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div style={{ color: theme.textPrimary, flex: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', gap: '15px', marginBottom: '15px' }}>
        <button onClick={() => setSelectedFile(null)} style={{ backgroundColor: '#444', color: 'white', padding: '8px 15px', borderRadius: '6px', border: 'none', cursor: 'pointer' }}>⬅️ 뒤로가기</button>
        <h2 style={{ margin: 0 }}>{stageLabel} 터미널</h2>
      </div>
      <div style={{ flex: 1, backgroundColor: '#111', padding: '20px', borderRadius: '10px', fontFamily: "monospace", overflowY: 'auto' }}>
        {isLoading ? <div style={{ color: theme.accent }}>⏳ 로딩 중...</div> : fileLogs.map((log, i) => <div key={i} style={{ padding: '2px 0', color: theme.textSecondary }}>{log}</div>)}
      </div>
    </div>
  );
}