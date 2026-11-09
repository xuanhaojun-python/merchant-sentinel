<template>
  <el-empty v-if="!store.currentId" description="请先创建项目" />
  <el-card v-else><RunTable /></el-card>
</template>

<script setup>
import { useProjectStore } from '../stores/project'
import RunTable from '../components/RunTable.vue'
const store = useProjectStore()
</script>
