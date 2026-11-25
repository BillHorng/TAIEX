import type { HistoryData, RunSummary } from '../types/market'

export async function loadMarket(): Promise<RunSummary> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/latest.json`, { cache: 'no-store' })
  if (!response.ok) throw new Error(`資料讀取失敗 (${response.status})`)
  return response.json() as Promise<RunSummary>
}

export async function loadHistory(): Promise<HistoryData> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/history.json`, { cache: 'no-store' })
  if (!response.ok) return { updated_at: null, records: [] }
  return response.json() as Promise<HistoryData>
}
