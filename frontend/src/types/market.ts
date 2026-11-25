export type MarketRecord = {
  record_id: string
  symbol: string
  symbol_name: string
  market: string
  trading_date: string
  scheduled_time: string
  market_data_time: string | null
  retrieved_at: string
  open: number | null
  high: number | null
  low: number | null
  last_price: number | null
  previous_close: number | null
  change_value: number | null
  change_percent: number | null
  volume: number | null
  turnover: number | null
  change_direction: 'UP' | 'DOWN' | 'FLAT' | 'UNKNOWN'
  data_source: string
  data_status: string
}

export type RunSummary = {
  run_id: string
  generated_at: string
  trading_date: string
  scheduled_time: string
  timezone: string
  calendar_status: string
  calendar_note: string
  pipeline_status: string
  records: MarketRecord[]
  warnings: string[]
  sources: string[]
}
