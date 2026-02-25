import React, { useState, useEffect } from 'react';
import { theme } from '../config/constants';

export default function MLDashboard() {
  const [mlMetrics, setMlMetrics] = useState({ 
    total_analyzed: 0, high_risk_count: 0, status: '대기 중', detection_list: [] 
  });

  useEffect(() => {
    const fetchMlMetrics = async () => {
      try {
        // ⭐️ 최신 v1 API 경로 적용 및 에러 핸들링
        const res = await fetch('http://localhost:8000/api/v1/analytics/ml-metrics');
        if (!res.ok) throw new Error("API 연동 대기 중");
        const data = await res.json();
        setMlMetrics(data);
      } catch (e) {
        console.warn("ML 통계 API 대기 중:", e);
        // 에러 시 빈 화면 대신 안전한 기본값 유지
        setMlMetrics(prev => ({ ...prev, status: 'API 연결 대기 중' }));
      }
    };
    fetchMlMetrics();
  }, []);

  const cardStyle = { flex: 1, backgroundColor: theme.bgCard, padding: '24px', borderRadius: '12px', borderTop: `4px solid ${theme.accent}` };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <h2 style={{ color: theme.textPrimary, marginBottom: '25px' }}>🤖 AI 이상탐지 (ML) 모델 현황</h2>
      
      <div style={{ display: 'flex', gap: '20px', marginBottom: '30px' }}>
        <div style={cardStyle}>
          <div style={{ color: theme.textSecondary, marginBottom: '15px' }}>총 학습 데이터</div>
          <div style={{ color: theme.textPrimary, fontSize: '36px', fontWeight: 'bold' }}>{mlMetrics.total_analyzed}</div>
        </div>
        <div style={{ ...cardStyle, borderTop: `4px solid ${theme.danger}` }}>
          <div style={{ color: theme.textSecondary, marginBottom: '15px' }}>탐지된 고위험 이상행위</div>
          <div style={{ color: theme.danger, fontSize: '36px', fontWeight: 'bold' }}>{mlMetrics.high_risk_count}</div>
        </div>
        <div style={{ ...cardStyle, borderTop: `4px solid ${theme.success}` }}>
          <div style={{ color: theme.textSecondary, marginBottom: '15px' }}>엔진 상태</div>
          <div style={{ color: theme.success, fontSize: '24px', fontWeight: 'bold', paddingTop: '10px' }}>{mlMetrics.status}</div>
        </div>
      </div>

      <div style={{ backgroundColor: theme.bgCard, padding: '25px', borderRadius: '12px', flex: 1 }}>
        <h3 style={{ margin: '0 0 20px 0', color: theme.textPrimary }}>🚨 실시간 이상징후 탐지 내역</h3>
        {mlMetrics.detection_list.length > 0 ? (
          <table style={{ width: '100%', color: theme.textPrimary, textAlign: 'left' }}>
            <thead>
              <tr style={{ color: theme.textSecondary }}><th style={{paddingBottom: '10px'}}>시간</th><th>사용자</th><th>위험점수</th><th>사유</th></tr>
            </thead>
            <tbody>
              {/* 데이터 매핑 영역 */}
            </tbody>
          </table>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px', color: theme.textSecondary }}>
            ✅ 현재 탐지된 고위험 이상행위가 없거나 API 연동을 대기 중입니다.
          </div>
        )}
      </div>
    </div>
  );
}