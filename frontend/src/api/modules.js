import { api } from './client'

export async function fetchModules(tenant) {
  const res = await api.get(`/t/${tenant}/api/v1/modules`)
  return res.data
}