<template>
  <div>
    <div class="toolbar">
      <el-select v-if="!finishedOnly" v-model="status" placeholder="状态" clearable style="width: 130px" @change="reload">
        <el-option v-for="s in statuses" :key="s.value" :label="s.label" :value="s.value" />
      </el-select>
      <div class="spacer" />
      <el-switch v-model="auto" active-text="自动刷新" />
      <el-button icon="Refresh" @click="load">刷新</el-button>
    </div>
    <el-table v-loading="loading" :data="items" border @row-click="(r) => $router.push(`${linkPrefix}/${r.id}`)" class="clickable">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="状态" width="100"><template #default="{ row }"><StatusTag :status="row.status" /></template></el-table-column>
      <el-table-column label="结果" width="200">
        <template #default="{ row }">
          <template v-if="row.total">
            <span class="ok">✔ {{ row.passed }}</span>
            <span class="bad">✘ {{ row.failed }}</span>
            <span class="skip">↷ {{ row.skipped }}</span>
            <span class="muted"> / {{ row.total }}</span>
          </template>
          <span v-else class="muted">{{ row.selected_nodeids.length }} 条待执行</span>
        </template>
      </el-table-column>
      <el-table-column label="通过率" width="140">
        <template #default="{ row }">
          <el-progress v-if="row.total" :percentage="Math.round((row.passed / row.total) * 100)"
            :status="row.failed ? 'exception' : 'success'" :stroke-width="10" />
        </template>
      </el-table-column>
      <el-table-column prop="environment_name" label="环境" width="90"><template #default="{ row }">{{ row.environment_name || '-' }}</template></el-table-column>
      <el-table-column label="触发" width="80"><template #default="{ row }">{{ row.trigger === 'manual' ? '手动' : '定时' }}</template></el-table-column>
      <el-table-column label="耗时" width="90"><template #default="{ row }">{{ row.duration ? row.duration.toFixed(1) + 's' : '-' }}</template></el-table-column>
      <el-table-column label="创建时间" min-width="160"><template #default="{ row }">{{ fmt(row.created_at) }}</template></el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button v-if="['queued', 'running'].includes(row.status)" link type="danger" @click.stop="stop(row)">停止</el-button>
          <el-button v-else link type="danger" @click.stop="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top: 12px; justify-content: flex-end" layout="total, prev, pager, next" :total="total"
      :page-size="pageSize" v-model:current-page="page" @current-change="load" />
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api'
import { useProjectStore } from '../stores/project'
import StatusTag from './StatusTag.vue'
import { fmt } from '../utils'

const props = defineProps({ finishedOnly: Boolean, linkPrefix: { type: String, default: '/runs' } })
const store = useProjectStore()
const statuses = [
  { value: 'queued', label: '排队中' }, { value: 'running', label: '执行中' }, { value: 'passed', label: '通过' },
  { value: 'failed', label: '失败' }, { value: 'error', label: '错误' }, { value: 'stopped', label: '已停止' },
  { value: 'interrupted', label: '已中断' },
]
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const status = ref('')
const loading = ref(false)
const auto = ref(true)
let timer

async function load(silent = false) {
  if (!store.currentId) return
  if (silent !== true) loading.value = true
  try {
    const params = { project_id: store.currentId, page: page.value, page_size: pageSize, status: status.value || undefined }
    if (props.finishedOnly) params.finished = true
    const r = await api.listRuns(params)
    items.value = r.items
    total.value = r.total
  } finally {
    loading.value = false
  }
}
function reload() { page.value = 1; load() }

async function stop(row) {
  await api.stopRun(row.id)
  ElMessage.success('已发送停止指令')
  load()
}
async function remove(row) {
  await ElMessageBox.confirm(`确定删除执行记录 #${row.id} 及其日志和截图吗？`, '删除确认', { type: 'warning' })
  await api.deleteRun(row.id)
  load()
}

function schedule() {
  clearInterval(timer)
  if (auto.value) timer = setInterval(() => load(true), 3000)
}
watch(auto, schedule)
onMounted(() => { load(); schedule() })
onBeforeUnmount(() => clearInterval(timer))
</script>

<style scoped>
.ok { color: #67c23a; margin-right: 8px; }
.bad { color: #f56c6c; margin-right: 8px; }
.skip { color: #e6a23c; }
.clickable :deep(.el-table__row) { cursor: pointer; }
</style>
