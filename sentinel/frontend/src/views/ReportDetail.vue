<template>
  <div v-if="run">
    <el-card class="page-card">
      <div class="toolbar" style="margin-bottom: 0">
        <el-button icon="ArrowLeft" @click="$router.push('/reports')">返回</el-button>
        <span class="run-title">测试报告 #{{ run.id }}</span>
        <StatusTag :status="run.status" effect="dark" />
        <span class="muted">环境：{{ run.environment_name || '工程默认配置' }}</span>
        <span v-if="run.title" class="muted">{{ TRIGGER_TEXT[run.trigger] }}：{{ run.title }}</span>
        <span class="muted">执行时间：{{ fmt(run.started_at || run.created_at) }}</span>
        <div class="spacer" />
        <el-button icon="Bell" @click="openNotify">发送通知</el-button>
        <el-button icon="Document" @click="$router.push(`/runs/${run.id}`)">查看日志</el-button>
      </div>
      <el-alert v-if="run.message" :title="run.message" type="warning" show-icon :closable="false" style="margin-top: 12px" />
    </el-card>

    <el-row :gutter="16" class="page-card">
      <el-col v-for="c in cards" :key="c.label" :span="4">
        <el-card shadow="never" class="stat"><div class="num" :style="{ color: c.color }">{{ c.value }}</div><div class="muted">{{ c.label }}</div></el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="never" class="stat">
          <el-progress type="circle" :width="64" :stroke-width="6" :percentage="rate" :color="run.failed ? '#f56c6c' : '#67c23a'" />
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header>
        <div class="toolbar" style="margin-bottom: 0">
          <span>用例明细</span>
          <el-radio-group v-model="filter" size="small">
            <el-radio-button value="">全部 {{ run.results.length }}</el-radio-button>
            <el-radio-button value="failed">失败 {{ run.failed }}</el-radio-button>
            <el-radio-button value="skipped">跳过 {{ run.skipped }}</el-radio-button>
            <el-radio-button value="passed">通过 {{ run.passed }}</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <ResultTable :key="filter" :results="shown" :run-id="run.id" :expand-all="filter === 'failed'" />
    </el-card>

    <el-dialog v-model="notify.visible" title="发送报告通知" width="440px">
      <el-select v-model="notify.ids" multiple placeholder="选择通知渠道" style="width: 100%">
        <el-option v-for="c in notify.channels" :key="c.id" :label="c.name" :value="c.id" :disabled="!c.enabled" />
      </el-select>
      <div v-if="!notify.channels.length" class="muted" style="margin-top: 8px">还没有通知渠道，请先到「通知列表」添加</div>
      <template #footer>
        <el-button @click="notify.visible = false">取消</el-button>
        <el-button type="primary" :disabled="!notify.ids.length" :loading="notify.sending" @click="sendNotify">发送</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import StatusTag from '../components/StatusTag.vue'
import ResultTable from '../components/ResultTable.vue'
import { fmt, TRIGGER_TEXT } from '../utils'
import { ElMessage } from 'element-plus'

const route = useRoute()
const run = ref(null)
const filter = ref('')

const rate = computed(() => (run.value?.total ? Math.round((run.value.passed / run.value.total) * 100) : 0))
const cards = computed(() => [
  { label: '总计', value: run.value.total, color: '#303133' },
  { label: '通过', value: run.value.passed, color: '#67c23a' },
  { label: '失败', value: run.value.failed, color: '#f56c6c' },
  { label: '跳过', value: run.value.skipped, color: '#e6a23c' },
  { label: '耗时', value: `${run.value.duration.toFixed(1)}s`, color: '#409eff' },
])
const shown = computed(() => {
  if (!filter.value) return run.value.results
  if (filter.value === 'failed') return run.value.results.filter((r) => ['failed', 'error'].includes(r.outcome))
  return run.value.results.filter((r) => r.outcome === filter.value)
})

const notify = reactive({ visible: false, sending: false, ids: [], channels: [] })
async function openNotify() {
  notify.channels = await api.listChannels()
  notify.ids = []
  notify.visible = true
}
async function sendNotify() {
  notify.sending = true
  try {
    const res = await api.notifyRun(run.value.id, notify.ids)
    const failed = res.filter((n) => n.status !== 'success')
    failed.length ? ElMessage.error(`${failed.length} 个渠道发送失败，详见「通知列表」`) : ElMessage.success('通知已发送')
    notify.visible = false
  } finally {
    notify.sending = false
  }
}

onMounted(async () => {
  run.value = await api.getRun(Number(route.params.id))
  if (run.value.failed) filter.value = 'failed'
})
</script>

<style scoped>
.run-title { font-size: 16px; font-weight: 600; }
.stat { text-align: center; height: 96px; display: flex; align-items: center; justify-content: center; }
.stat :deep(.el-card__body) { padding: 12px; }
.num { font-size: 28px; font-weight: 700; line-height: 1.3; }
</style>
