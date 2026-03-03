import { createRouter, createWebHistory } from 'vue-router'
import { h } from 'vue' 
import MainLayout from '@/core_components/layout/MainLayout.vue'
import Dashboard from '@/plugin_views/Dashboard.vue'

// 우리가 구현해 둔 3가지 뷰
import ParserBuilder from '@/plugin_views/standard/ParserBuilder.vue' 
import AISchema from '@/plugin_views/standard/AISchema.vue'
import SchemaViewer from '@/plugin_views/standard/SchemaViewer.vue' 

const createDummyView = (title) => ({
  render: () => h('div', { style: 'padding: 20px;' }, [
    h('h2', { style: 'color: var(--text-main); margin-bottom: 10px;' }, `🚧 ${title}`),
    h('p', { style: 'color: var(--text-muted);' }, '해당 플러그인 화면은 준비 중입니다.')
  ])
})

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', redirect: '/dashboard' }, 
      { path: 'dashboard', component: Dashboard }, 

      // 1. Ingestion (수집/정제)
      { path: 'pipeline/schema', component: AISchema }, 
      { path: 'pipeline/parser', component: ParserBuilder }, 
      { path: 'pipeline/viewer', component: SchemaViewer }, 

      // 2. Detection (분석/탐지)
      { path: 'analysis/detect', component: createDummyView('Rule 기반 탐지 엔진') },
      { path: 'analysis/ml-detect', component: createDummyView('ML 이상 행위 탐지 모델') },
      { path: 'analysis/scoring', component: createDummyView('자산 위험도 스코어링') },

      // 3. Response (대응/SOAR)
      { path: 'response/workflow', component: createDummyView('자동화 대응 워크플로우') },
      { path: 'response/soar', component: createDummyView('SOAR API 연동 설정') },
      { path: 'response/advanced', component: createDummyView('고급 플레이북 에디터') },

      // 4. Settings (공통 설정)
      { path: 'settings/grep', component: createDummyView('Grep 파이프라인 라우팅') },
      { path: 'settings/deploy', component: createDummyView('에이전트 원격 배포') },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router