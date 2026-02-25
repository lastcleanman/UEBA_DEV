import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import MainDashboard from './components/MainDashboard';
import MLDashboard from './components/MLDashboard';
import ParserManager from './components/ParserManager';
import LicenseManager from './components/LicenseManager';
import PipelineMonitor from './components/PipelineMonitor';
import StageLogViewer from './components/StageLogViewer';
import { theme } from './config/constants';

function App() {
  const [isAdmin, setIsAdmin] = useState(false);
  const [password, setPassword] = useState('');
  const [currentView, setCurrentView] = useState('main'); // 기본 화면: 메인 대시보드

  const handleLogin = (e) => {
    e.preventDefault();
    if (password === 'admin123') { setIsAdmin(true); setPassword(''); }
    else { alert("비밀번호가 틀렸습니다."); }
  };

  // ⭐️ 권한 및 메뉴에 따른 화면 동적 렌더링
  const renderContent = () => {
    switch (currentView) {
      case 'main': return <MainDashboard />;
      case 'ml': return <MLDashboard isAdmin={isAdmin} />;
      case 'parser': return isAdmin ? <ParserManager /> : <Unauthorized />;
      case 'license': return isAdmin ? <LicenseManager /> : <Unauthorized />;
      case 'input':
      case 'rule':
      case 'elastic':
        return <StageLogViewer currentView={currentView} />;
      default: return <MainDashboard />;
    }
  };

  const Unauthorized = () => (
    <div className="flex flex-col items-center justify-center h-full text-gray-400">
      <span className="text-4xl mb-4">🔒</span>
      <h2 className="text-xl">관리자(Admin) 전용 메뉴입니다.</h2>
    </div>
  );

  return (
    <div style={{ display: 'flex', height: '100vh', backgroundColor: theme.bgMain, color: theme.textPrimary, overflow: 'hidden' }}>
      {/* 1. 사이드바 (권한에 따라 메뉴 숨김 처리됨) */}
      <Sidebar currentView={currentView} setCurrentView={setCurrentView} isAdmin={isAdmin} />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
        {/* 2. 상단 네비게이션 및 로그인 바 */}
        <nav style={{ backgroundColor: theme.bgSidebar, padding: '15px 25px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
          <h1 style={{ margin: 0, fontSize: '18px', borderLeft: `4px solid ${theme.accent}`, paddingLeft: '10px' }}>UEBA Enterprise Dashboard</h1>
          <div>
            {!isAdmin ? (
              <form onSubmit={handleLogin} style={{ display: 'flex', gap: '10px' }}>
                <input type="password" placeholder="Admin PW (admin123)" value={password} onChange={(e) => setPassword(e.target.value)}
                  style={{ padding: '6px 10px', borderRadius: '4px', border: 'none', outline: 'none', backgroundColor: '#111', color: 'white' }} />
                <button type="submit" style={{ backgroundColor: theme.accent, color: 'white', border: 'none', padding: '6px 15px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>인증</button>
              </form>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                <span style={{ color: theme.success, fontWeight: 'bold' }}>✓ Admin 접속됨</span>
                <button onClick={() => setIsAdmin(false)} style={{ backgroundColor: theme.danger, color: 'white', border: 'none', padding: '6px 15px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}>로그아웃</button>
              </div>
            )}
          </div>
        </nav>

        {/* 3. 관리자 전용 파이프라인 엔진 모니터 (상단 고정) */}
        {isAdmin && (
          <div style={{ padding: '20px', backgroundColor: '#1a1a1a', borderBottom: '1px solid #333' }}>
            <h3 style={{ margin: '0 0 10px 0', color: theme.accent }}>⚙️ 엔진 컨트롤 센터</h3>
            <PipelineMonitor />
          </div>
        )}

        {/* 4. 메인 컨텐츠 영역 */}
        <div style={{ padding: '25px', flex: 1 }}>
          {renderContent()}
        </div>
      </div>
    </div>
  );
}

export default App;