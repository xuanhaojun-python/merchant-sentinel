<template>
  <NoProject v-if="!store.currentId" />
  <div v-else v-loading="loading">
    <div class="toolbar">
      <el-radio-group v-model="days" @change="load">
        <el-radio-button :value="7">近 7 天</el-radio-button>
        <el-radio-button :value="14">近 14 天</el-radio-button>
        <el-radio-button :value="30">近 30 天</el-radio-button>
        <el-radio-button :value="90">近 90 天</el-radio-button>
      </el-radio-group>
      <div class="spacer" />
      <span v-if="d?.kpi.last_run" class="muted">
        最近执行 <el-link type="primary" @click="$router.push(`/runs/${d.kpi.last_run.id}`)">#{{ d.kpi.last_run.id }}</el-link>
        <StatusTag :status="d.kpi.last_run.status" style="margin: 0 6px" />{{ fmt(d.kpi.last_run.created_at) }}
      </span>
      <el-button icon="Refresh" @click="load">刷新</el-button>
    </div>

    <template v-if="d">
      <!-- KPI -->
      <el-row :gutter="12" class="page-card">
        <el-col v-for="k in kpis" :key="k.label" :span="4">
          <el-card shadow="never" class="kpi" :class="{ link: k.to }" @click="k.to && $router.push(k.to)">
            <div class="kpi-label">{{ k.label }}</div>
            <div class="kpi-value">{{ k.value }}<span v-if="k.unit" class="unit">{{ k.unit }}</span></div>
            <div class="kpi-sub">{{ k.sub }}</div>
          </el-card>
        </el-col>
      </el-row>

      <el-empty v-if="!d.kpi.run_count" :description="`近 ${days} 天没有执行记录，去「用例管理」或「套件管理」执行一次吧`" class="page-card" />

      <template v-else>
        <el-row :gutter="12" class="page-card">
          <el-col :span="14">
            <el-card shadow="never" header="每日用例结果（条）"><EChart :option="resultOption" /></el-card>
          </el-col>
          <el-col :span="10">
            <el-card shadow="never" header="每日通过率（不含跳过）"><EChart :option="rateOption" /></el-card>
          </el-col>
        </el-row>

        <el-row :gutter="12" class="page-card">
          <el-col :span="8">
            <el-card shadow="never" header="执行状态分布（次）"><EChart :option="statusOption" height="220px" /></el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="never" header="用例优先级（有效用例）"><EChart :option="priorityOption" height="220px" /></el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="never" header="业务模块用例数"><EChart :option="moduleOption" height="220px" /></el-card>
          </el-col>
        </el-row>
      </template>

      <el-row v-if="d.kpi.run_count" :gutter="12">
        <el-col :span="8">
          <el-card shadow="never" header="失败最多的用例">
            <CaseRank :rows="d.top_failed" value-label="失败" :value="(r) => `${r.failed}/${r.total}`" empty="没有失败用例 🎉" />
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="never">
            <template #header>
              不稳定用例
              <el-tooltip content="统计周期内既通过过、又失败过的用例"><el-icon class="muted"><QuestionFilled /></el-icon></el-tooltip>
            </template>
            <CaseRank :rows="d.flaky" value-label="通过/失败" :value="(r) => `${r.passed}/${r.failed}`" empty="没有不稳定用例" />
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="never" header="耗时最长的用例（平均）">
            <CaseRank :rows="d.slowest" value-label="平均 / 最长" :value="(r) => `${r.avg_duration}s / ${r.max_duration}s`" empty="暂无数据" />
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { computed, h, onMounted, ref } from 'vue'
import { ElTable, ElTableColumn, ElTooltip } from 'element-plus'
import { api } from '../api'
import { useProjectStore } from '../stores/project'
import NoProject from '../components/NoProject.vue'
import StatusTag from '../components/StatusTag.vue'
import EChart from '../components/EChart.vue'
import { fmt } from '../utils'

// 状态色只用于表达状态（通过 / 失败 / 跳过），其余图表用单一系列色
const C = {
  series: '#2a78d6', good: '#0ca30c', critical: '#d03b3b', warning: '#fab219', serious: '#ec835a', neutral: '#a8abb2',
  grid: '#ebeef5', axis: '#dcdfe6', text: '#606266', muted: '#909399', surface: '#ffffff',
}
const STATUS_LABEL = { passed: '通过', failed: '失败', error: '错误', stopped: '已停止', interrupted: '已中断' }
const STATUS_COLOR = { passed: C.good, failed: C.critical, error: C.serious, stopped: C.neutral, interrupted: C.neutral }
const PRIORITY_LABEL = { p0: 'P0', p1: 'P1', p2: 'P2', none: '未分级' }

const store = useProjectStore()
const days = ref(14)
const d = ref(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    d.value = await api.dashboard(store.currentId, days.value)
  } finally {
    loading.value = false
  }
}

const kpis = computed(() => {
  const k = d.value.kpi
  return [
    { label: '有效用例', value: k.case_count, sub: `近 ${days.value} 天执行过 ${k.executed_case_count} 条`, to: '/cases' },
    { label: '执行覆盖率', value: k.exec_coverage ?? '-', unit: k.exec_coverage != null ? '%' : '', sub: '执行过的用例 / 有效用例' },
    { label: '执行次数', value: k.run_count, sub: `共 ${k.result_count} 条用例结果`, to: '/runs' },
    { label: '用例通过率', value: k.pass_rate ?? '-', unit: k.pass_rate != null ? '%' : '', sub: '通过 / (通过 + 失败)', to: '/reports' },
    { label: '平均执行耗时', value: k.avg_run_duration, unit: 's', sub: '每次执行' },
    { label: '套件 / 定时 / 脚本', value: `${k.suite_count} / ${k.schedule_enabled} / ${k.script_count}`, sub: '定时任务仅统计已启用', to: '/suites' },
  ]
})

const axisCommon = {
  axisLine: { lineStyle: { color: C.axis } }, axisTick: { show: false }, axisLabel: { color: C.muted },
}
const valueAxis = (extra = {}) => ({
  type: 'value', splitLine: { lineStyle: { color: C.grid, type: 'solid' } }, axisLabel: { color: C.muted }, ...extra,
})
const tooltip = (extra = {}) => ({
  trigger: 'axis', backgroundColor: '#fff', borderColor: C.axis, textStyle: { color: '#303133', fontSize: 12 }, ...extra,
})
const dates = computed(() => d.value.trend.map((t) => t.date.slice(5)))

const resultOption = computed(() => {
  const seg = (name, key, color) => ({
    name, type: 'bar', stack: 'r', data: d.value.trend.map((t) => t[key]), barMaxWidth: 18,
    itemStyle: { color, borderColor: C.surface, borderWidth: 1, borderRadius: 2 },
    emphasis: { focus: 'series' },
  })
  return {
    grid: { left: 36, right: 12, top: 36, bottom: 24 },
    legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10, textStyle: { color: C.text } },
    tooltip: tooltip({ axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(0,0,0,0.04)' } } }),
    xAxis: { type: 'category', data: dates.value, ...axisCommon },
    yAxis: valueAxis({ minInterval: 1 }),
    series: [seg('通过', 'passed', C.good), seg('失败', 'failed', C.critical), seg('跳过', 'skipped', C.warning)],
  }
})

const rateOption = computed(() => ({
  grid: { left: 44, right: 16, top: 20, bottom: 24 },
  tooltip: tooltip({
    axisPointer: { type: 'line', lineStyle: { color: C.axis } },
    formatter: (ps) => {
      const t = d.value.trend[ps[0].dataIndex]
      return t.pass_rate == null ? `${t.date}<br/>当天无执行`
        : `${t.date}<br/>通过率 <b>${t.pass_rate}%</b><br/>通过 ${t.passed} · 失败 ${t.failed} · 执行 ${t.runs} 次`
    },
  }),
  xAxis: { type: 'category', data: dates.value, boundaryGap: false, ...axisCommon },
  yAxis: valueAxis({ min: 0, max: 100, axisLabel: { color: C.muted, formatter: '{value}%' } }),
  series: [{
    name: '通过率', type: 'line', data: d.value.trend.map((t) => t.pass_rate), connectNulls: true,
    lineStyle: { width: 2, color: C.series }, itemStyle: { color: C.series, borderColor: C.surface, borderWidth: 2 },
    symbol: 'circle', symbolSize: 8, showSymbol: true,
  }],
}))

// 横向条形图：分类在 y 轴，按数值降序（优先级保持固有顺序）
function hbar(entries, colorOf = () => C.series, name = '数量') {
  const rows = [...entries].reverse() // ECharts 的 category y 轴自下而上
  return {
    grid: { left: 8, right: 36, top: 4, bottom: 4, containLabel: true },
    tooltip: tooltip({ trigger: 'item', formatter: (p) => `${p.name}：<b>${p.value}</b>` }),
    xAxis: { type: 'value', show: false },
    yAxis: { type: 'category', data: rows.map((r) => r[0]), ...axisCommon, axisLine: { show: false }, axisLabel: { color: C.text } },
    series: [{
      name, type: 'bar', barMaxWidth: 14, data: rows.map((r) => ({ value: r[1], itemStyle: { color: colorOf(r) } })),
      itemStyle: { borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: 'right', color: C.text, fontSize: 12 },
    }],
  }
}

const statusOption = computed(() => hbar(
  Object.entries(d.value.status_dist).sort((a, b) => b[1] - a[1]).map(([s, n]) => [STATUS_LABEL[s] || s, n, s]),
  (r) => STATUS_COLOR[r[2]] || C.neutral, '执行次数'))
const priorityOption = computed(() => hbar(Object.entries(d.value.priority_dist).map(([p, n]) => [PRIORITY_LABEL[p], n]), undefined, '用例数'))
const moduleOption = computed(() => {
  const entries = Object.entries(d.value.module_dist)
  const top = entries.slice(0, 7)
  const rest = entries.slice(7).reduce((s, [, n]) => s + n, 0)
  return hbar(rest ? [...top, ['其它', rest]] : top, undefined, '用例数')
})

// 小型排名表
const CaseRank = (props) => props.rows.length
  ? h(ElTable, { data: props.rows, size: 'small', showHeader: true }, () => [
    h(ElTableColumn, { label: '用例', minWidth: 160 }, {
      default: ({ row }) => h(ElTooltip, { content: row.nodeid, placement: 'top' }, () => h('span', { class: 'mono' }, row.name)),
    }),
    h(ElTableColumn, { label: props.valueLabel, width: 110, align: 'right' }, { default: ({ row }) => props.value(row) }),
  ])
  : h('div', { class: 'muted empty' }, props.empty)
CaseRank.props = ['rows', 'valueLabel', 'value', 'empty']

onMounted(() => store.currentId && load())
</script>

<style scoped>
.kpi { height: 104px; }
.kpi.link { cursor: pointer; }
.kpi.link:hover { border-color: #c6e2ff; }
.kpi-label { color: #606266; font-size: 13px; }
.kpi-value { font-size: 26px; font-weight: 700; margin: 6px 0 2px; color: #303133; }
.kpi-value .unit { font-size: 14px; font-weight: 400; margin-left: 2px; color: #606266; }
.kpi-sub { color: #909399; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.empty { padding: 24px 0; text-align: center; }
</style>
