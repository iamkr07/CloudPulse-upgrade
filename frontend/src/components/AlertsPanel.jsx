function severityStyles(severity) {
  if (severity === 'critical') {
    return 'border-rose-500/60 bg-rose-500/5 text-rose-100'
  }
  if (severity === 'warning') {
    return 'border-amber-400/60 bg-amber-400/5 text-amber-50'
  }
  return 'border-sky-400/50 bg-sky-400/5 text-sky-50'
}

function iconAccent(severity) {
  if (severity === 'critical') {
    return 'bg-rose-500/15 text-rose-400'
  }
  if (severity === 'warning') {
    return 'bg-amber-400/10 text-amber-300'
  }
  return 'bg-sky-500/10 text-sky-400'
}

function AlertsPanel({ alerts }) {
  return (
    <section className="flex flex-col rounded-xl border border-slate-800 bg-slate-950/70 p-4 shadow-sm shadow-slate-900/40 h-full">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-slate-100 sm:text-base">Recommendations</h2>
        <span className="text-[11px] text-slate-400">Optimization actions</span>
      </div>
      <div className="space-y-3 overflow-y-auto pr-1 custom-scrollbar max-h-[500px]">
        {alerts.length === 0 ? (
          <div className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-[12px] text-slate-300">
            All resources are normal. Maintain current configuration.
          </div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`flex items-start gap-3 rounded-lg border px-3 py-2.5 text-xs ${severityStyles(alert.severity)}`}
            >
              <div
                className={`mt-0.5 flex h-7 w-7 items-center justify-center rounded-full text-[11px] font-semibold ${iconAccent(alert.severity)}`}
              >
                <span>!</span>
              </div>
              <div className="space-y-0.5">
                <p className="text-[12px] font-semibold leading-snug">{alert.title}</p>
                <p className="text-[11px] leading-snug text-slate-300">{alert.message}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  )
}

export default AlertsPanel

