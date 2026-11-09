<template>
  <el-empty v-if="!store.currentId" description="还没有项目，请先到「项目管理」创建">
    <el-button type="primary" @click="$router.push('/projects')">去创建</el-button>
  </el-empty>

  <el-row v-else :gutter="16">
    <el-col :span="6">
      <el-card header="用例文件" body-style="padding: 8px">
        <el-tree :data="tree" node-key="key" :props="{ label: 'label' }" highlight-current default-expand-all
          :expand-on-click-node="false" @node-click="onNodeClick">
          <template #default="{ data }">
            <span class="tree-node">
              <el-icon><component :is="data.file ? 'Document' : 'Folder'" /></el-icon>
              <span class="mono">{{ data.label }}</span>
              <span class="muted">{{ data.count }}</span>
            </span>
          </template>
        </el-tree>
      </el-card>
    </el-col>

    <el-col :span="18">
      <el-card>
        <div class="toolbar">
          <el-input v-model="filters.keyword" placeholder="搜索 nodeid / 描述 / 备注" clearable style="width: 240px" prefix-icon="Search" />
          <el-select v-model="filters.marker" placeholder="标记" clearable style="width: 140px">
            <el-option v-for="m in markers" :key="m" :label="m" :value="m" />
          </el-select>
          <el-radio-group v-model="filters.status">
            <el-radio-button value="active">有效</el-radio-button>
            <el-radio-button value="removed">已移除</el-radio-button>
          </el-radio-group>
          <div class="spacer" />
          <el-button icon="Refresh" :loading="syncing" @click="sync">同步用例</el-button>
          <el-button type="primary" icon="VideoPlay" :disabled="!selected.length" @click="runSelected">
            执行所选（{{ selected.length }}）
          </el-button>
        </div>

        <el-table ref="tableRef" v-loading="loading" :data="filtered" border row-key="id" @selection-change="(v) => (selected = v)">
          <el-table-column type="selection" width="44" :selectable="(r) => r.status === 'active'" reserve-selection />
          <el-table-column label="用例" min-width="280">
            <template #default="{ row }">
              <div class="mono">{{ row.name }}</div>
              <div class="muted mono">{{ row.file }}</div>
            </template>
          </el-table-column>
          <el-table-column label="标记" width="160">
            <template #default="{ row }">
              <el-tag v-for="m in row.markers" :key="m" size="small" effect="plain" class="tag">{{ m }}</el-tag>
              <el-tag v-for="t in row.tags" :key="'t' + t" size="small" type="warning" effect="plain" class="tag">{{ t }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="描述 / 备注" min-width="180">
            <template #default="{ row }">
              <div>{{ row.docstring || '-' }}</div>
              <div v-if="row.remark" class="muted">备注：{{ row.remark }}</div>
            </template>
          </el-table-column>
          <el-table-column label="最近结果" width="90" align="center">
            <template #default="{ row }"><StatusTag v-if="row.last_outcome" :status="row.last_outcome" /><span v-else class="muted">-</span></template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" :disabled="row.status !== 'active'" @click="runDialog.open([row.nodeid])">执行</el-button>
              <el-button link type="primary" @click="editCase(row)">备注</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="muted" style="margin-top: 8px">共 {{ filtered.length }} 条</div>
      </el-card>
    </el-col>
  </el-row>

  <RunDialog v-if="store.currentId" ref="runDialog" :project-id="store.currentId" />

  <el-dialog v-model="edit.visible" title="编辑备注 / 标签" width="480px">
    <el-form label-width="60px">
      <el-form-item label="用例"><span class="mono">{{ edit.row?.nodeid }}</span></el-form-item>
      <el-form-item label="备注"><el-input v-model="edit.remark" type="textarea" :rows="3" /></el-form-item>
      <el-form-item label="标签">
        <el-select v-model="edit.tags" multiple filterable allow-create default-first-option placeholder="输入后回车" style="width: 100%" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="edit.visible = false">取消</el-button>
      <el-button type="primary" @click="saveCase">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import { api } from '../api'
import { useProjectStore } from '../stores/project'
import StatusTag from '../components/StatusTag.vue'
import RunDialog from '../components/RunDialog.vue'

const store = useProjectStore()
const cases = ref([])
const loading = ref(false)
const syncing = ref(false)
const selected = ref([])
const tableRef = ref()
const runDialog = ref()
const filters = reactive({ keyword: '', marker: '', status: 'active', file: '' })

async function load() {
  if (!store.currentId) return
  loading.value = true
  try {
    cases.value = await api.listCases(store.currentId, { status: filters.status })
  } finally {
    loading.value = false
  }
}

const markers = computed(() => [...new Set(cases.value.flatMap((c) => c.markers))].sort())

const filtered = computed(() => {
  const kw = filters.keyword.trim().toLowerCase()
  return cases.value.filter((c) =>
    (!filters.file || c.file === filters.file || c.file.startsWith(filters.file + '/')) &&
    (!filters.marker || c.markers.includes(filters.marker)) &&
    (!kw || [c.nodeid, c.docstring, c.remark].some((s) => (s || '').toLowerCase().includes(kw))))
})

// 按目录 / 文件构建树
const tree = computed(() => {
  const root = { key: '', label: '全部', count: cases.value.length, children: [] }
  const dirs = new Map()
  for (const c of cases.value) {
    const parts = c.file.split('/')
    const dir = parts.slice(0, -1).join('/') || '.'
    if (!dirs.has(dir)) {
      const node = { key: dir, label: dir, count: 0, children: [] }
      dirs.set(dir, node)
      root.children.push(node)
    }
    const d = dirs.get(dir)
    d.count++
    let f = d.children.find((n) => n.key === c.file)
    if (!f) d.children.push((f = { key: c.file, label: parts.at(-1), count: 0, file: true }))
    f.count++
  }
  return [root]
})

function onNodeClick(node) {
  filters.file = node.key === '.' ? '' : node.key
}

async function sync() {
  syncing.value = true
  try {
    const r = await api.syncCases(store.currentId)
    ElMessage.success(`同步完成：新增 ${r.added}，更新 ${r.updated}，移除 ${r.removed}`)
    if (r.errors.length) {
      ElNotification({ type: 'warning', title: `${r.errors.length} 个文件导入失败`, duration: 0,
        message: r.errors.map((e) => e.file).join('\n') })
    }
    await Promise.all([load(), store.load()])
  } finally {
    syncing.value = false
  }
}

function runSelected() {
  runDialog.value.open(selected.value.map((c) => c.nodeid))
}

const edit = reactive({ visible: false, row: null, remark: '', tags: [] })
function editCase(row) {
  Object.assign(edit, { visible: true, row, remark: row.remark, tags: [...row.tags] })
}
async function saveCase() {
  await api.updateCase(edit.row.id, { remark: edit.remark, tags: edit.tags })
  edit.visible = false
  ElMessage.success('已保存')
  await load()
}

watch(() => filters.status, () => { tableRef.value?.clearSelection(); load() })
onMounted(load)
</script>

<style scoped>
.tree-node { display: flex; align-items: center; gap: 4px; width: 100%; }
.tree-node .muted { margin-left: auto; padding-right: 8px; }
.tag { margin: 2px 4px 2px 0; }
</style>
