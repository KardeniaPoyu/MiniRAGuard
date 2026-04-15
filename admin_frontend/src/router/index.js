import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/warnings', name: 'WarningCenter', component: () => import('../views/WarningCenter.vue') },
  { path: '/clues/:id/workbench', name: 'ClueWorkbench', component: () => import('../views/ClueWorkbench.vue') },
  { path: '/cases', name: 'CaseTrack', component: () => import('../views/CaseTrack.vue') },
  { path: '/audit', name: 'AuditLogs', component: () => import('../views/AuditLogs.vue') }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.name !== 'Login' && !token) {
    next({ name: 'Login' })
  } else if (to.name === 'Login' && token) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
