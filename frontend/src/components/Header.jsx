function Header({ timeLeft, isRefreshing, isPaused, setIsPaused, loadResources, lastUpdated }) {
  const progress = ((20 - timeLeft) / 20) * 100

  return (
    <header className="flex flex-col gap-4 border-b border-slate-800 pb-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-50 sm:text-2xl">
            Cloud Resource Dashboard
          </h1>
          <div className="mt-1 flex items-center gap-2">
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-400">
              Cloud Resource Monitoring &amp; Optimization
            </p>
            <span className="text-[10px] text-slate-600">|</span>
            <p className="text-[10px] text-slate-500">
              Last sync: {lastUpdated.toLocaleTimeString()}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-900/50 p-1">
            <button
              onClick={() => setIsPaused(!isPaused)}
              className={`rounded px-2 py-1 text-[10px] font-bold uppercase transition-colors ${
                isPaused 
                  ? 'bg-amber-500/20 text-amber-400 hover:bg-amber-500/30' 
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
              }`}
              title={isPaused ? "Resume auto-refresh" : "Pause auto-refresh"}
            >
              {isPaused ? 'Paused' : 'Live'}
            </button>
            <button
              onClick={() => loadResources()}
              disabled={isRefreshing}
              className="rounded bg-slate-800 px-2 py-1 text-[10px] font-bold uppercase text-slate-400 transition-colors hover:bg-slate-700 hover:text-slate-200 disabled:opacity-50"
              title="Refresh data now"
            >
              Sync
            </button>
          </div>

          <div className="hidden items-center gap-2 rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs text-slate-300 sm:flex">
            <span className={`inline-flex h-2 w-2 rounded-full bg-emerald-400 ${isRefreshing ? 'animate-ping' : 'animate-pulse'}`} />
            <span>{isRefreshing ? 'Syncing...' : 'System Active'}</span>
          </div>
        </div>
      </div>
      
      <div className="relative h-1 w-full overflow-hidden rounded-full bg-slate-900">
        <div 
          className={`absolute inset-y-0 left-0 bg-emerald-500 transition-all duration-1000 ease-linear ${isPaused ? 'opacity-50' : 'opacity-100'}`}
          style={{ width: `${isPaused ? 0 : progress}%` }}
        />
      </div>
    </header>
  )
}

export default Header

