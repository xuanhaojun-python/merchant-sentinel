<template>
  <el-tag :type="meta.type" :effect="effect" size="small">
    <el-icon v-if="status === 'running'" class="is-loading"><Loading /></el-icon>
    {{ meta.label }}
  </el-tag>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ status: String, effect: { type: String, default: 'light' } })
const MAP = {
  queued: { label: '排队中', type: 'info' },
  running: { label: '执行中', type: 'primary' },
  passed: { label: '通过', type: 'success' },
  failed: { label: '失败', type: 'danger' },
  error: { label: '错误', type: 'danger' },
  skipped: { label: '跳过', type: 'warning' },
  stopped: { label: '已停止', type: 'warning' },
  interrupted: { label: '已中断', type: 'warning' },
}
const meta = computed(() => MAP[props.status] || { label: props.status || '-', type: 'info' })
</script>
