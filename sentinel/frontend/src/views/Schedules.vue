<template>
  <NoProject v-if="!store.currentId" />
  <el-card v-else>
    <div class="toolbar">
      <el-button type="primary" icon="Plus" :disabled="!suites.length" @click="openForm()">新建定时任务</el-button>
      <span v-if="!suites.length" class="muted">请先在「套件管理」创建套件</span>
      <div class="spacer" />
      <span class="muted">按本机时区调度；平台进程需保持运行</span>
      <el-button icon="Refresh" @click="load">刷新</el-button>
    </div>
    <el-table v-loading="loading" :data="items" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="任务" min-width="180">
        <template #default="{ row }">
          <div><b>{{ row.name }}</b></div>
          <div class="muted">套件：{{ row.suite_name }} · 环境：{{ row.environment_name || '工程默认配置' }}</div>
        </template>
      </el-table-column>
      <el-table-column label="执行周期" min-width="170">
        <template #default="{ row }">
          <code class="mono">{{ row.cron }}</code>
          <div class="muted">{{ describeCron(row.cron) }}</div>
        </template>
      </el-table-column>
      <el-table-column label="启用" width="70" align="center">
        <template #default="{ row }"><el-switch :model-value="row.enabled" size="small" @change="toggle(row)" /></template>
      </el-table-column>
      <el-table-column label="下次执行" width="160">
        <template #default="{ row }">{{ row.enabled ? fmt(row.next_run_at) : '-' }}</template>
      </el-table-column>
      <el-table-column label="上次执行" width="210">
        <template #default="{ row }">
          <template v-if="row.last_run_id">
            <el-link type="primary" @click="$router.push(`/runs/${row.last_run_id}`)">#{{ row.last_run_id }}</el-link>
            <StatusTag v-if="row.last_status" :status="row.last_status" style="margin: 0 6px" />
            <span class="muted">{{ fmt(row.last_run_at).slice(5, 16) }}</span>
          </template>
          <span v-else class="muted">-</span>
        </template>
      </el-table-column>
      <el-table-column label="通知" min-width="150">
        <template #default="{ row }">
          <template v-if="row.channel_ids.length && row.notify_on !== 'never'">
            <el-tag size="small" effect="plain" :type="row.notify_on === 'always' ? 'primary' : 'danger'">{{ NOTIFY_ON[row.notify_on] }}</el-tag>
            <div class="muted">{{ channelNames(row.channel_ids) }}</div>
          </template>
          <span v-else class="muted">不通知</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="trigger(row)">立即执行</el-button>
          <el-button link type="primary" @click="openForm(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="form.visible" :title="form.id ? '编辑定时任务' : '新建定时任务'" width="600px">
    <el-form label-width="96px">
      <el-form-item label="任务名称" required><el-input v-model="form.name" maxlength="100" /></el-form-item>
      <el-form-item label="执行套件" required>
        <el-select v-model="form.suite_id" style="width: 100%">
          <el-option v-for="s in suites" :key="s.id" :label="`${s.name}（${s.case_count} 条）`" :value="s.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="执行环境">
        <el-select v-model="form.environment_id" clearable placeholder="不指定则使用工程自身配置" style="width: 100%">
          <el-option v-for="e in envs" :key="e.id" :label="`${e.name}  (${e.base_url})`" :value="e.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="cron 表达式" required>
        <el-input v-model="form.cron" placeholder="分 时 日 月 周，如 0 2 * * *" class="mono" />
        <div class="presets">
          <el-button v-for="p in CRON_PRESETS" :key="p.cron" size="small" @click="form.cron = p.cron">{{ p.label }}</el-button>
        </div>
        <div class="muted" style="width: 100%">
          <template v-if="cronPreview.error"><span class="bad">{{ cronPreview.error }}</span></template>
          <template v-else-if="cronPreview.times.length">最近 5 次：{{ cronPreview.times.map((t) => fmt(t).slice(5, 16)).join('，') }}</template>
        </div>
      </el-form-item>
      <el-form-item label="启用"><el-switch v-model="form.enabled" /></el-form-item>
      <el-divider content-position="left">结果通知</el-divider>
      <el-form-item label="通知时机">
        <el-radio-group v-model="form.notify_on">
          <el-radio-button v-for="(label, v) in NOTIFY_ON" :key="v" :value="v">{{ label }}</el-radio-button>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="通知渠道">
        <el-select v-model="form.channel_ids" multiple placeholder="选择渠道" style="width: 100%" :disabled="form.notify_on === 'never'">
          <el-option v-for="c in channels" :key="c.id" :label="`${c.name}（${CHANNEL_TYPES[c.type]}）`" :value="c.id" :disabled="!c.enabled" />
        </el-select>
        <div v-if="!channels.length" class="muted">还没有通知渠道，可到「通知列表」添加</div>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="form.visible = false">取消</el-button>
      <el-button type="primary" :loading="form.saving" @click="save">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api'
import { useProjectStore } from '../stores/project'
import NoProject from '../components/NoProject.vue'
import StatusTag from '../components/StatusTag.vue'
import { CHANNEL_TYPES, fmt } from '../utils'

const NOTIFY_ON = { failed: '仅失败时', always: '每次', never: '不通知' }
const CRON_PRESETS = [
  { label: '每天 02:00', cron: '0 2 * * *' }, { label: '工作日 09:00', cron: '0 9 * * 1-5' },
  { label: '每小时', cron: '7 * * * *' }, { label: '每 30 分钟', cron: '*/30 * * * *' }, { label: '每周一 08:30', cron: '30 8 * * 1' },
]

const store = useProjectStore()
const router = useRouter()
const items = ref([])
const suites = ref([])
const envs = ref([])
const channels = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    ;[items.value, suites.value, envs.value, channels.value] = await Promise.all([
      api.listSchedules(store.currentId), api.listSuites(store.currentId), api.listEnvs(store.currentId), api.listChannels()])
  } finally {
    loading.value = false
  }
}

const channelNames = (ids) => ids.map((id) => channels.value.find((c) => c.id === id)?.name).filter(Boolean).join('、')

// 常见 cron 的中文描述，复杂表达式只显示原文
function describeCron(expr) {
  const p = expr.trim().split(/\s+/)
  if (p.length !== 5) return ''
  const [mi, h, d, mo, w] = p
  const num = (s) => /^\d+$/.test(s)
  const hm = num(mi) && num(h) ? `${h.padStart(2, '0')}:${mi.padStart(2, '0')}` : ''
  if (hm && d === '*' && mo === '*' && w === '*') return `每天 ${hm}`
  if (hm && d === '*' && mo === '*' && w === '1-5') return `工作日 ${hm}`
  if (hm && d === '*' && mo === '*' && num(w)) return `每周${'日一二三四五六日'[Number(w)]} ${hm}`
  if (hm && num(d) && mo === '*' && w === '*') return `每月 ${d} 日 ${hm}`
  if (num(mi) && h === '*' && d === '*' && mo === '*' && w === '*') return `每小时第 ${mi} 分`
  const m = mi.match(/^\*\/(\d+)$/)
  if (m && h === '*' && d === '*' && mo === '*' && w === '*') return `每 ${m[1]} 分钟`
  return ''
}

const form = reactive({ visible: false, saving: false, id: null, name: '', suite_id: null, environment_id: null, cron: '0 2 * * *', enabled: true, notify_on: 'failed', channel_ids: [] })
const cronPreview = reactive({ times: [], error: '' })

function openForm(row) {
  const defEnv = envs.value.find((e) => e.is_default)?.id ?? null
  Object.assign(form, {
    visible: true, saving: false, id: row?.id ?? null, name: row?.name || '', suite_id: row?.suite_id ?? suites.value[0]?.id,
    environment_id: row ? row.environment_id : defEnv, cron: row?.cron || '0 2 * * *', enabled: row?.enabled ?? true,
    notify_on: row?.notify_on || 'failed', channel_ids: [...(row?.channel_ids || [])],
  })
}

let timer
watch(() => form.cron, (expr) => {
  clearTimeout(timer)
  timer = setTimeout(async () => {
    if (!expr.trim()) return Object.assign(cronPreview, { times: [], error: '' })
    try {
      Object.assign(cronPreview, { times: await api.cronPreview(expr), error: '' })
    } catch (e) {
      Object.assign(cronPreview, { times: [], error: e.response?.data?.detail || 'cron 不合法' })
    }
  }, 300)
}, { immediate: true })

async function save() {
  if (!form.name.trim() || !form.suite_id) return ElMessage.warning('请填写任务名称并选择套件')
  form.saving = true
  try {
    const { visible, saving, id, ...body } = form
    body.name = body.name.trim()
    if (id) await api.updateSchedule(id, body)
    else await api.createSchedule(store.currentId, body)
    form.visible = false
    ElMessage.success('已保存')
    load()
  } finally {
    form.saving = false
  }
}

async function toggle(row) {
  await api.toggleSchedule(row.id)
  load()
}

async function trigger(row) {
  await ElMessageBox.confirm(`立即执行「${row.name}」一次？（按任务配置发送通知）`, '立即执行', { type: 'info' })
  const run = await api.triggerSchedule(row.id)
  router.push(`/runs/${run.id}`)
}

async function remove(row) {
  await ElMessageBox.confirm(`确定删除定时任务「${row.name}」吗？`, '删除确认', { type: 'warning' })
  await api.deleteSchedule(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(() => store.currentId && load())
</script>

<style scoped>
.presets { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 6px; }
.presets .el-button + .el-button { margin-left: 0; }
.bad { color: #f56c6c; }
code { background: #f4f4f5; padding: 1px 4px; border-radius: 3px; }
</style>
