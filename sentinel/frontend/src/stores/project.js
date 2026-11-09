import { defineStore } from 'pinia'
import { api } from '../api'

const KEY = 'sentinel.currentProjectId'

export const useProjectStore = defineStore('project', {
  state: () => ({ projects: [], currentId: Number(localStorage.getItem(KEY)) || null }),
  getters: {
    current: (s) => s.projects.find((p) => p.id === s.currentId) || null,
  },
  actions: {
    async load() {
      this.projects = await api.listProjects()
      if (!this.projects.some((p) => p.id === this.currentId)) {
        this.select(this.projects[0]?.id ?? null)
      }
    },
    select(id) {
      this.currentId = id
      if (id) localStorage.setItem(KEY, id)
      else localStorage.removeItem(KEY)
    },
  },
})
