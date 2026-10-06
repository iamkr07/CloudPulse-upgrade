import { useEffect, useState } from 'react'
import { fetchResourceForecast } from '../services/api.js'

const STATUS_STYLES = {
  Normal: 'border-emerald-500/20 bg-emerald-500/10 text-emerald-400',
  Underutilized: 'border-amber-500/20 bg-amber-500/10 text-amber-400',
  Overutilized: 'border-rose-500/20 bg-rose-500/10 text-rose-400',
}

function ForecastTimeline({ resource, simulationData }) {
  const [forecast, setForecast] = useState(null)
  const [error, setError] = useState(null)
  const scale = simulationData?.id === resource?.id ? simulationData.cpu_scale ?? 1 : 1
  const isSimulated = scale !== 1

  useEffect(() => {
    if (!resource) return undefined
    let cancelled = false
    const timerId = setTimeout(() => {
      setForecast(null)
      setError(null)
      fetchResourceForecast(resource.id, scale)
        .then((result) => {
          if (!cancelled) setForecast(result.forecasts || [])
        })
        .catch((requestError) => {
          if (!cancelled) setError(requestError.message)
        })
    }, 0)
    return () => {
      cancelled = true
      clearTimeout(timerId)
    }
  }, [resource, scale])

  return (
    <section className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 shadow-sm shadow-slate-900/40">
      <div className="mb-3">
        <h2 className="text-sm font-semibold text-slate-100">CPU Forecast Timeline</h2>
        <p className="text-xs text-slate-400">{isSimulated ? `Forecast under current simulation (${Math.round(scale * 100)}% CPU)` : 'Passive forecast: what happens naturally over time'}</p>
      </div>
      {error ? <p className="text-xs text-rose-300">Forecast unavailable: {error}</p> : !forecast ? <p className="text-xs text-slate-400">Loading forecast...</p> : (
        <div className="grid grid-cols-3 gap-2">
          {forecast.map((item) => (
            <div key={item.minutes} className={`rounded-lg border p-3 text-center ${STATUS_STYLES[item.status] || 'border-slate-700 bg-slate-900 text-slate-300'}`}>
              <p className="text-[10px] uppercase tracking-wider opacity-70">+{item.minutes} min</p>
              <p className="mt-2 text-xs font-bold">{item.status}</p>
              <p className="mt-1 text-[11px]">{typeof item.confidence === 'number' ? `${item.confidence.toFixed(1)}%` : 'Confidence unavailable'}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

export default ForecastTimeline