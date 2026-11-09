<template>
  <el-container class="layout">
    <el-aside width="208px" class="aside">
      <div class="logo">🛡️ Web3Rec</div>
      <el-menu :default-active="activeMenu" router class="menu">
        <el-menu-item v-for="m in menus" :key="m.path" :index="m.path">
          <el-icon><component :is="m.icon" /></el-icon>
          <span>{{ m.title }}</span>
          <el-tag v-if="m.phase" size="small" type="info" effect="plain" class="soon">建设中</el-tag>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span class="title">{{ route.meta.title }}</span>
        <div class="spacer" />
        <span class="muted">当前项目</span>
        <el-select v-model="currentId" placeholder="请先创建项目" style="width: 220px" @change="store.select">
          <el-option v-for="p in store.projects" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
      </el-header>
      <el-main class="main">
        <router-view :key="`${route.fullPath}-${store.currentId}`" />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { menus } from '../router'
import { useProjectStore } from '../stores/project'

const route = useRoute()
const store = useProjectStore()
const currentId = computed({ get: () => store.currentId, set: (v) => store.select(v) })
const activeMenu = computed(() => route.meta.parent || route.path)

onMounted(() => store.load())
</script>

<style scoped>
.layout { height: 100%; }
.aside { background: #1f2d3d; overflow-y: auto; }
.logo { height: 56px; line-height: 56px; color: #fff; font-weight: 600; font-size: 16px; padding-left: 20px; }
.menu { border-right: none; --el-menu-bg-color: #1f2d3d; --el-menu-text-color: #bfcbd9; --el-menu-active-color: #409eff; --el-menu-hover-bg-color: #263445; }
.soon { margin-left: auto; transform: scale(0.85); }
.header { display: flex; align-items: center; gap: 10px; background: #fff; border-bottom: 1px solid #e4e7ed; }
.header .title { font-size: 16px; font-weight: 600; }
.spacer { flex: 1; }
.main { padding: 20px; }
</style>
