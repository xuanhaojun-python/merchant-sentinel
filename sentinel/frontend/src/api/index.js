import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({ baseURL: '/api', timeout: 180000 })

http.interceptors.response.use(
  (resp) => resp.data,
  (err) => {
    if (err.config?.silent) return Promise.reject(err)
    const detail = err.response?.data?.detail
    const msg = typeof detail === 'string' ? detail : detail ? JSON.stringify(detail) : err.message
    ElMessage({ type: 'error', message: msg, showClose: true, duration: 5000 })
    return Promise.reject(err)
  },
)

export const api = {
  // 项目
  listProjects: () => http.get('/projects'),
  createProject: (data) => http.post('/projects', data),
  updateProject: (id, data) => http.put(`/projects/${id}`, data),
  deleteProject: (id) => http.delete(`/projects/${id}`),
  // 环境
  listEnvs: (pid) => http.get(`/projects/${pid}/environments`),
  createEnv: (pid, data) => http.post(`/projects/${pid}/environments`, data),
  updateEnv: (id, data) => http.put(`/environments/${id}`, data),
  deleteEnv: (id) => http.delete(`/environments/${id}`),
  // 用例
  syncCases: (pid) => http.post(`/projects/${pid}/cases/sync`),
  listCases: (pid, params) => http.get(`/projects/${pid}/cases`, { params }),
  updateCase: (id, data) => http.put(`/cases/${id}`, data),
  // 执行
  createRun: (data) => http.post('/runs', data),
  listRuns: (params) => http.get('/runs', { params }),
  getRun: (id) => http.get(`/runs/${id}`),
  stopRun: (id) => http.post(`/runs/${id}/stop`),
  deleteRun: (id) => http.delete(`/runs/${id}`),
  getLog: (id) => http.get(`/runs/${id}/log`, { responseType: 'text' }),
  notifyRun: (id, channelIds) => http.post(`/runs/${id}/notify`, { channel_ids: channelIds }),
  // 套件
  listSuites: (pid) => http.get(`/projects/${pid}/suites`),
  createSuite: (pid, data) => http.post(`/projects/${pid}/suites`, data),
  previewSuite: (pid, data) => http.post(`/projects/${pid}/suites/preview`, data),
  updateSuite: (id, data) => http.put(`/suites/${id}`, data),
  deleteSuite: (id) => http.delete(`/suites/${id}`),
  runSuite: (id, envId) => http.post(`/suites/${id}/run`, { environment_id: envId }),
  // 定时任务
  listSchedules: (pid) => http.get(`/projects/${pid}/schedules`),
  createSchedule: (pid, data) => http.post(`/projects/${pid}/schedules`, data),
  updateSchedule: (id, data) => http.put(`/schedules/${id}`, data),
  toggleSchedule: (id) => http.post(`/schedules/${id}/toggle`),
  deleteSchedule: (id) => http.delete(`/schedules/${id}`),
  triggerSchedule: (id) => http.post(`/schedules/${id}/trigger`),
  cronPreview: (expr) => http.get('/cron/preview', { params: { expr }, silent: true }),
  // 通知
  listChannels: () => http.get('/channels'),
  createChannel: (data) => http.post('/channels', data),
  updateChannel: (id, data) => http.put(`/channels/${id}`, data),
  deleteChannel: (id) => http.delete(`/channels/${id}`),
  testChannel: (id) => http.post(`/channels/${id}/test`),
  listNotifications: (params) => http.get('/notifications', { params }),
  resendNotification: (id) => http.post(`/notifications/${id}/resend`),
  // 元素
  syncElements: (pid) => http.post(`/projects/${pid}/elements/sync`),
  listElements: (pid, params) => http.get(`/projects/${pid}/elements`, { params }),
  updateElement: (id, data) => http.put(`/elements/${id}`, data),
  // 脚本 / 录制
  listScripts: (pid) => http.get(`/projects/${pid}/scripts`),
  createScript: (pid, data) => http.post(`/projects/${pid}/scripts`, data),
  getScript: (id) => http.get(`/scripts/${id}`),
  updateScript: (id, data) => http.put(`/scripts/${id}`, data),
  deleteScript: (id) => http.delete(`/scripts/${id}`),
  runScript: (id, envId) => http.post(`/scripts/${id}/run`, { environment_id: envId }),
  exportScript: (id, filename, overwrite = false) => http.post(`/scripts/${id}/export`, { filename }, { params: { overwrite } }),
  recorderStatus: () => http.get('/recorder'),
  startRecording: (pid, data) => http.post(`/projects/${pid}/recorder/start`, data),
  stopRecording: () => http.post('/recorder/stop'),
  // 看板
  dashboard: (pid, days) => http.get(`/projects/${pid}/dashboard`, { params: { days } }),
}

export const screenshotUrl = (runId, path) => `/api/runs/${runId}/${path}`

export function logSocketUrl(runId) {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${location.host}/ws/runs/${runId}/log`
}
