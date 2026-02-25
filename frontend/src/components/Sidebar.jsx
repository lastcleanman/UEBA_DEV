import React, { useState } from 'react';
import { theme, menuItems } from '../config/constants';

// ⭐️ App.jsx에서 isAdmin 프롭스를 받아옵니다.
export default function Sidebar({ currentView, setCurrentView, isAdmin }) {
  const [hoveredItem, setHoveredItem] = useState(null);

  // 권한에 따른 메뉴 필터링 (일반 유저는 parser, license 메뉴 접근 불가)
  const visibleMenuItems = menuItems.filter(item => {
    if (!isAdmin && (item.id === 'parser' || item.id === 'license')) return false;
    return true;
  });

  return (
    <div style={{ width: '260px', backgroundColor: theme.bgSidebar, padding: '25px 15px', display: 'flex', flexDirection: 'column', boxShadow: '2px 0 15px rgba(0,0,0,0.3)', zIndex: 10 }}>
      <div style={{ padding: '0 10px', marginBottom: '40px', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ fontSize: '26px' }}>🛡️</span>
        <h2 style={{ color: theme.textPrimary, margin: 0, fontSize: '22px', fontWeight: 'bold', letterSpacing: '0.5px' }}>
          UEBA <span style={{ color: theme.accent }}>Control</span>
        </h2>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {visibleMenuItems.map(item => {
          const isActive = currentView === item.id;
          const isHovered = hoveredItem === item.id;

          return (
            <div key={item.id} onClick={() => setCurrentView(item.id)} onMouseEnter={() => setHoveredItem(item.id)} onMouseLeave={() => setHoveredItem(null)}
              style={{ display: 'flex', alignItems: 'center', padding: '14px 18px', borderRadius: '8px', cursor: 'pointer', transition: 'all 0.2s ease-in-out',
                backgroundColor: isActive ? 'rgba(52, 152, 219, 0.15)' : (isHovered ? 'rgba(255, 255, 255, 0.05)' : 'transparent'),
                borderLeft: isActive ? `4px solid ${theme.accent}` : '4px solid transparent',
                color: isActive ? theme.accent : (isHovered ? theme.textPrimary : theme.textSecondary),
                fontWeight: isActive ? 'bold' : '500',
              }}>
              <span style={{ fontSize: '18px', marginRight: '15px', filter: isActive ? 'none' : 'grayscale(40%) opacity(70%)', transition: 'all 0.2s' }}>
                {item.icon}
              </span>
              <span style={{ fontSize: '15px', letterSpacing: '0.3px' }}>{item.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}