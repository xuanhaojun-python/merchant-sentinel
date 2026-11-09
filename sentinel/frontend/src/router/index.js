import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../layout/Layout.vue'

// 左侧菜单定义：phase 为 null 表示已实现
export const menus = [
  { path: '/dashboard', title: '数据看板', icon: 'DataAnalysis', phase: 4 },
  { path: '/projects', title: '项目管理', icon: 'FolderOpened', component: () => import('../views/Projects.vue') },
  { path: '/elements', title: '元素管理', icon: 'Aim', phase: 3 },
  { path: '/cases', title: '用例管理', icon: 'Tickets', component: () => import('../views/Cases.vue') },
  { path: '/recorder', title: '脚本录制', icon: 'VideoCamera', phase: 3 },
  { path: '/scripts', title: '脚本列表', icon: 'Document', phase: 3 },
  { path: '/suites', title: '套件管理', icon: 'Collection', phase: 2 },
  { path: '/runs', title: '执行记录', icon: 'VideoPlay', component: () => import('../views/Runs.vue') },
  { path: '/reports', title: '报告管理', icon: 'PieChart', component: () => import('../views/Reports.vue') },
  { path: '/schedules', title: '定时任务', icon: 'AlarmClock', phase: 2 },
  { path: '/notifications', title: '通知列表', icon: 'Bell', phase: 2 },
]

const Placeholder = () => import('../views/Placeholder.vue')

const routes = [
  {
    path: '/',
    component: Layout,
    redirect: '/cases',
    children: [
      ...menus.map((m) => ({
        path: m.path.slice(1),
        component: m.component || Placeholder,
        meta: { title: m.title, phase: m.phase },
      })),
      { path: 'runs/:id', component: () => import('../views/RunDetail.vue'), meta: { title: '执行详情', parent: '/runs' } },
      { path: 'reports/:id', component: () => import('../views/ReportDetail.vue'), meta: { title: '测试报告', parent: '/reports' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({ history: createWebHistory(), routes })
router.afterEach((to) => { document.title = `${to.meta.title || ''} · Web3Rec` })
export default router
