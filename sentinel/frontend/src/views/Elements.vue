<template>
  <NoProject v-if="!store.currentId" />
  <el-row v-else :gutter="16">
    <el-col :span="5">
      <el-card header="页面对象" body-style="padding: 8px">
        <div v-for="p in pages" :key="p.name" class="page-item" :class="{ active: filters.page === p.name }"
          @click="filters.page = filters.page === p.name ? '' : p.name">
          <el-icon><component :is="p.name ? 'Document' : 'Files'" /></el-icon>
          <span class="mono">{{ p.name || '全部' }}</span>
          <span class="muted count">{{ p.count }}</span>
        </div>
      </el-card>
    </el-col>
    <el-col :span="19">
      <el-card>
        <div class="toolbar">
          <el-input v-model="filters.keyword" placeholder="搜索常量名 / 选择器 / 备注" clearable prefix-icon="Search" style="width: 260px" />
          <el-select v-model="filters.kind" placeholder="类型" clearable style="width: 120px">
            <el-option v-for="(v, k) in KINDS" :key="k" :label="v.label" :value="k" />
          </el-select>
          <el-checkbox v-model="filters.unused">仅看未引用</el-checkbox>
          <el-radio-group v-model="filters.status">
            <el-radio-button value="active">有效</el-radio-button>
            <el-radio-button value="removed">已移除</el-radio-button>
          </el-radio-group>
          <div class="spacer" />
          <span v-if="lastSync" class="muted">上次同步 {{ fmt(lastSync) }}</span>
          <el-button icon="Refresh" type="primary" :loading="syncing" @click="sync">从 pages/ 同步</el-button>
        </div>

        <el-alert v-if="!loading && !items.length && filters.status === 'active'" type="info" :closable="false" show-icon
          title="还没有元素数据" description="点击「从 pages/ 同步」扫描 Page Object 中的大写字符串常量（选择器、路径、按钮文案、正则）。" style="margin-bottom: 12px" />

        <el-table v-loading="loading" :data="shown" border>
          <el-table-column label="元素" min-width="200">
            <template #default="{ row }">
              <div class="mono"><b>{{ row.name }}</b></div>
              <div class="muted mono">{{ row.page }}</div>
            </template>
          </el-table-column>
          <el-table-column label="类型" width="80" align="center">
            <template #default="{ row }"><el-tag size="small" :type="KINDS[row.kind]?.type" effect="plain">{{ KINDS[row.kind]?.label || row.kind }}</el-tag></template>
          </el-table-column>
          <el-table-column label="选择器 / 值" min-width="300">
            <template #default="{ row }">
              <div class="selector">
                <code class="mono">{{ row.selector || '（空）' }}</code>
                <el-tooltip content="复制选择器"><el-icon class="copy" @click="copy(row.selector)"><CopyDocument /></el-icon></el-tooltip>
                <el-tooltip content="复制引用"><el-icon class="copy" @click="copy(`${row.page}.${row.name}`)"><Link /></el-icon></el-tooltip>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="位置" min-width="180">
            <template #default="{ row }"><span class="mono muted">{{ row.file }}:{{ row.line }}</span></template>
          </el-table-column>
          <el-table-column label="引用" width="70" align="center">
            <template #default="{ row }">
              <el-tooltip v-if="row.kind === 'path'" content="PATH 通常由基类 goto() 统一使用"><span class="muted">-</span></el-tooltip>
              <span v-else :class="{ warn: !row.refs }">{{ row.refs }}</span>
            </template>
          </el-table-column>
          <el-table-column label="备注" min-width="160">
            <template #default="{ row }">
              <span v-if="row.remark">{{ row.remark }}</span>
              <span v-else class="muted">-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="70" fixed="right">
            <template #default="{ row }"><el-button link type="primary" @click="editRemark(row)">备注</el-button></template>
          </el-table-column>
        </el-table>
        <div class="muted" style="margin-top: 8px">
          共 {{ shown.length }} 个元素<template v-if="unusedCount">，其中 <span class="warn">{{ unusedCount }}</span> 个未被引用（可能已废弃）</template>
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { api } from '../api'
import { useProjectStore } from '../stores/project'
import NoProject from '../components/NoProject.vue'
import { fmt } from '../utils'

const KINDS = {
  css: { label: 'CSS', type: 'primary' }, xpath: { label: 'XPath', type: 'warning' }, text: { label: '文案', type: 'success' },
  regex: { label: '正则', type: 'danger' }, path: { label: '路径', type: 'info' },
}

const store = useProjectStore()
const items = ref([])
const loading = ref(false)
const syncing = ref(false)
const filters = reactive({ keyword: '', kind: '', page: '', status: 'active', unused: false })

const lastSync = computed(() => items.value.reduce((m, e) => (e.synced_at > m ? e.synced_at : m), ''))
const pages = computed(() => {
  const counts = {}
  for (const e of items.value) counts[e.page] = (counts[e.page] || 0) + 1
  return [{ name: '', count: items.value.length }, ...Object.keys(counts).sort().map((name) => ({ name, count: counts[name] }))]
})
const isUnused = (e) => e.kind !== 'path' && !e.refs
const shown = computed(() => {
  const kw = filters.keyword.trim().toLowerCase()
  return items.value.filter((e) =>
    (!filters.page || e.page === filters.page) && (!filters.kind || e.kind === filters.kind) &&
    (!filters.unused || isUnused(e)) &&
    (!kw || [e.name, e.selector, e.remark].some((s) => (s || '').toLowerCase().includes(kw))))
})
const unusedCount = computed(() => shown.value.filter(isUnused).length)

async function load() {
  loading.value = true
  try {
    items.value = await api.listElements(store.currentId, { status: filters.status })
  } finally {
    loading.value = false
  }
}

async function sync() {
  syncing.value = true
  try {
    const r = await api.syncElements(store.currentId)
    ElMessage.success(`同步完成：新增 ${r.added}，更新 ${r.updated}，移除 ${r.removed}`)
    if (r.errors.length) {
      ElNotification({ type: 'warning', title: `${r.errors.length} 个文件解析失败`, duration: 0,
        message: r.errors.map((e) => `${e.file}：${e.error}`).join('\n') })
    }
    load()
  } finally {
    syncing.value = false
  }
}

async function copy(text) {
  await navigator.clipboard.writeText(text)
  ElMessage.success({ message: '已复制', duration: 1200 })
}

async function editRemark(row) {
  const { value } = await ElMessageBox.prompt(`${row.page}.${row.name}`, '编辑备注', { inputValue: row.remark, inputType: 'textarea' })
  await api.updateElement(row.id, { remark: value || '' })
  row.remark = value || ''
}

watch(() => filters.status, load)
onMounted(() => store.currentId && load())
</script>

<style scoped>
.page-item { display: flex; align-items: center; gap: 6px; padding: 7px 8px; border-radius: 4px; cursor: pointer; }
.page-item:hover { background: #f5f7fa; }
.page-item.active { background: #ecf5ff; color: #409eff; }
.page-item .count { margin-left: auto; }
.selector { display: flex; align-items: center; gap: 6px; }
.selector code { background: #f4f4f5; padding: 2px 6px; border-radius: 3px; word-break: break-all; }
.copy { cursor: pointer; color: #909399; flex-shrink: 0; }
.copy:hover { color: #409eff; }
.warn { color: #e6a23c; font-weight: 600; }
</style>
