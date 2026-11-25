import { useEffect, useMemo, useState } from 'react'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { loadMarket } from './services/market'
import type { MarketRecord, RunSummary } from './types/market'

const money = new Intl.NumberFormat('zh-TW', { maximumFractionDigits: 2 })
const compact = new Intl.NumberFormat('zh-TW', { notation: 'compact', maximumFractionDigits: 1 })

function direction(row: MarketRecord) {
  return row.change_direction === 'UP' ? 'up' : row.change_direction === 'DOWN' ? 'down' : 'flat'
}

function MarketCard({ row, selected, onClick }: { row: MarketRecord; selected: boolean; onClick: () => void }) {
  const tone = direction(row)
  return <button className={`market-card ${selected ? 'selected' : ''}`} onClick={onClick}>
    <div className="card-top"><span className="symbol">{row.symbol}</span><span className={`status ${row.data_status.toLowerCase()}`}>{row.data_status}</span></div>
    <div className="name">{row.symbol_name}</div>
    <div className="quote-row">
      <strong>{row.last_price == null ? '—' : money.format(row.last_price)}</strong>
      <span className={tone}>{row.change_value == null ? '—' : `${row.change_value > 0 ? '+' : ''}${money.format(row.change_value)} (${row.change_percent?.toFixed(2)}%)`}</span>
    </div>
    <div className="range"><span>低 {row.low ?? '—'}</span><i><b style={{ width: row.low && row.high && row.last_price ? `${Math.max(3, Math.min(100, (row.last_price - row.low) / (row.high - row.low || 1) * 100))}%` : '0%' }} /></i><span>高 {row.high ?? '—'}</span></div>
  </button>
}

export function App() {
  const [data, setData] = useState<RunSummary | null>(null)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState('TAIEX')
  useEffect(() => { loadMarket().then(setData).catch((e: Error) => setError(e.message)) }, [])
  const current = data?.records.find((r) => r.symbol === selected) ?? data?.records[0]
  const chart = useMemo(() => current ? [
    { label: '開盤', value: current.open }, { label: '低點', value: current.low },
    { label: '高點', value: current.high }, { label: '最新', value: current.last_price },
  ].filter((point) => point.value != null) : [], [current])
  const updated = data ? new Intl.DateTimeFormat('zh-TW', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Taipei' }).format(new Date(data.generated_at)) : ''

  return <main>
    <header>
      <div className="brand-mark"><span>TW</span></div>
      <div className="brand"><p>TAIWAN MARKET</p><h1>市場脈動</h1></div>
      <div className="header-meta"><span className="live-dot" />{data?.calendar_status === 'TRADING_DAY' ? '交易日' : '非交易時段'}<small>{updated || '載入中'}</small></div>
    </header>

    <section className="hero">
      <div><p className="eyebrow">MARKET OVERVIEW · 台北時間</p><h2>掌握市場，<em>看見趨勢。</em></h2><p className="sub">追蹤台灣加權指數與核心 ETF，資料經驗證後由自動化管線發布。</p></div>
      <div className="run-state"><span>PIPELINE</span><strong>{data?.pipeline_status ?? 'LOADING'}</strong><small>{data?.scheduled_time ?? '—'} 批次</small></div>
    </section>

    {error && <div className="alert">{error}</div>}
    <section className="cards">{data?.records.map((row) => <MarketCard key={row.symbol} row={row} selected={current?.symbol === row.symbol} onClick={() => setSelected(row.symbol)} />)}</section>

    <section className="panel chart-panel">
      <div className="panel-title"><div><p>SESSION RANGE</p><h3>{current?.symbol_name ?? '市場走勢'}</h3></div><span>{current?.data_source ?? 'TWSE OpenAPI'}</span></div>
      <div className="chart-wrap">
        {chart.length ? <ResponsiveContainer width="100%" height="100%"><AreaChart data={chart} margin={{ top: 12, right: 10, left: 4, bottom: 0 }}>
          <defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#f3c969" stopOpacity={.42}/><stop offset="100%" stopColor="#f3c969" stopOpacity={0}/></linearGradient></defs>
          <CartesianGrid vertical={false} stroke="#ffffff12"/><XAxis dataKey="label" tickLine={false} axisLine={false} stroke="#93a49d"/><YAxis domain={['dataMin - 1', 'dataMax + 1']} tickLine={false} axisLine={false} stroke="#93a49d" width={66}/><Tooltip contentStyle={{ background: '#10221d', border: '1px solid #ffffff20', borderRadius: 12 }}/><Area type="monotone" dataKey="value" stroke="#f3c969" strokeWidth={3} fill="url(#fill)"/></AreaChart></ResponsiveContainer> : <div className="empty">目前沒有可繪製的價量資料</div>}
      </div>
    </section>

    <section className="details">
      <div className="panel metrics"><div className="panel-title"><div><p>MARKET DETAILS</p><h3>交易摘要</h3></div></div>
        <dl><div><dt>成交量</dt><dd>{current?.volume == null ? '—' : compact.format(current.volume)}</dd></div><div><dt>成交金額</dt><dd>{current?.turnover == null ? '—' : compact.format(current.turnover)}</dd></div><div><dt>前收</dt><dd>{current?.previous_close ?? '—'}</dd></div><div><dt>資料狀態</dt><dd>{current?.data_status ?? '—'}</dd></div></dl>
      </div>
      <div className="panel provenance"><div className="panel-title"><div><p>DATA INTEGRITY</p><h3>資料可信度</h3></div></div>
        <ul><li><span>交易日判定</span><b>{data?.calendar_status ?? '—'}</b></li><li><span>來源</span><b>{data?.sources.join(', ') || '—'}</b></li><li><span>警告</span><b>{data?.warnings.length ?? 0}</b></li></ul>
      </div>
    </section>
    <footer><span>TWSE public data · 僅供資訊參考，不構成投資建議</span><span>Asia/Taipei</span></footer>
  </main>
}
