import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // ⭐️ 도커 환경에서는 이 줄이 필수입니다! (또는 '0.0.0.0')
    port: 5173,
    watch: {
      usePolling: true // WSL/Windows 환경에서 파일 변경 실시간 감지
    }
  }
})
