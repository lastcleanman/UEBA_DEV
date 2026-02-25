import { useState, useEffect } from 'react';

// App.jsx와 동일한 테마 적용
const theme = {
  bgMain: '#1e1e1e', bgSidebar: '#2c3e50', bgCard: '#252526',
  textPrimary: '#ecf0f1', textSecondary: '#bdc3c7',
  accent: '#3498db', success: '#2ecc71', danger: '#e74c3c',
};

const TIERS = {
  basic: { level: 1, name: "Basic", desc: "Rule 기반 기본 탐지 및 시스템 운영" },
  standard: { level: 2, name: "Standard", desc: "통계 및 행위 프로파일링 (임직원 5,000명 미만 권장)" },
  enterprise: { level: 3, name: "Enterprise", desc: "AI 비지도학습 및 자율 탐지 (초대형 분산 환경 권장)" }
};

const ALL_PLUGINS = [
  { id: "plugins.detect.rule_engine", label: "Rule 기반 지시적 위협 탐지 (Core)", minTier: "basic", isCore: true },
  { id: "plugins.detect.rule_abnormal_time", label: "비정상 시간대 접근 탐지", minTier: "basic", isCore: false },
  { id: "plugins.detect.ml_zscore", label: "Z-Score 통계 프로파일링 (Core)", minTier: "standard", isCore: true },
  { id: "plugins.detect.peer_group", label: "동료 그룹(Peer) 비교 탐지", minTier: "standard", isCore: false },
  { id: "plugins.detect.ml_anomaly", label: "비지도학습(ML) 이상행위 탐지 (Core)", minTier: "enterprise", isCore: true },
  { id: "plugins.detect.gre_auto_rule", label: "AI 자율형 탐지 시나리오 생성(GRE)", minTier: "enterprise", isCore: false },
  { id: "plugins.detect.xai_explain", label: "XAI 위협 판단 근거 시각화", minTier: "enterprise", isCore: false }
];

export default function LicenseManager() {
  const [currentTier, setCurrentTier] = useState("enterprise");
  const [selectedPlugins, setSelectedPlugins] = useState([]);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    // ⭐️ 최신 V1 API로 변경
    fetch('http://localhost:8000/api/v1/system/license')
      .then(res => {
        if (!res.ok) throw new Error("API Not Ready");
        return res.json();
      })
      .then(data => {
        if (data.tier) setCurrentTier(data.tier);
        if (data.plugins) setSelectedPlugins(data.plugins);
      })
      .catch(err => {
        console.warn("라이선스 API 연결 대기 중 (기본값 사용):", err);
      });
  }, []);

  const handleTierChange = (newTier) => {
    setCurrentTier(newTier);
    const tierLevel = TIERS[newTier].level;

    const updatedPlugins = ALL_PLUGINS.filter(p => {
      const pluginLevel = TIERS[p.minTier].level;
      if (pluginLevel > tierLevel) return false;
      if (p.isCore) return true;
      return selectedPlugins.includes(p.id);
    }).map(p => p.id);

    setSelectedPlugins(updatedPlugins);
  };

  const togglePlugin = (pluginId) => {
    setSelectedPlugins(prev => 
      prev.includes(pluginId) ? prev.filter(id => id !== pluginId) : [...prev, pluginId]
    );
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const res = await fetch('http://localhost:8000/api/license', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier: currentTier, plugins: selectedPlugins })
      });
      
      const result = await res.json();
      
      // ⭐️ HTTP 상태 코드가 200번대(성공)인지 확인
      if (res.ok) {
        alert(`✅ ${result.message}`);
      } else {
        // FastAPI는 내부 에러 발생 시 'detail' 필드에 에러 내용을 담아 보냅니다.
        alert(`❌ 서버 에러: ${result.detail || '알 수 없는 오류가 발생했습니다.'}`);
      }
    } catch (error) {
      alert("❌ 통신 중 오류가 발생했습니다. 백엔드 서버가 켜져 있는지 확인하세요.");
    } finally {
      setIsSaving(false);
    }
  };

  const currentLevel = TIERS[currentTier].level;

  return (
    <div style={{ color: theme.textPrimary, overflowY: 'auto', flex: 1, paddingRight: '10px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>🔑 라이선스 및 AI 플러그인 프로비저닝</h2>
        <button 
          onClick={handleSave} disabled={isSaving}
          style={{ backgroundColor: theme.accent, color: 'white', border: 'none', padding: '12px 25px', borderRadius: '6px', fontWeight: 'bold', cursor: isSaving ? 'wait' : 'pointer', fontSize: '15px' }}
        >
          {isSaving ? "적용 중..." : "💾 라이선스 적용 (실시간 자동 반영)"}
        </button>
      </div>

      {/* 1. 티어 선택 영역 */}
      <div style={{ display: 'flex', gap: '20px', marginBottom: '40px' }}>
        {Object.entries(TIERS).map(([tierKey, tierInfo]) => {
          const isActive = currentTier === tierKey;
          return (
            <div 
              key={tierKey} onClick={() => handleTierChange(tierKey)}
              style={{ flex: 1, backgroundColor: isActive ? '#34495e' : theme.bgCard, border: isActive ? `2px solid ${theme.accent}` : '2px solid #444', padding: '20px', borderRadius: '10px', cursor: 'pointer', transition: 'all 0.3s' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                <input type="radio" checked={isActive} readOnly style={{ width: '18px', height: '18px', cursor: 'pointer' }} />
                <h3 style={{ margin: 0, color: isActive ? theme.accent : theme.textPrimary }}>{tierInfo.name}</h3>
              </div>
              <div style={{ color: theme.textSecondary, fontSize: '13px', lineHeight: '1.5' }}>{tierInfo.desc}</div>
            </div>
          );
        })}
      </div>

      {/* 2. 세부 플러그인 선택 영역 */}
      <div style={{ backgroundColor: theme.bgCard, padding: '25px', borderRadius: '12px' }}>
        <h3 style={{ borderBottom: '1px solid #444', paddingBottom: '15px', marginTop: 0 }}>플러그인 활성화 목록</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', marginTop: '20px' }}>
          {ALL_PLUGINS.map(plugin => {
            const pluginLevel = TIERS[plugin.minTier].level;
            const isAllowed = currentLevel >= pluginLevel;
            const isChecked = selectedPlugins.includes(plugin.id);
            const isDisabled = !isAllowed || plugin.isCore;

            return (
              <label key={plugin.id} style={{ display: 'flex', alignItems: 'center', padding: '15px', backgroundColor: isAllowed ? '#1e1e1e' : '#111', border: isChecked ? `1px solid ${theme.accent}` : '1px solid #333', borderRadius: '8px', cursor: isDisabled ? 'not-allowed' : 'pointer', opacity: isAllowed ? 1 : 0.5 }}>
                <input 
                  type="checkbox" checked={isChecked} disabled={isDisabled} onChange={() => togglePlugin(plugin.id)}
                  style={{ width: '18px', height: '18px', marginRight: '15px', cursor: isDisabled ? 'not-allowed' : 'pointer' }}
                />
                <div style={{ flex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '15px', fontWeight: isChecked ? 'bold' : 'normal', color: isAllowed ? theme.textPrimary : '#777' }}>
                    {plugin.label}
                  </span>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    {plugin.isCore && <span style={{ backgroundColor: '#4c1d1d', color: '#ff7675', padding: '4px 10px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold' }}>필수 (Core)</span>}
                    <span style={{ backgroundColor: '#333', color: '#ccc', padding: '4px 10px', borderRadius: '4px', fontSize: '12px' }}>Min: {TIERS[plugin.minTier].name}</span>
                  </div>
                </div>
              </label>
            );
          })}
        </div>
      </div>
    </div>
  );
}