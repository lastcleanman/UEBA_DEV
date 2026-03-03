import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  
  server: {
    host: '0.0.0.0',      // 컨테이너 외부 접속 허용
    port: 5173,

    watch: {
      usePolling: true,   // WSL/Docker 파일 변경 감지
    },

    proxy: {
      // 프론트에서 /api 로 시작하는 요청은
      // backend 컨테이너의 8000으로 전달
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/t': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})