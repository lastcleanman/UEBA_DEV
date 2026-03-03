import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// ⭐️ 글로벌 테마 CSS 및 초기화 함수 로드
import './assets/theme.css'
import { initTheme } from './config/theme.js'

// 앱이 그려지기 전에 테마 즉시 적용!
initTheme()

createApp(App).use(router).mount('#app')