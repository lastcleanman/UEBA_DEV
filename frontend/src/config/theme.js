import { ref, watch } from 'vue'

// 1. 초기 테마 설정 (로컬 스토리지 확인, 없으면 기본값 dark)
const savedTheme = localStorage.getItem('ueba-theme') || 'dark'
export const currentTheme = ref(savedTheme)

// 2. 테마 변경 토글 함수
export function toggleTheme() {
  currentTheme.value = currentTheme.value === 'dark' ? 'light' : 'dark'
}

// 3. 테마 상태가 바뀔 때마다 HTML 최상단 태그에 반영 & 저장
export function initTheme() {
  watch(currentTheme, (newTheme) => {
    // <html> 태그에 data-theme 속성을 부여하여 CSS 변수를 스위칭합니다.
    document.documentElement.setAttribute('data-theme', newTheme)
    localStorage.setItem('ueba-theme', newTheme)
  }, { immediate: true })
}