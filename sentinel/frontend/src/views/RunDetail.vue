<template>
  <div v-if="run">
    <el-card class="page-card">
      <div class="toolbar" style="margin-bottom: 0">
        <el-button icon="ArrowLeft" @click="$router.push('/runs')">返回</el-button>
        <span class="run-title">执行 #{{ run.id }}</span>
        <StatusTag :status="run.status" effect="dark" />
        <span class="muted">环境：{{ run.environment_name || '工程默认配置' }}</span>
        <span class="muted">用例：{{ run.selected_nodeids.length }} 条</span>
        <span class="muted">创建：{{ fmt(run.created_at) }}</span>
        <span v-if="run.duration" class="muted">耗时：{{ run.duration.toFixed(1) }}s</span>
        <div class="spacer" />
        <el-button v-if="active" type="danger" icon="VideoPause" @click="stop">停止</el-button>
        <template v-else>
          <el-button icon="RefreshRight" @click="rerun">重新执行</el-button>
          <el-button type="primary" icon="PieChart" @click="$router.push(`/reports/${run.id}`)">查看报告</el-button>
        </template>
      </div>
      <el-alert v-if="run.message" :title="run.message" :type="run.status === 'error' ? 'error' : 'warning'" show-icon :closable="false" style="margin-top: 12px" />
    </el-card>

    <el-card class="page-card">
      <template #header>
        <div class="toolbar" style="margin-bottom: 0">
          <span>执行日志</span>
          <el-tag v-if="active" size="small" type="primary">实时</el-tag>
          <div class="spacer" />
          <el-checkbox v-model="follow">自动滚动</el-checkbox>
        </div>
      </template>
      <pre ref="logEl" class="terminal mono">{{ log || (run.status === 'queued' ? '排队中，等待执行…' : '') }}</pre>
    </el-card>

    <el-card v-if="run.results.length" header="用例结果">
      <ResultTable :results="run.results" :run-id="run.id" />
    </el-card>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api, logSocketUrl } from '../api'
import StatusTag from '../components/StatusTag.vue'
import ResultTable from '../components/ResultTable.vue'
import { fmt } from '../utils'

const route = useRoute()
const router = useRouter()
const id = Number(route.params.id)
const run = ref(null)
const log = ref('')
const follow = ref(true)
const logEl = ref()
const active = computed(() => run.value && ['queued', 'running'].includes(run.value.status))
let ws

async function loadRun() {
  run.value = await api.getRun(id)
}

function connect() {
  log.value = ''
  ws = new WebSocket(logSocketUrl(id))
  ws.onmessage = async (e) => {
    const msg = JSON.parse(e.data)
    if (msg.type === 'log') log.value += msg.data
    else if (msg.type === 'status' && run.value && msg.status !== run.value.status) await loadRun()
    else if (msg.type === 'end') await loadRun()
  }
}

watch(log, async () => {
  if (!follow.value) return
  await nextTick()
  if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight
})

async function stop() {
  await api.stopRun(id)
  ElMessage.success('已发送停止指令')
  await loadRun()
}

async function rerun() {
  const r = await api.createRun({ project_id: run.value.project_id, environment_id: run.value.environment_id, nodeids: run.value.selected_nodeids })
  router.push(`/runs/${r.id}`)
}

onMounted(async () => {
  await loadRun()
  connect()
})
onBeforeUnmount(() => ws?.close())
</script>

<style scoped>
.run-title { font-size: 16px; font-weight: 600; }
.terminal { background: #1e1e1e; color: #d4d4d4; padding: 12px 16px; border-radius: 4px; height: 420px; overflow: auto; margin: 0; white-space: pre-wrap; word-break: break-all; line-height: 1.5; }
</style>
