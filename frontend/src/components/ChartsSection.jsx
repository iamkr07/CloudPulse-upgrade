import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from 'recharts'

function ChartsSection({ cpuData = [], statusData = [] }) {
  // Transform the current resources into a format suitable for the graphs
  const snapshotData = (cpuData || []).map(r => ({
    name: `Res ${r?.id || 'Unknown'}`,
    cpu: r?.cpu_usage ? Number(r.cpu_usage.toFixed(2)) : 0,
    status: r?.status || 'Unknown'
  }));

  // Safely handle statusData with null checks
  const safeStatusData = (statusData || []).map(entry => ({
    name: entry?.name || 'Unknown',
    value: entry?.value || 0,
    color: entry?.color || '#6b7280'
  }));

  return (
    <section className="grid gap-4 lg:grid-cols-2">
      {/* CPU Distribution */}
      <div className="flex flex-col rounded-xl border border-slate-800 bg-slate-950/70 p-4 shadow-sm shadow-slate-900/40">
        <div className="mb-4 flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-slate-100 sm:text-base">Resource CPU Distribution</h2>
          <p className="text-xs text-slate-400">Exact CPU usage across all monitored resources</p>
        </div>
        <div className="h-40" style={{ width: "100%" }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={snapshotData} margin={{ top: 12, right: 16, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
              <XAxis 
                dataKey="name" 
                stroke="#6b7280" 
                tickLine={false} 
                fontSize={10} 
                interval={0}
              />
              <YAxis
                stroke="#6b7280"
                tickLine={false}
                fontSize={11}
                width={32}
                domain={[0, 100]}
                tickFormatter={(v) => `${v}%`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#020617',
                  borderColor: '#1f2937',
                  borderRadius: 8,
                  fontSize: 12,
                }}
                labelStyle={{ color: '#e5e7eb', fontWeight: 500 }}
              />
              <Line
                type="monotone"
                dataKey="cpu"
                name="CPU Usage"
                stroke="#38bdf8"
                strokeWidth={2}
                dot={{ r: 4, strokeWidth: 2, fill: '#0f172a' }}
                activeDot={{ r: 6 }}
                isAnimationActive={true}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Status Distribution */}
      <div className="flex flex-col rounded-xl border border-slate-800 bg-slate-950/70 p-4 shadow-sm shadow-slate-900/40">
        <div className="mb-2 flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-slate-100 sm:text-base">Resource Status Distribution</h2>
          <p className="text-xs text-slate-400">Current resource statuses</p>
        </div>
        <div className="h-40" style={{ width: "100%" }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={safeStatusData} margin={{ top: 4, right: 16, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="name" stroke="#6b7280" tickLine={false} fontSize={11} />
              <YAxis stroke="#6b7280" tickLine={false} fontSize={11} width={40} allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#020617',
                  borderColor: '#1f2937',
                  borderRadius: 8,
                  fontSize: 12,
                }}
                labelStyle={{ color: '#e5e7eb', fontWeight: 500 }}
              />
              <Bar dataKey="value" fill="#22c55e" radius={[4, 4, 0, 0]}>
                {(safeStatusData || []).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  )
}

export default ChartsSection

