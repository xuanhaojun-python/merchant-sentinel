<template>
  <NoProject v-if="!store.currentId" />
  <el-card v-else>
    <div class="toolbar">
      <el-button type="danger" icon="VideoCamera" @click="$router.push('/recorder')">去录制</el-button>
      <el-button icon="Plus" @click="openEditor()">手写脚本</el-button>
      <el-input v-model="filters.keyword" placeholder="搜索名称 / 描述 / 代码" clearable prefix-icon="Search" style="width: 240px" />
      <el-radio-group v-model="filters.source">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="recorded">录制</el-radio-button>
        <el-radio-button value="manual">手写</el-radio-button>
      </el-radio-group>
      <div class="spacer" />
      <el-button icon="Refresh" @click="load">刷新</el-button>
    </div>
    <el-table v-loading="loading" :data="shown" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column label="脚本" min-width="200">
        <template #default="{ row }">
          <div><b>{{ row.name }}</b></div>
          <div class="muted">{{ row.description || '-' }}</div>
        </template>
      </el-table-column>
      <el-table-column label="来源" width="80" align="center">
        <template #default="{ row }"><el-tag size="small" effect="plain" :type="row.source === 'recorded' ? 'danger' : 'info'">{{ row.source === 'recorded' ? '录制' : '手写' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }"><el-tag size="small" :type="STATUS[row.status].type">{{ STATUS[row.status].label }}</el-tag></template>
      </el-table-column>
      <el-table-column label="规模" width="90" align="center">
        <template #default="{ row }"><span class="muted">{{ lines(row) }} 行 / {{ tests(row) }} 用例</span></template>
      </el-table-column>
      <el-table-column label="最近运行" width="110" align="center">
        <template #default="{ row }">
          <el-link v-if="row.last_run_id" @click="$router.push(`/runs/${row.last_run_id}`)"><StatusTag :status="row.last_status || 'queued'" /></el-link>
          <span v-else class="muted">-</span>
        </template>
      </el-table-column>
      <el-table-column label="已导出" min-width="200">
        <template #default="{ row }"><span v-if="row.exported_path" class="mono">{{ row.exported_path }}</span><span v-else class="muted">-</span></template>
      </el-table-column>
      <el-table-column label="更新时间" width="160"><template #default="{ row }">{{ fmt(row.updated_at) }}</template></el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :disabled="row.status !== 'ready'" @click="run(row)">运行</el-button>
          <el-button link type="primary" :disabled="row.status === 'recording'" @click="openEditor(row)">编辑</el-button>
          <el-button link type="primary" :disabled="row.status !== 'ready'" @click="exportCase(row)">导出为用例</el-button>
          <el-button link type="danger" :disabled="row.status === 'recording'" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="editor.visible" :title="editor.id ? `编辑脚本 #${editor.id}` : '手写脚本'" width="900px" top="4vh">
    <el-form label-width="60px">
      <el-row :gutter="12">
        <el-col :span="10"><el-form-item label="名称" required><el-input v-model="editor.name" maxlength="100" /></el-form-item></el-col>
        <el-col :span="14"><el-form-item label="描述"><el-input v-model="editor.description" /></el-form-item></el-col>
      </el-row>
      <el-input v-model="editor.content" type="textarea" :rows="24" class="code-input" spellcheck="false"
        @keydown.tab.prevent="insertTab" />
      <div class="muted" style="margin-top: 6px">
        脚本以 pytest 方式运行，可使用 pytest-playwright 的 <code>page</code> fixture。试运行时不加载工程 tests/conftest.py；导出到 tests/recorded/ 后会使用工程的登录态 fixture。
      </div>
    </el-form>
    <template #footer>
      <el-button @click="editor.visible = false">取消</el-button>
      <el-button type="primary" :loading="editor.saving" @click="saveEditor">保存</el-button>
    </template>
  </el-dialog>

  <RunDialog v-if="store.currentId" ref="runDialog" :project-id="store.currentId" />
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api'
import { useProjectStore } from '../stores/project'
import NoProject from '../components/NoProject.vue'
import RunDialog from '../components/RunDialog.vue'
import StatusTag from '../components/StatusTag.vue'
import { fmt } from '../utils'

const STATUS = { recording: { label: '录制中', type: 'danger' }, ready: { label: '就绪', type: 'success' }, failed: { label: '失败', type: 'info' } }
const TEMPLATE = `from playwright.sync_api import Page, expect


def test_example(page: Page) -> None:
    page.goto("https://example.com")
    print("[Script] 打开首页")
    expect(page).to_have_title("Example Domain")
`

const store = useProjectStore()
const route = useRoute()
const items = ref([])
const loading = ref(false)
const runDialog = ref()
const filters = reactive({ keyword: '', source: '' })

const lines = (s) => (s.content ? s.content.trimEnd().split('\n').length : 0)
const tests = (s) => (s.content.match(/^\s*(async\s+)?def test_/gm) || []).length
const shown = computed(() => {
  const kw = filters.keyword.trim().toLowerCase()
  return items.value.filter((s) => (!filters.source || s.source === filters.source) &&
    (!kw || [s.name, s.description, s.content].some((t) => (t || '').toLowerCase().includes(kw))))
})

async function load() {
  loading.value = true
  try {
    items.value = await api.listScripts(store.currentId)
  } finally {
    loading.value = false
  }
}

const editor = reactive({ visible: false, saving: false, id: null, name: '', description: '', content: '' })
function openEditor(row) {
  Object.assign(editor, { visible: true, saving: false, id: row?.id ?? null, name: row?.name || '',
    description: row?.description || '', content: row ? row.content : TEMPLATE })
}
function insertTab(e) {
  const el = e.target
  const { selectionStart: s, selectionEnd: t } = el
  editor.content = editor.content.slice(0, s) + '    ' + editor.content.slice(t)
  requestAnimationFrame(() => { el.selectionStart = el.selectionEnd = s + 4 })
}
async function saveEditor() {
  if (!editor.name.trim()) return ElMessage.warning('请填写名称')
  editor.saving = true
  try {
    const body = { name: editor.name.trim(), description: editor.description, content: editor.content }
    if (editor.id) await api.updateScript(editor.id, body)
    else await api.createScript(store.currentId, body)
    editor.visible = false
    ElMessage.success('已保存')
    load()
  } finally {
    editor.saving = false
  }
}

function run(row) {
  runDialog.value.open(null, { title: '运行脚本', label: row.name, count: tests(row), run: (env) => api.runScript(row.id, env) })
}

const slug = (s) => s.name.replace(/[^A-Za-z0-9_]+/g, '_').replace(/^_+|_+$/g, '').toLowerCase() || `script_${s.id}`
async function exportCase(row) {
  const def = row.exported_path ? row.exported_path.split('/').pop().replace(/^test_|\.py$/g, '') : slug(row)
  const { value } = await ElMessageBox.prompt('导出到工程 tests/recorded/test_<文件名>.py，并同步到用例管理', '导出为用例', {
    inputValue: def, inputPattern: /^[A-Za-z0-9_]+$/, inputErrorMessage: '只能包含字母、数字、下划线' })
  let r
  try {
    r = await api.exportScript(row.id, value)
  } catch (e) {
    if (e.response?.status !== 409) return
    await ElMessageBox.confirm(`${e.response.data.detail}，是否覆盖？`, '文件已存在', { type: 'warning' })
    r = await api.exportScript(row.id, value, true)
  }
  ElMessage.success(`已导出并同步用例：新增 ${r.added}，更新 ${r.updated}`)
  load()
}

async function remove(row) {
  await ElMessageBox.confirm(`确定删除脚本「${row.name}」吗？已导出到工程的文件不会删除。`, '删除确认', { type: 'warning' })
  await api.deleteScript(row.id)
  load()
}

onMounted(async () => {
  if (!store.currentId) return
  await load()
  const editId = Number(route.query.edit)
  if (editId) {
    const row = items.value.find((s) => s.id === editId)
    if (row) openEditor(row)
    // 不用 router.replace：Layout 以 fullPath 作为 key，改 query 会重建页面并关掉弹窗
    window.history.replaceState(window.history.state, '', route.path)
  }
})
</script>

<style scoped>
.code-input :deep(textarea) { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 12px; line-height: 1.6; background: #fafafa; }
code { background: #f4f4f5; padding: 1px 4px; border-radius: 3px; }
</style>
