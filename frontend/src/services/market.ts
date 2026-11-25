import type { RunSummary } from '../types/market'

export async function loadMarket(): Promise<RunSummary> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/latest.json`, { cache: 'no-store' })
  if (!response.ok) throw new Error(`資料讀取失敗 (${response.status})`)
  return response.json() as Promise<RunSummary>
}
