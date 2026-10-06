import { useMemo } from 'react'

function SummaryCards({ summary }) {
  const items = useMemo(
    () => [
      {
        id: 'total-resources',
        label: 'Total Active Resources',
        value: summary.totalActiveResources,
        accent: 'bg-sky-500/10 text-sky-400 ring-sky-500/40',
        iconBg: 'bg-sky-500/10 text-sky-400',
        iconLabel: 'R',
      },
      {
        id: 'normal-resources',
        label: 'Normal Resources',
        value: summary.normalResources,
        accent: 'bg-emerald-500/10 text-emerald-400 ring-emerald-500/40',
        iconBg: 'bg-emerald-500/10 text-emerald-400',
        iconLabel: 'N',
      },
      {
        id: 'underutilized',
        label: 'Underutilized Resources',
        value: summary.underutilizedResources,
        accent: 'bg-amber-500/10 text-amber-400 ring-amber-500/40',
        iconBg: 'bg-amber-500/10 text-amber-400',
        iconLabel: 'U',
      },
      {
        id: 'overutilized',
        label: 'Overutilized Resources',
        value: summary.overutilizedResources,
        accent: 'bg-rose-500/10 text-rose-400 ring-rose-500/40',
        iconBg: 'bg-rose-500/10 text-rose-400',
        iconLabel: 'O',
      },
    ],
    [summary],
  )

  return (
    <section aria-label="Summary metrics" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <div
          key={item.id}
          className="flex items-center justify-between gap-4 rounded-xl border border-slate-800 bg-gradient-to-b from-slate-900/60 to-slate-950/80 px-4 py-3 shadow-sm shadow-slate-900/40"
        >
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-400">
              {item.label}
            </p>
            <p className="mt-2 text-lg font-semibold text-slate-50 sm:text-xl">{item.value}</p>
          </div>
          <div
            className={`flex h-10 w-10 items-center justify-center rounded-full text-sm font-semibold ${item.iconBg}`}
          >
            <span>{item.iconLabel}</span>
          </div>
        </div>
      ))}
    </section>
  )
}

export default SummaryCards

