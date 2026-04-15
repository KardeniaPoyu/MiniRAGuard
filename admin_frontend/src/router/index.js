import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/clues', name: 'ClueList', component: () => import('../views/ClueList.vue') },
  { path: '/clues/new', name: 'ClueCreate', component: () => import('../views/ClueCreate.vue') },
  { path: '/clues/:id', name: 'ClueDetail', component: () => import('../views/ClueDetail.vue') },
  { path: '/chat', name: 'ChatView', component: () => import('../views/ChatView.vue') }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
