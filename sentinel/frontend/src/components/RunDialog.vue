<template>
  <el-dialog v-model="visible" :title="title" width="480px">
    <el-form label-width="80px">
      <el-form-item v-if="label" label="执行对象">{{ label }}</el-form-item>
      <el-form-item v-if="count !== null" label="用例数">{{ count }} 条</el-form-item>
      <el-form-item label="执行环境">
        <el-select v-model="envId" placeholder="不指定则使用工程自身配置" clearable style="width: 100%">
          <el-option v-for="e in envs" :key="e.id" :label="`${e.name}  (${e.base_url})`" :value="e.id" />
        </el-select>
      </el-form-item>
      <el-alert v-if="fundEnv" type="error" :closable="false" show-icon
        title="该环境允许执行 fund 真实资金用例，请确认后再执行" />
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" :disabled="count === 0" @click="submit">开始执行</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const props = defineProps({ projectId: Number })
const router = useRouter()
const visible = ref(false)
const submitting = ref(false)
const envs = ref([])
const envId = ref(null)
const title = ref('执行用例')
const label = ref('')
const count = ref(null)
let runner = null

const fundEnv = computed(() => envs.value.find((e) => e.id === envId.value)?.allow_fund)

/**
 * open(nodeids)：执行指定用例
 * open(null, { title, label, count, run: (envId) => Promise<Run> })：自定义执行（套件 / 脚本）
 */
async function open(ids, opts = {}) {
  title.value = opts.title || '执行用例'
  label.value = opts.label || ''
  count.value = ids ? ids.length : opts.count ?? null
  runner = opts.run || ((env) => api.createRun({ project_id: props.projectId, environment_id: env, nodeids: ids }))
  envs.value = await api.listEnvs(props.projectId)
  envId.value = envs.value.find((e) => e.is_default)?.id ?? null
  visible.value = true
}

async function submit() {
  submitting.value = true
  try {
    const run = await runner(envId.value)
    visible.value = false
    router.push(`/runs/${run.id}`)
  } finally {
    submitting.value = false
  }
}

defineExpose({ open })
</script>
