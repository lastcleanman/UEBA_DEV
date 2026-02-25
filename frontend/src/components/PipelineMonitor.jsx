import React, { useState, useEffect } from 'react';
import { theme } from '../config/constants'; // 기존 테마 임포트

export default function PipelineMonitor() {
  const [status, setStatus] = useState({
    is_running: false,
    current_stage: 'idle',
    last_log: '대기 중...'
  });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/pipeline/status');
        if (response.ok) {
          const data = await response.json();
          setStatus(data);
        }
      } catch (error) {
        console.warn("엔진 상태 폴링 중:", error.message);
      }
    };
    
    fetchStatus();
    const interval = setInterval(fetchStatus, 1000);
    return () => clearInterval(interval);
  }, []);

  const startPipeline = async () => {
    try {
      await fetch('http://localhost:8000/api/v1/pipeline/run', { method: 'POST' });
    } catch {
      alert("파이프라인 실행 요청 실패 (백엔드 확인 필요)");
    }
  };

  const stages = ['init', 'input', 'process', 'detect', 'output', 'done'];
  const currentIndex = stages.indexOf(status.current_stage);

  // 단계별 원형 아이콘 스타일
  const getCircleStyle = (stageId) => {
    const stageIndex = stages.indexOf(stageId);
    if (stageIndex === currentIndex) return { border: `3px solid ${theme.accent}`, color: theme.accent, boxShadow: `0 0 10px ${theme.accent}` };
    if (stageIndex < currentIndex) return { border: `3px solid ${theme.success}`, backgroundColor: theme.success, color: '#000' };
    return { border: '3px solid #555', color: '#555' };
  };

  const steps = [
    { id: 'input', label: '1. 수집 (Input)' },
    { id: 'process', label: '2. 정제 (Process)' },
    { id: 'detect', label: '3. 탐지 (Detect)' },
    { id: 'output', label: '4. 적재 (Output)' }
  ];

  return (
    <div style={{ backgroundColor: theme.bgCard, padding: '20px', borderRadius: '12px', border: '1px solid #333' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <h2 style={{ color: theme.textPrimary, margin: 0, fontSize: '20px' }}>🚀 파이프라인 실시간 제어</h2>
        <button 
          onClick={startPipeline}
          disabled={status.is_running}
          style={{ 
            backgroundColor: status.is_running ? '#555' : theme.accent, 
            color: 'white', border: 'none', padding: '10px 20px', borderRadius: '6px', 
            fontWeight: 'bold', cursor: status.is_running ? 'not-allowed' : 'pointer',
            transition: '0.3s'
          }}
        >
          {status.is_running ? '분석 진행 중...' : '▶️ 파이프라인 가동 (RUN)'}
        </button>
      </div>

      {/* 시각적 흐름도 (Stepper) */}
      <div style={{ position: 'relative', display: 'flex', justifyContent: 'space-between', marginBottom: '20px', padding: '0 20px' }}>
        <div style={{ position: 'absolute', top: '20px', left: '40px', right: '40px', height: '4px', backgroundColor: '#333', zIndex: 0 }}></div>
        
        {steps.map((step) => (
          <div key={step.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 1, backgroundColor: theme.bgCard, padding: '0 10px' }}>
            <div style={{ 
              width: '40px', height: '40px', borderRadius: '50%', backgroundColor: theme.bgMain,
              display: 'flex', justifyContent: 'center', alignItems: 'center', fontWeight: 'bold',
              transition: 'all 0.4s ease', ...getCircleStyle(step.id)
            }}>
              {status.current_stage === 'done' || currentIndex > stages.indexOf(step.id) ? '✓' : ''}
            </div>
            <span style={{ marginTop: '10px', color: theme.textSecondary, fontSize: '13px', fontWeight: 'bold' }}>{step.label}</span>
          </div>
        ))}
      </div>

      {/* 실시간 로그 터미널 */}
      <div style={{ backgroundColor: '#0a0a0a', padding: '15px', borderRadius: '8px', border: '1px solid #222', fontFamily: 'monospace' }}>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: theme.danger }}></div>
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#f1c40f' }}></div>
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: theme.success }}></div>
        </div>
        <div style={{ color: theme.success, fontSize: '13px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
           {status.last_log}
        </div>
      </div>
    </div>
  );
}