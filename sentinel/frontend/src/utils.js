export function fmt(t) {
  if (!t) return '-'
  return t.replace('T', ' ').slice(0, 19)
}
