import React from 'react';
import { theme } from '../config/constants';

export default function LogTerminal({ logs, currentView }) {
  const getFilteredLogs = () => {
    if (currentView === 'main') return logs.slice(-50);
    return logs.filter(log => {
      const lowerLog = log.toLowerCase();
      if (currentView === 'input') return lowerLog.includes('input') || lowerLog.includes('수집') || lowerLog.includes('extract') || lowerLog.includes('multiloggenerator');
      if (currentView === 'rule') return lowerLog.includes('rule') || lowerLog.includes('abnormal') || lowerLog.includes('탐지');
      if (currentView === 'ml') return lowerLog.includes('mlanomaly') || lowerLog.includes('머신러닝') || lowerLog.includes('anomaly');
      if (currentView === 'elastic') return lowerLog.includes('load') || lowerLog.includes('elastic') || lowerLog.includes('적재') || lowerLog.includes('history');
      return true;
    });
  };

  return (
    <div style={{ flex: 1, backgroundColor: '#111', padding: '20px', borderRadius: '10px', overflowY: 'auto', fontFamily: "monospace", fontSize: '13px', marginTop: '20px' }}>
      {getFilteredLogs().slice().reverse().map((log, i) => (
        <div key={i} style={{ color: log.includes('ERROR') ? theme.danger : log.includes('INFO') ? theme.success : theme.textPrimary }}>{log}</div>
      ))}
    </div>
  );
}