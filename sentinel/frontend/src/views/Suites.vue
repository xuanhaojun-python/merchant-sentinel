<template>
  <NoProject v-if="!store.currentId" />
  <el-card v-else>
    <div class="toolbar">
      <el-button type="primary" icon="Plus" @click="openForm()">新建套件</el-button>
      <el-input v-model="keyword" placeholder="搜索套件名称 / 描述" clearable prefix-icon="Search" style="width: 240px" />
      <div class="spacer" />
      <el-button icon="Refresh" @click="load">刷新</el-button>
    </div>
    <el-table v-loading="loading" :data="shown" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="套件" min-width="200">
        <template #default="{ row }">
          <div><b>{{ row.name }}</b></div>
          <div class="muted">{{ row.description || '-' }}</div>
        </template>
      </el-table-column>
      <el-table-column label="组成" min-width="240">
        <template #default="{ row }">
          <div v-if="row.nodeids.length">固定用例 {{ row.nodeids.length }} 条</div>
          <div v-if="row.marker_expr">marker：<code class="mono">{{ row.marker_expr }}</code></div>
          <el-tooltip v-if="row.missing.length" placement="top">
            <template #content><div v-for="m in row.missing" :key="m" class="mono">{{ m }}</div></template>
            <el-tag size="small" type="warning">{{ row.missing.length }} 条已失效</el-tag>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column label="可执行用例" width="100" align="center">
        <template #default="{ row }"><b>{{ row.case_count }}</b></template>
      </el-table-column>
      <el-table-column label="最近执行" width="220">
        <template #default="{ row }">
          <template v-if="row.last_run">
            <el-link type="primary" @click="$router.push(`/runs/${row.last_run.id}`)">#{{ row.last_run.id }}</el-link>
            <StatusTag :status="row.last_run.status" style="margin: 0 6px" />
            <span class="muted">{{ fmt(row.last_run.created_at).slice(5, 16) }}</span>
          </template>
          <span v-else class="muted">从未执行</span>
        </template>
      </el-table-column>
      <el-table-column label="更新时间" width="160"><template #default="{ row }">{{ fmt(row.updated_at) }}</template></el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :disabled="!row.case_count" @click="run(row)">执行</el-button>
          <el-button link type="primary" @click="$router.push({ path: '/runs', query: { suite: row.id } })">历史</el-button>
          <el-button link type="primary" @click="openForm(row)">编辑</el-button>
          <el-button link type="primary" @click="openForm(row, true)">复制</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="form.visible" :title="form.id ? '编辑套件' : '新建套件'" width="900px" top="5vh">
    <el-form label-width="96px">
      <el-form-item label="套件名称" required><el-input v-model="form.name" maxlength="100" /></el-form-item>
      <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
      <el-form-item label="marker 表达式">
        <el-input v-model="form.marker_expr" placeholder="与 pytest -m 语法一致，如：p0 and not fund" clearable>
          <template #append>
            <el-dropdown @command="(v) => (form.marker_expr = v)">
              <el-button>常用</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item v-for="e in EXPR_PRESETS" :key="e" :command="e"><code>{{ e }}</code></el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-input>
        <div class="muted">可用标记：<span v-for="m in markers" :key="m" class="marker" @click="appendMarker(m)">{{ m }}</span></div>
      </el-form-item>
      <el-form-item label="固定用例">
        <div style="width: 100%">
          <div class="toolbar" style="margin-bottom: 8px">
            <el-input v-model="pick.keyword" placeholder="筛选用例" clearable size="small" style="width: 220px" prefix-icon="Search" />
            <span class="muted">已选 {{ form.nodeids.length }} 条（与 marker 匹配结果取并集）</span>
          </div>
          <el-table ref="pickTable" :data="pickable" height="260" size="small" border row-key="nodeid"
            @selection-change="onPick">
            <el-table-column type="selection" width="40" reserve-selection />
            <el-table-column label="用例" min-width="300">
              <template #default="{ row }"><span class="mono">{{ row.nodeid }}</span></template>
            </el-table-column>
            <el-table-column label="标记" width="220">
              <template #default="{ row }"><el-tag v-for="m in row.markers" :key="m" size="small" class="tag">{{ m }}</el-tag></template>
            </el-table-column>
          </el-table>
        </div>
      </el-form-item>
      <el-form-item label="预览">
        <div style="width: 100%">
          <span>共 <b>{{ preview.nodeids.length }}</b> 条可执行用例</span>
          <span v-if="preview.error" class="bad" style="margin-left: 8px">{{ preview.error }}</span>
          <el-collapse v-if="preview.nodeids.length" style="margin-top: 4px">
            <el-collapse-item title="展开查看">
              <div v-for="n in preview.nodeids" :key="n" class="mono">{{ n }}</div>
            </el-collapse-item>
          </el-collapse>
        </div>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="form.visible = false">取消</el-button>
      <el-button type="primary" :loading="form.saving" @click="save">保存</el-button>
    </template>
  </el-dialog>

  <RunDialog v-if="store.currentId" ref="runDialog" :project-id="store.currentId" />
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api'
import { useProjectStore } from '../stores/project'
import NoProject from '../components/NoProject.vue'
import RunDialog from '../components/RunDialog.vue'
import StatusTag from '../components/StatusTag.vue'
import { fmt } from '../utils'

const EXPR_PRESETS = ['p0', 'p0 and not fund', 'smoke', 'p0 or p1', 'not fund and not creates_data', 'security']

const store = useProjectStore()
const suites = ref([])
const cases = ref([])
const loading = ref(false)
const keyword = ref('')
const runDialog = ref()
const pickTable = ref()

const shown = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return suites.value.filter((s) => !kw || `${s.name} ${s.description}`.toLowerCase().includes(kw))
})
const markers = computed(() => [...new Set(cases.value.flatMap((c) => c.markers))].sort())

async function load() {
  loading.value = true
  try {
    ;[suites.value, cases.value] = await Promise.all([api.listSuites(store.currentId), api.listCases(store.currentId)])
  } finally {
    loading.value = false
  }
}

// ── 表单 ──
const form = reactive({ visible: false, saving: false, id: null, name: '', description: '', marker_expr: '', nodeids: [] })
const pick = reactive({ keyword: '' })
const preview = reactive({ nodeids: [], error: '' })
let syncingSelection = false

const pickable = computed(() => {
  const kw = pick.keyword.trim().toLowerCase()
  return cases.value.filter((c) => !kw || `${c.nodeid} ${c.markers.join(' ')} ${c.docstring}`.toLowerCase().includes(kw))
})

async function openForm(row, copy = false) {
  Object.assign(form, {
    visible: true, saving: false, id: copy ? null : row?.id ?? null,
    name: row ? (copy ? `${row.name} 副本` : row.name) : '', description: row?.description || '',
    marker_expr: row?.marker_expr || '', nodeids: [...(row?.nodeids || [])],
  })
  pick.keyword = ''
  await nextTick()
  syncingSelection = true
  pickTable.value.clearSelection()
  const set = new Set(form.nodeids)
  cases.value.filter((c) => set.has(c.nodeid)).forEach((c) => pickTable.value.toggleRowSelection(c, true))
  // 失效的 nodeid 不在表格中，保留在 form.nodeids 里由用户决定是否清理
  syncingSelection = false
  refreshPreview()
}

function onPick(rows) {
  if (syncingSelection) return
  const valid = new Set(cases.value.map((c) => c.nodeid))
  const stale = form.nodeids.filter((n) => !valid.has(n))
  form.nodeids = [...stale, ...rows.map((r) => r.nodeid)]
}

function appendMarker(m) {
  form.marker_expr = form.marker_expr.trim() ? `${form.marker_expr.trim()} and ${m}` : m
}

let previewTimer
function refreshPreview() {
  clearTimeout(previewTimer)
  previewTimer = setTimeout(async () => {
    try {
      const r = await api.previewSuite(store.currentId, { nodeids: form.nodeids, marker_expr: form.marker_expr })
      Object.assign(preview, { nodeids: r.nodeids, error: '' })
    } catch (e) {
      Object.assign(preview, { nodeids: [], error: e.response?.data?.detail || '预览失败' })
    }
  }, 300)
}
watch(() => [form.marker_expr, form.nodeids.length], () => form.visible && refreshPreview())

async function save() {
  if (!form.name.trim()) return ElMessage.warning('请填写套件名称')
  form.saving = true
  try {
    const body = { name: form.name.trim(), description: form.description, marker_expr: form.marker_expr.trim(), nodeids: form.nodeids }
    if (form.id) await api.updateSuite(form.id, body)
    else await api.createSuite(store.currentId, body)
    form.visible = false
    ElMessage.success('已保存')
    load()
  } finally {
    form.saving = false
  }
}

function run(row) {
  runDialog.value.open(null, { title: '执行套件', label: row.name, count: row.case_count, run: (env) => api.runSuite(row.id, env) })
}

async function remove(row) {
  await ElMessageBox.confirm(`确定删除套件「${row.name}」吗？历史执行记录会保留。`, '删除确认', { type: 'warning' })
  await api.deleteSuite(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(() => store.currentId && load())
</script>

<style scoped>
.marker { display: inline-block; margin: 0 6px 0 0; color: #409eff; cursor: pointer; }
.marker:hover { text-decoration: underline; }
.tag { margin: 1px 4px 1px 0; }
.bad { color: #f56c6c; }
code { background: #f4f4f5; padding: 1px 4px; border-radius: 3px; }
</style>
