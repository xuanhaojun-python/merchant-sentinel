<template>
  <el-empty v-if="!store.currentId" description="请先创建项目" />
  <el-card v-else><RunTable :suite-id="Number(route.query.suite) || undefined" /></el-card>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { useProjectStore } from '../stores/project'
import RunTable from '../components/RunTable.vue'
const store = useProjectStore()
const route = useRoute()
</script>
