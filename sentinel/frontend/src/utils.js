export function fmt(t) {
  if (!t) return '-'
  return t.replace('T', ' ').slice(0, 19)
}

// 用例优先级：markers 中有且仅有一个 p0/p1/p2 时返回它，否则视为未分级（与 utils/pytest_guards.py 的检查一致）
export const PRIORITIES = ['p0', 'p1', 'p2']
export const NO_PRIORITY = 'none'
export function priorityOf(c) {
  const found = PRIORITIES.filter((p) => (c.markers || []).includes(p))
  return found.length === 1 ? found[0] : NO_PRIORITY
}
