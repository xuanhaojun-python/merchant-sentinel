import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({ baseURL: '/api', timeout: 180000 })

http.interceptors.response.use(
  (resp) => resp.data,
  (err) => {
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
}

export const screenshotUrl = (runId, path) => `/api/runs/${runId}/${path}`

export function logSocketUrl(runId) {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${location.host}/ws/runs/${runId}/log`
}
