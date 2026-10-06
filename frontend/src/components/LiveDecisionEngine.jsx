import { useEffect, useState } from 'react'
import { fetchResourceExplanation } from '../services/api.js'

function LiveDecisionEngine({ resources = [] }) {
  const [explanations, setExplanations] = useState({})

  useEffect(() => {
    let cancelled = false
    const timerId = setTimeout(() => {
      Promise.all(resources.slice(0, 3).map(async (resource) => {
        try {
          return [resource.id, await fetchResourceExplanation(resource.id)]
        } catch {
          return [resource.id, { error: 'Explanation unavailable' }]
        }
      })).then((entries) => {
        if (!cancelled) setExplanations(Object.fromEntries(entries))
      })
    }, 0)
    return () => {
      cancelled = true
      clearTimeout(timerId)
    }
  }, [resources])

  if (!resources || resources.length === 0) {
    return (
      <section className="rounded-3xl border border-slate-800 bg-slate-950/80 p-5 shadow-sm shadow-slate-900/40">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-100">Live Decision Engine</h2>
            <p className="mt-1 text-sm text-slate-400">Top 3 resources showing input, process, and output.</p>
          </div>
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="col-span-full rounded-2xl border border-slate-800 bg-slate-900/80 p-4 text-sm text-slate-300">
            Waiting for resource data to populate the live decision engine.
          </div>
        </div>
      </section>
    )
  }

  const topResources = resources.slice(0, 3)

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-950/80 p-5 shadow-sm shadow-slate-900/40">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">Live Decision Engine</h2>
          <p className="mt-1 text-sm text-slate-400">Top 3 resources showing input, process, and output.</p>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {topResources.map((resource) => (
          <div key={resource?.id ?? 'unknown'} className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
            <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Resource ID: {resource?.id ?? 'Unknown'}</p>
            <div className="mt-3 space-y-3 text-sm text-slate-300">
              <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-3">
                <p className="text-[11px] uppercase tracking-[0.25em] text-slate-500">INPUT</p>
                <p className="mt-2 font-medium text-slate-100">CPU: {(resource?.cpu_usage ?? 0).toFixed(2)}%</p>
                <p className="text-slate-400">Peak CPU: {(resource?.max_cpu ?? 0).toFixed(2)}%</p>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-3">
                <p className="text-[11px] uppercase tracking-[0.25em] text-slate-500">PROCESS</p>
                <p className="mt-2 font-medium text-slate-100">Utilization Score = {(resource?.utilization ?? 0).toFixed(2)}%</p>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-3">
                <p className="text-[11px] uppercase tracking-[0.25em] text-slate-500">OUTPUT</p>
                <p className="mt-2 font-medium text-slate-100">Status: {resource?.status ?? 'Unknown'}</p>
                <p className="text-slate-400">Priority: {resource?.priority ?? 'N/A'}</p>
                <p className="mt-2 text-slate-400">Top model contributions</p>
                {explanations[resource.id]?.error ? (
                  <p className="text-xs text-rose-300">{explanations[resource.id].error}</p>
                ) : Array.isArray(explanations[resource.id]?.features) ? (
                  explanations[resource.id].features
                    .slice()
                    .sort((left, right) => Math.abs(right.shap_value) - Math.abs(left.shap_value))
                    .slice(0, 3)
                    .map((feature) => (
                      <p key={feature.name} className="text-xs text-slate-300">
                        {feature.name}: {feature.shap_value >= 0 ? 'toward' : 'away from'} {explanations[resource.id].predicted_class} ({feature.shap_value.toFixed(4)})
                      </p>
                    ))
                ) : (
                  <p className="text-xs text-slate-500">Loading explanation...</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

export default LiveDecisionEngine
