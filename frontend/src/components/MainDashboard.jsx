import React, { useState, useEffect } from 'react';
import { theme } from '../config/constants';

export default function MainDashboard() {
  const [summary, setSummary] = useState({ total_threats: 0, top_risky_users: [], threats_by_type: {} });

  useEffect(() => {
    // ⭐️ 404 에러의 주범이었던 옛날 API 대신, 우리가 만든 최신 V1 통계 API 호출!
    fetch('http://localhost:8000/api/v1/analytics/summary')
      .then(res => res.json())
      .then(data => {
        if (data && data.data) setSummary(data.data);
      })
      .catch(err => console.error("통계 데이터 로드 실패:", err));
  }, []);

  return (
    <div>
      <h2 style={{ color: theme.textPrimary, marginBottom: '20px' }}>📊 보안 관제 요약 (Security Summary)</h2>
      
      <div style={{ display: 'flex', gap: '20px', marginBottom: '30px' }}>
        {/* 총 위협 건수 카드 */}
        <div style={{ flex: 1, padding: '30px', backgroundColor: theme.bgCard, borderRadius: '10px', textAlign: 'center', borderTop: `4px solid ${theme.danger}`, boxShadow: '0 4px 10px rgba(0,0,0,0.2)' }}>
          <h3 style={{ margin: '0 0 15px 0', color: theme.textSecondary }}>누적 위협 탐지 건수</h3>
          <div style={{ fontSize: '3rem', fontWeight: 'bold', color: theme.danger }}>{summary.total_threats} <span style={{fontSize: '1rem', color: '#777'}}>건</span></div>
        </div>

        {/* 고위험 사용자 요약 카드 */}
        <div style={{ flex: 2, padding: '30px', backgroundColor: theme.bgCard, borderRadius: '10px', borderTop: `4px solid ${theme.accent}`, boxShadow: '0 4px 10px rgba(0,0,0,0.2)' }}>
          <h3 style={{ margin: '0 0 15px 0', color: theme.textSecondary }}>🔥 Top 고위험 사용자</h3>
          {summary.top_risky_users.length > 0 ? (
            <div style={{ display: 'flex', gap: '15px' }}>
              {summary.top_risky_users.map((user, idx) => (
                <div key={idx} style={{ backgroundColor: '#111', padding: '10px 15px', borderRadius: '6px', border: '1px solid #333' }}>
                  <span style={{ color: theme.textPrimary, fontWeight: 'bold', display: 'block' }}>{user.user_id}</span>
                  <span style={{ color: theme.danger, fontSize: '0.9rem' }}>{user.count}건 적발</span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: theme.textSecondary, paddingTop: '10px' }}>탐지된 고위험 사용자가 없습니다.</div>
          )}
        </div>
      </div>
      
      <div style={{ padding: '20px', backgroundColor: 'rgba(52, 152, 219, 0.1)', borderRadius: '8px', borderLeft: `4px solid ${theme.accent}`, color: theme.textSecondary, lineHeight: '1.6' }}>
        💡 <b>안내:</b> 엔진의 기동 및 파이프라인(Input~Output) 실시간 제어는 상단의 <b>Admin 계정</b>으로 로그인하셔야 [엔진 컨트롤 센터]가 활성화됩니다.
      </div>
    </div>
  );
}