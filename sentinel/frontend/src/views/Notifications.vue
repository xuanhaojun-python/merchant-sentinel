<template>
  <el-card>
    <el-tabs v-model="tab">
      <el-tab-pane label="发送记录" name="logs">
        <div class="toolbar">
          <el-select v-model="logFilter.channel_id" placeholder="渠道" clearable style="width: 180px" @change="reloadLogs">
            <el-option v-for="c in channels" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
          <el-radio-group v-model="logFilter.status" @change="reloadLogs">
            <el-radio-button value="">全部</el-radio-button>
            <el-radio-button value="success">成功</el-radio-button>
            <el-radio-button value="failed">失败</el-radio-button>
          </el-radio-group>
          <div class="spacer" />
          <el-button icon="Refresh" @click="loadLogs">刷新</el-button>
        </div>
        <el-table v-loading="logLoading" :data="logs" border>
          <el-table-column type="expand">
            <template #default="{ row }">
              <div class="detail">
                <div class="label">消息内容</div>
                <pre>{{ row.content }}</pre>
                <div class="label">渠道响应</div>
                <pre>{{ row.response || '-' }}</pre>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === 'success' ? 'success' : 'danger'">{{ row.status === 'success' ? '成功' : '失败' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="渠道" width="180">
            <template #default="{ row }">{{ row.channel_name }} <span class="muted">{{ CHANNEL_TYPES[row.channel_type] }}</span></template>
          </el-table-column>
          <el-table-column prop="title" label="标题" min-width="280" show-overflow-tooltip />
          <el-table-column label="关联执行" width="100">
            <template #default="{ row }">
              <el-link v-if="row.run_id" type="primary" @click="$router.push(`/reports/${row.run_id}`)">#{{ row.run_id }}</el-link>
              <span v-else class="muted">测试消息</span>
            </template>
          </el-table-column>
          <el-table-column label="时间" width="160"><template #default="{ row }">{{ fmt(row.created_at) }}</template></el-table-column>
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" :disabled="!row.channel_id" @click="resend(row)">重发</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination style="margin-top: 12px; justify-content: flex-end" layout="total, prev, pager, next" :total="logTotal"
          :page-size="20" v-model:current-page="logPage" @current-change="loadLogs" />
      </el-tab-pane>

      <el-tab-pane label="通知渠道" name="channels">
        <div class="toolbar">
          <el-button type="primary" icon="Plus" @click="openForm()">新建渠道</el-button>
          <span class="muted">渠道全局共享，在「定时任务」中选择使用；报告详情页也可手动发送</span>
        </div>
        <el-table :data="channels" border>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="name" label="名称" width="180" />
          <el-table-column label="类型" width="120"><template #default="{ row }">{{ CHANNEL_TYPES[row.type] }}</template></el-table-column>
          <el-table-column label="Webhook 地址" min-width="300">
            <template #default="{ row }"><span class="mono">{{ maskUrl(row.url) }}</span></template>
          </el-table-column>
          <el-table-column label="加签" width="70" align="center"><template #default="{ row }">{{ row.secret ? '是' : '-' }}</template></el-table-column>
          <el-table-column label="启用" width="70" align="center">
            <template #default="{ row }"><el-switch :model-value="row.enabled" size="small" @change="toggle(row)" /></template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" :loading="testing === row.id" @click="test(row)">发送测试</el-button>
              <el-button link type="primary" @click="openForm(row)">编辑</el-button>
              <el-button link type="danger" @click="remove(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </el-card>

  <el-dialog v-model="form.visible" :title="form.id ? '编辑渠道' : '新建渠道'" width="560px">
    <el-form label-width="96px">
      <el-form-item label="名称" required><el-input v-model="form.name" maxlength="100" /></el-form-item>
      <el-form-item label="类型" required>
        <el-radio-group v-model="form.type">
          <el-radio-button v-for="(label, v) in CHANNEL_TYPES" :key="v" :value="v">{{ label }}</el-radio-button>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="Webhook" required>
        <el-input v-model="form.url" :placeholder="URL_HINT[form.type]" />
      </el-form-item>
      <el-form-item v-if="form.type === 'feishu' || form.type === 'dingtalk'" label="加签密钥">
        <el-input v-model="form.secret" placeholder="机器人开启「签名校验 / 加签」时填写" show-password />
      </el-form-item>
      <el-form-item v-if="form.type === 'webhook'" label="说明">
        <span class="muted">以 POST JSON 发送：{ title, lines, link, run_id, status, total, passed, failed, skipped, duration }</span>
      </el-form-item>
      <el-form-item label="启用"><el-switch v-model="form.enabled" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="form.visible = false">取消</el-button>
      <el-button type="primary" @click="save">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api'
import { useProjectStore } from '../stores/project'
import { CHANNEL_TYPES, fmt } from '../utils'

const URL_HINT = {
  feishu: 'https://open.feishu.cn/open-apis/bot/v2/hook/xxxx',
  wecom: 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxx',
  dingtalk: 'https://oapi.dingtalk.com/robot/send?access_token=xxxx',
  webhook: 'https://your-service.example/hook',
}

const store = useProjectStore()
const tab = ref('logs')
const channels = ref([])
const logs = ref([])
const logTotal = ref(0)
const logPage = ref(1)
const logLoading = ref(false)
const logFilter = reactive({ channel_id: null, status: '' })
const testing = ref(null)

// 只露出域名和末尾 4 位，避免 token 被旁人看到
function maskUrl(url) {
  try {
    const u = new URL(url)
    const tail = url.slice(-4)
    return `${u.origin}/…${tail}`
  } catch {
    return url
  }
}

async function loadChannels() {
  channels.value = await api.listChannels()
}
async function loadLogs() {
  logLoading.value = true
  try {
    const r = await api.listNotifications({ project_id: store.currentId || undefined, page: logPage.value, page_size: 20,
      channel_id: logFilter.channel_id || undefined, status: logFilter.status || undefined })
    logs.value = r.items
    logTotal.value = r.total
  } finally {
    logLoading.value = false
  }
}
function reloadLogs() { logPage.value = 1; loadLogs() }

async function resend(row) {
  const n = await api.resendNotification(row.id)
  n.status === 'success' ? ElMessage.success('已重发') : ElMessage.error(`重发失败：${n.response}`)
  loadLogs()
}

const form = reactive({ visible: false, id: null, name: '', type: 'feishu', url: '', secret: '', enabled: true })
function openForm(row) {
  Object.assign(form, { visible: true, id: row?.id ?? null, name: row?.name || '', type: row?.type || 'feishu',
    url: row?.url || '', secret: row?.secret || '', enabled: row?.enabled ?? true })
}
async function save() {
  if (!form.name.trim() || !/^https?:\/\//.test(form.url)) return ElMessage.warning('请填写名称和以 http(s):// 开头的地址')
  const { visible, id, ...body } = form
  if (!['feishu', 'dingtalk'].includes(body.type)) body.secret = ''
  if (id) await api.updateChannel(id, body)
  else await api.createChannel(body)
  form.visible = false
  ElMessage.success('已保存')
  loadChannels()
}
async function toggle(row) {
  const { id, created_at, ...body } = row
  await api.updateChannel(id, { ...body, enabled: !row.enabled })
  loadChannels()
}
async function test(row) {
  testing.value = row.id
  try {
    const n = await api.testChannel(row.id)
    n.status === 'success' ? ElMessage.success('测试消息已发送') : ElMessage.error({ message: `发送失败：${n.response}`, duration: 8000, showClose: true })
    loadLogs()
  } finally {
    testing.value = null
  }
}
async function remove(row) {
  await ElMessageBox.confirm(`确定删除渠道「${row.name}」吗？引用它的定时任务将不再通知到该渠道。`, '删除确认', { type: 'warning' })
  await api.deleteChannel(row.id)
  loadChannels()
}

onMounted(() => { loadChannels(); loadLogs() })
</script>

<style scoped>
.detail { padding: 4px 48px; }
.detail .label { font-weight: 600; margin: 6px 0 2px; }
.detail pre { margin: 0; white-space: pre-wrap; word-break: break-all; font-family: "SF Mono", Menlo, monospace; font-size: 12px; background: #f5f7fa; padding: 8px; border-radius: 4px; }
</style>
