<template>
  <NoProject v-if="!store.currentId" />
  <el-row v-else :gutter="16">
    <el-col :span="9">
      <el-card header="录制设置">
        <el-form label-width="84px" :disabled="recording">
          <el-form-item label="脚本名称" required><el-input v-model="form.name" maxlength="100" placeholder="如：提现表单校验" /></el-form-item>
          <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
          <el-form-item label="起始地址">
            <el-radio-group v-model="form.mode" style="margin-bottom: 6px">
              <el-radio-button value="env">使用环境</el-radio-button>
              <el-radio-button value="url">自定义 URL</el-radio-button>
            </el-radio-group>
            <el-select v-if="form.mode === 'env'" v-model="form.environment_id" placeholder="选择环境" style="width: 100%">
              <el-option v-for="e in envs" :key="e.id" :label="`${e.name}  (${e.base_url})`" :value="e.id" />
            </el-select>
            <el-input v-else v-model="form.url" placeholder="https://..." />
          </el-form-item>
          <el-form-item label="设备模拟">
            <el-select v-model="form.device" clearable filterable allow-create placeholder="桌面浏览器（默认）" style="width: 100%">
              <el-option v-for="d in DEVICES" :key="d" :label="d" :value="d" />
            </el-select>
          </el-form-item>
        </el-form>
        <div class="actions">
          <el-button v-if="!recording" type="danger" icon="VideoCamera" :loading="starting" @click="start">开始录制</el-button>
          <el-button v-else type="warning" icon="SwitchButton" @click="stop">结束录制</el-button>
        </div>
        <el-alert type="info" :closable="false" show-icon style="margin-top: 16px" title="录制说明">
          <ol class="tips">
            <li>点击「开始录制」后，本机会弹出 Chromium 浏览器窗口和 Playwright Inspector。</li>
            <li>在浏览器中操作，右侧会实时显示生成的 pytest 代码。</li>
            <li>关闭浏览器窗口或点击「结束录制」后，脚本自动保存到「脚本列表」。</li>
            <li>Inspector 中的拾取（Pick locator）可以帮你找到稳定的选择器，再整理到「元素管理」对应的 Page Object 中。</li>
          </ol>
        </el-alert>
      </el-card>
    </el-col>

    <el-col :span="15">
      <el-card>
        <template #header>
          <div class="toolbar" style="margin-bottom: 0">
            <span>生成代码</span>
            <el-tag v-if="recording" type="danger" effect="dark" class="rec"><span class="dot" />录制中 · 脚本 #{{ script?.id }}</el-tag>
            <el-tag v-else-if="script" :type="script.status === 'ready' ? 'success' : 'danger'">
              {{ script.status === 'ready' ? '已保存' : '录制失败' }}
            </el-tag>
            <div class="spacer" />
            <template v-if="script && !recording && script.status === 'ready'">
              <el-button size="small" icon="Edit" @click="$router.push({ path: '/scripts', query: { edit: script.id } })">编辑脚本</el-button>
              <el-button size="small" type="primary" icon="VideoPlay" @click="runDialog.open(null, { title: '执行脚本', label: script.name, run: (env) => api.runScript(script.id, env) })">试运行</el-button>
            </template>
          </div>
        </template>
        <el-alert v-if="script?.message" :title="script.message" type="error" :closable="false" style="margin-bottom: 8px" />
        <pre v-if="code" class="code">{{ code }}</pre>
        <el-empty v-else :description="recording ? '等待浏览器中的操作…' : '开始录制后这里实时显示代码'" />
      </el-card>

      <el-card header="最近录制" style="margin-top: 16px">
        <el-table :data="recent" size="small" border>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="name" label="名称" min-width="160" />
          <el-table-column label="状态" width="90"><template #default="{ row }"><el-tag size="small" :type="STATUS[row.status].type">{{ STATUS[row.status].label }}</el-tag></template></el-table-column>
          <el-table-column prop="url" label="起始地址" min-width="200" show-overflow-tooltip />
          <el-table-column label="时间" width="150"><template #default="{ row }">{{ fmt(row.created_at) }}</template></el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="{ row }"><el-button link type="primary" @click="script = row">查看</el-button></template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-col>
  </el-row>
  <RunDialog v-if="store.currentId" ref="runDialog" :project-id="store.currentId" />
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api'
import { useProjectStore } from '../stores/project'
import NoProject from '../components/NoProject.vue'
import RunDialog from '../components/RunDialog.vue'
import { fmt } from '../utils'

const DEVICES = ['iPhone 13', 'iPhone 14 Pro Max', 'Pixel 7', 'iPad Pro 11', 'Galaxy S9+']
const STATUS = { recording: { label: '录制中', type: 'danger' }, ready: { label: '就绪', type: 'success' }, failed: { label: '失败', type: 'info' } }

const store = useProjectStore()
const envs = ref([])
const scripts = ref([])
const script = ref(null)
const starting = ref(false)
const runDialog = ref()
const form = reactive({ name: '', description: '', mode: 'env', environment_id: null, url: '', device: '' })
let timer

const recording = computed(() => script.value?.status === 'recording')
const code = computed(() => script.value?.content || '')
const recent = computed(() => scripts.value.filter((s) => s.source === 'recorded').slice(0, 8))

async function loadScripts() {
  scripts.value = await api.listScripts(store.currentId)
}

async function poll() {
  clearTimeout(timer)
  if (!script.value) return
  script.value = await api.getScript(script.value.id)
  if (script.value.status === 'recording') timer = setTimeout(poll, 1000)
  else {
    loadScripts()
    if (script.value.status === 'ready') ElMessage.success(`录制完成，已保存为脚本 #${script.value.id}`)
  }
}

async function start() {
  if (!form.name.trim()) return ElMessage.warning('请填写脚本名称')
  if (form.mode === 'url' && form.url && !/^https?:\/\//.test(form.url)) return ElMessage.warning('URL 需以 http(s):// 开头')
  starting.value = true
  try {
    script.value = await api.startRecording(store.currentId, {
      name: form.name.trim(), description: form.description, device: form.device || '',
      url: form.mode === 'url' ? form.url.trim() : '', environment_id: form.mode === 'env' ? form.environment_id : null,
    })
    ElMessage.info('浏览器窗口已在本机打开，开始操作吧')
    poll()
  } finally {
    starting.value = false
  }
}

async function stop() {
  await api.stopRecording()
  setTimeout(poll, 500)
}

onMounted(async () => {
  if (!store.currentId) return
  ;[envs.value] = await Promise.all([api.listEnvs(store.currentId), loadScripts()])
  form.environment_id = envs.value.find((e) => e.is_default)?.id ?? envs.value[0]?.id ?? null
  if (!envs.value.length) form.mode = 'url'
  // 页面刷新后恢复进行中的录制
  const st = await api.recorderStatus()
  if (st.recording) {
    script.value = await api.getScript(st.script_id)
    poll()
  }
})
onBeforeUnmount(() => clearTimeout(timer))
</script>

<style scoped>
.actions { display: flex; justify-content: center; }
.tips { margin: 4px 0 0; padding-left: 18px; line-height: 1.8; }
.code { margin: 0; max-height: 520px; overflow: auto; background: #1e1e1e; color: #d4d4d4; padding: 12px 16px; border-radius: 6px;
  font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 12px; line-height: 1.6; }
.rec .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #fff; margin-right: 6px; animation: blink 1s infinite; }
@keyframes blink { 50% { opacity: 0.2; } }
</style>
