function HowItWorksPanel() {
  const steps = [
    {
      title: 'STEP 1',
      description: 'Data is taken from the Azure Public Dataset V2 CPU trace',
    },
    {
      title: 'STEP 2',
      description: 'Average, minimum, and maximum CPU extracted from five-minute trace readings',
    },
    {
      title: 'STEP 3',
      description: 'Utilization is the average CPU percentage',
    },
    {
      title: 'STEP 4',
      description: 'Classification: 0–30 → Underutilized; 30–70 → Normal; 70–100 → Overutilized',
    },
    {
      title: 'STEP 5',
      description: 'Priority Assignment: Low / Medium / High',
    },
    {
      title: 'STEP 6',
      description: 'Recommendation Engine suggests optimal instance type',
    },
  ]

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-950/80 p-5 shadow-sm shadow-slate-900/40">
      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">How the System Works</h2>
          <p className="mt-1 text-sm text-slate-400">A complete, explainable cloud decision support workflow.</p>
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {steps.map((step) => (
          <article key={step.title} className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-sky-400">{step.title}</p>
            <p className="mt-3 text-sm leading-relaxed text-slate-200">{step.description}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

export default HowItWorksPanel
