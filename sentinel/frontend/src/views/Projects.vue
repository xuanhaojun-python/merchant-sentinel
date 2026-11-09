<template>
  <el-card>
    <div class="toolbar">
      <el-button type="primary" icon="Plus" @click="openProject()">新建项目</el-button>
      <div class="spacer" />
      <el-button icon="Refresh" @click="store.load()">刷新</el-button>
    </div>
    <el-table :data="store.projects" border>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="项目名称" min-width="160">
        <template #default="{ row }">
          {{ row.name }}
          <el-tag v-if="row.id === store.currentId" size="small" style="margin-left: 6px">当前</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="root_path" label="工程目录" min-width="300">
        <template #default="{ row }"><span class="mono">{{ row.root_path }}</span></template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip />
      <el-table-column prop="case_count" label="用例数" width="80" align="center" />
      <el-table-column prop="env_count" label="环境数" width="80" align="center" />
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="store.select(row.id)">设为当前</el-button>
          <el-button link type="primary" @click="openEnvs(row)">环境配置</el-button>
          <el-button link type="primary" @click="openProject(row)">编辑</el-button>
          <el-button link type="danger" @click="removeProject(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <!-- 项目表单 -->
  <el-dialog v-model="projectDialog.visible" :title="projectDialog.form.id ? '编辑项目' : '新建项目'" width="560px">
    <el-form ref="projectFormRef" :model="projectDialog.form" :rules="projectRules" label-width="90px">
      <el-form-item label="项目名称" prop="name"><el-input v-model="projectDialog.form.name" /></el-form-item>
      <el-form-item label="工程目录" prop="root_path">
        <el-input v-model="projectDialog.form.root_path" placeholder="pytest 工程的绝对路径，如 /Users/me/merchant-sentinel" />
      </el-form-item>
      <el-form-item label="描述"><el-input v-model="projectDialog.form.description" type="textarea" :rows="2" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="projectDialog.visible = false">取消</el-button>
      <el-button type="primary" :loading="projectDialog.saving" @click="saveProject">保存</el-button>
    </template>
  </el-dialog>

  <!-- 环境配置 -->
  <el-drawer v-model="envDrawer.visible" :title="`环境配置 · ${envDrawer.project?.name || ''}`" size="760px">
    <div class="toolbar"><el-button type="primary" icon="Plus" @click="openEnv()">新建环境</el-button></div>
    <el-table :data="envDrawer.envs" border>
      <el-table-column prop="name" label="名称" width="100">
        <template #default="{ row }">
          {{ row.name }}<el-tag v-if="row.is_default" size="small" type="success" style="margin-left: 4px">默认</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="base_url" label="Base URL" min-width="200" show-overflow-tooltip />
      <el-table-column prop="email" label="账号" min-width="160" show-overflow-tooltip />
      <el-table-column label="密码" width="80"><template #default="{ row }">{{ row.password ? '已配置' : '-' }}</template></el-table-column>
      <el-table-column label="无头" width="60"><template #default="{ row }">{{ row.headless ? '是' : '否' }}</template></el-table-column>
      <el-table-column label="操作" width="110">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEnv(row)">编辑</el-button>
          <el-button link type="danger" @click="removeEnv(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-drawer>

  <el-dialog v-model="envDialog.visible" :title="envDialog.form.id ? '编辑环境' : '新建环境'" width="520px" append-to-body>
    <el-form ref="envFormRef" :model="envDialog.form" :rules="envRules" label-width="90px">
      <el-form-item label="名称" prop="name"><el-input v-model="envDialog.form.name" placeholder="如 SIT / UAT" /></el-form-item>
      <el-form-item label="Base URL" prop="base_url"><el-input v-model="envDialog.form.base_url" placeholder="https://..." /></el-form-item>
      <el-form-item label="登录账号"><el-input v-model="envDialog.form.email" /></el-form-item>
      <el-form-item label="登录密码"><el-input v-model="envDialog.form.password" type="password" show-password /></el-form-item>
      <el-form-item label="无头模式"><el-switch v-model="envDialog.form.headless" /></el-form-item>
      <el-form-item label="默认环境"><el-switch v-model="envDialog.form.is_default" /></el-form-item>
      <el-alert type="info" :closable="false" show-icon
        title="执行时通过 MS_BASE_URL / MS_EMAIL / MS_PASSWORD / MS_HEADLESS 环境变量注入；账号留空则使用工程自身配置。" />
    </el-form>
    <template #footer>
      <el-button @click="envDialog.visible = false">取消</el-button>
      <el-button type="primary" :loading="envDialog.saving" @click="saveEnv">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api'
import { useProjectStore } from '../stores/project'

const store = useProjectStore()

// ── 项目 ──
const projectFormRef = ref()
const projectDialog = reactive({ visible: false, saving: false, form: {} })
const projectRules = {
  name: [{ required: true, message: '请输入项目名称' }],
  root_path: [{ required: true, message: '请输入工程目录' }],
}

function openProject(row) {
  projectDialog.form = row ? { ...row } : { name: '', root_path: '', description: '' }
  projectDialog.visible = true
}

async function saveProject() {
  await projectFormRef.value.validate()
  projectDialog.saving = true
  try {
    const { id, name, root_path, description } = projectDialog.form
    const saved = id ? await api.updateProject(id, { name, root_path, description })
      : await api.createProject({ name, root_path, description })
    ElMessage.success('已保存')
    projectDialog.visible = false
    await store.load()
    if (!id) store.select(saved.id)
  } finally {
    projectDialog.saving = false
  }
}

async function removeProject(row) {
  await ElMessageBox.confirm(`删除项目「${row.name}」将同时删除其环境、用例和全部执行记录，确定吗？`, '删除确认', { type: 'warning' })
  await api.deleteProject(row.id)
  ElMessage.success('已删除')
  await store.load()
}

// ── 环境 ──
const envFormRef = ref()
const envDrawer = reactive({ visible: false, project: null, envs: [] })
const envDialog = reactive({ visible: false, saving: false, form: {} })
const envRules = {
  name: [{ required: true, message: '请输入名称' }],
  base_url: [{ required: true, message: '请输入 Base URL' }],
}

async function loadEnvs() {
  envDrawer.envs = await api.listEnvs(envDrawer.project.id)
}

async function openEnvs(project) {
  envDrawer.project = project
  envDrawer.visible = true
  await loadEnvs()
}

function openEnv(row) {
  envDialog.form = row ? { ...row } : { name: '', base_url: '', email: '', password: '', headless: true, is_default: false }
  envDialog.visible = true
}

async function saveEnv() {
  await envFormRef.value.validate()
  envDialog.saving = true
  try {
    const { id, project_id, ...body } = envDialog.form
    if (id) await api.updateEnv(id, body)
    else await api.createEnv(envDrawer.project.id, body)
    ElMessage.success('已保存')
    envDialog.visible = false
    await Promise.all([loadEnvs(), store.load()])
  } finally {
    envDialog.saving = false
  }
}

async function removeEnv(row) {
  await ElMessageBox.confirm(`确定删除环境「${row.name}」吗？`, '删除确认', { type: 'warning' })
  await api.deleteEnv(row.id)
  await Promise.all([loadEnvs(), store.load()])
}
</script>
