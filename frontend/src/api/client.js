import axios from 'axios'

export const api = axios.create({
  baseURL: '',      // Vite proxy 사용: /api 로 호출
  timeout: 15000,
})