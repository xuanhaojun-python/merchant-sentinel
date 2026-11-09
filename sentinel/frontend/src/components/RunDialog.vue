<template>
  <el-dialog v-model="visible" title="执行用例" width="480px">
    <el-form label-width="80px">
      <el-form-item label="用例数">{{ nodeids.length }} 条</el-form-item>
      <el-form-item label="执行环境">
        <el-select v-model="envId" placeholder="不指定则使用工程自身配置" clearable style="width: 100%">
          <el-option v-for="e in envs" :key="e.id" :label="`${e.name}  (${e.base_url})`" :value="e.id" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">开始执行</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const props = defineProps({ projectId: Number })
const router = useRouter()
const visible = ref(false)
const submitting = ref(false)
const nodeids = ref([])
const envs = ref([])
const envId = ref(null)

async function open(ids) {
  nodeids.value = ids
  envs.value = await api.listEnvs(props.projectId)
  envId.value = envs.value.find((e) => e.is_default)?.id ?? null
  visible.value = true
}

async function submit() {
  submitting.value = true
  try {
    const run = await api.createRun({ project_id: props.projectId, environment_id: envId.value, nodeids: nodeids.value })
    visible.value = false
    router.push(`/runs/${run.id}`)
  } finally {
    submitting.value = false
  }
}

defineExpose({ open })
</script>
