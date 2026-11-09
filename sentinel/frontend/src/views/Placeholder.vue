<template>
  <el-card>
    <el-empty :description="`「${route.meta.title}」建设中，计划于第 ${route.meta.phase} 期上线`" />
  </el-card>
</template>

<script setup>
import { useRoute } from 'vue-router'
const route = useRoute()
</script>
