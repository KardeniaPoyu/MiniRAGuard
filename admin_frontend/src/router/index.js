import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/warnings', name: 'WarningCenter', component: () => import('../views/WarningCenter.vue') },
  { path: '/clues/:id/workbench', name: 'ClueWorkbench', component: () => import('../views/ClueWorkbench.vue') },
  { path: '/cases', name: 'CaseTrack', component: () => import('../views/CaseTrack.vue') }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
