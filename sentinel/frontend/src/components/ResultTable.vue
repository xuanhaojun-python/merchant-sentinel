<template>
  <el-table :data="results" border row-key="id" :default-expand-all="expandAll">
    <el-table-column type="expand">
      <template #default="{ row }">
        <div class="detail">
          <div v-if="row.steps.length" class="steps">
            <div class="label">检查步骤</div>
            <div v-for="(s, i) in row.steps" :key="i" class="step">
              <el-icon :color="stepColor(row, i)"><component :is="stepIcon(row, i)" /></el-icon>{{ s }}
            </div>
          </div>
          <div v-if="row.error">
            <div class="label">{{ row.outcome === 'skipped' ? '跳过原因' : '错误信息' }}</div>
            <pre class="error mono" :class="{ skip: row.outcome === 'skipped' }">{{ row.error }}</pre>
          </div>
          <div v-if="row.screenshot">
            <div class="label">失败截图（点击放大）</div>
            <el-image :src="screenshotUrl(runId, row.screenshot)" :preview-src-list="[screenshotUrl(runId, row.screenshot)]"
              fit="contain" class="shot" preview-teleported />
          </div>
          <div v-if="!row.steps.length && !row.error && !row.screenshot" class="muted">无详细信息</div>
        </div>
      </template>
    </el-table-column>
    <el-table-column label="结果" width="90"><template #default="{ row }"><StatusTag :status="row.outcome" effect="dark" /></template></el-table-column>
    <el-table-column label="用例" min-width="320">
      <template #default="{ row }">
        <span class="mono">{{ row.nodeid.split('::').at(-1) }}</span>
        <span class="muted mono" style="margin-left: 8px">{{ row.nodeid.split('::')[0] }}</span>
      </template>
    </el-table-column>
    <el-table-column label="步骤" width="70" align="center"><template #default="{ row }">{{ row.steps.length }}</template></el-table-column>
    <el-table-column label="耗时" width="90"><template #default="{ row }">{{ row.duration.toFixed(2) }}s</template></el-table-column>
  </el-table>
</template>

<script setup>
import { screenshotUrl } from '../api'
import StatusTag from './StatusTag.vue'

defineProps({ results: Array, runId: Number, expandAll: Boolean })

// 失败用例：最后一步标红（失败发生在最后打印的步骤之后）
const isFailedLast = (row, i) => ['failed', 'error'].includes(row.outcome) && i === row.steps.length - 1
const stepIcon = (row, i) => (isFailedLast(row, i) ? 'CircleCloseFilled' : 'CircleCheckFilled')
const stepColor = (row, i) => (isFailedLast(row, i) ? '#f56c6c' : '#67c23a')
</script>

<style scoped>
.detail { padding: 8px 24px 16px 48px; display: flex; flex-direction: column; gap: 12px; }
.label { font-weight: 600; font-size: 13px; margin-bottom: 6px; }
.step { display: flex; align-items: center; gap: 6px; font-size: 13px; padding: 2px 0; }
.error { background: #fef0f0; color: #c45656; padding: 10px; border-radius: 4px; white-space: pre-wrap; word-break: break-all; max-height: 360px; overflow: auto; margin: 0; }
.error.skip { background: #fdf6ec; color: #b88230; }
.shot { max-width: 640px; max-height: 400px; border: 1px solid #e4e7ed; border-radius: 4px; cursor: zoom-in; }
</style>
