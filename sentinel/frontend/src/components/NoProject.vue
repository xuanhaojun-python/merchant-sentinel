<template>
  <el-empty description="还没有项目，请先到「项目管理」创建">
    <el-button type="primary" @click="$router.push('/projects')">去创建</el-button>
  </el-empty>
</template>
