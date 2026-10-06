import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { EC2_DETAILS, getEC2Explanation } from '../utils/ec2Utils.js'
import { simulateResource } from '../services/api.js'

const STATUS_COLORS = {
  Underutilized: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20' },
  Normal: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20' },
  Overutilized: { bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/20' },
}

const PRIORITY_COLORS = { Low: 'text-green-400', Medium: 'text-yellow-400', High: 'text-red-400' }

export default function ResourceSimulationPanel({ resource, onClose, onSimulationChange }) {
  const [cpuScale, setCpuScale] = useState(1.0)
  const [simulated, setSimulated] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!resource) return undefined
    let cancelled = false
    const requestTimer = setTimeout(() => {
      setIsLoading(true)
      setError(null)
      onSimulationChange(null)
      simulateResource(resource.id, cpuScale)
        .then((result) => {
          if (cancelled) return
          if (result?.error) throw new Error(result.message || result.error)
          const nextSimulation = { ...result, ec2_explanation: getEC2Explanation(result.cpu_usage) }
          setSimulated(nextSimulation)
          onSimulationChange(nextSimulation)
        })
        .catch((requestError) => {
          if (cancelled) return
          setError(requestError.message)
          setSimulated(null)
          onSimulationChange(null)
        })
        .finally(() => {
          if (!cancelled) setIsLoading(false)
        })
    }, 0)
    return () => {
      cancelled = true
      clearTimeout(requestTimer)
    }
  }, [resource, cpuScale, onSimulationChange])

  if (!resource) return null

  if (!simulated) {
    if (isLoading) {
      return <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 text-sm text-slate-300">Running model simulation...</div>
    }
    if (error) {
      return <div className="rounded-xl border border-rose-500/30 bg-slate-900/50 p-4 text-sm text-rose-300">Simulation unavailable: {error}</div>
    }
    return <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 text-sm text-slate-300">Preparing simulation...</div>
  }

  const originalWorkloadType = resource.workload_type || 'Unknown'
  const statusColors = STATUS_COLORS[simulated.status] || STATUS_COLORS.Normal
  const originalStatusColors = STATUS_COLORS[resource.status] || STATUS_COLORS.Normal
  const chartData = [{ name: 'Utilization %', before: resource.utilization, after: simulated.utilization }]

  const handleReset = () => {
    setCpuScale(1.0)
  }

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-slate-800 bg-slate-900/50 p-4 shadow-sm shadow-slate-900/40">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h2 className="text-base font-semibold text-slate-100 tracking-[0.18em]">RESOURCE SIMULATION</h2>
          <p className="text-xs text-slate-400 mt-1">Resource ID: {resource.id}</p>
          {isLoading && <p className="text-xs text-sky-300 mt-1">Calculating updated CPU status...</p>}
          {error && <p className="text-xs text-rose-300 mt-1">Simulation update failed: {error}</p>}
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-200 transition-colors" aria-label="Close simulation">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2 flex flex-col gap-3">
          <div className="bg-slate-800/30 rounded-lg p-3">
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Current Metrics</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div><span className="text-slate-400">CPU</span><p className="text-slate-200 font-semibold">{resource.cpu_usage.toFixed(1)}%</p></div>
              <div><span className="text-slate-400">Peak CPU</span><p className="text-slate-200 font-semibold">{resource.max_cpu.toFixed(1)}%</p></div>
              <div><span className="text-slate-400">Utilization</span><p className="text-slate-200 font-semibold">{resource.utilization.toFixed(1)}%</p></div>
              <div><span className="text-slate-400">Priority</span><p className={`font-semibold ${PRIORITY_COLORS[resource.priority]}`}>{resource.priority}</p></div>
              <div className="col-span-2"><span className="text-slate-400">Current Instance</span><div className="flex items-center gap-2 mt-1">
                {resource?.ec2_instance && EC2_DETAILS[resource.ec2_instance] ? <span className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase ${EC2_DETAILS[resource.ec2_instance].color}`}>{resource.ec2_instance}</span> : <span className="text-slate-400 text-xs">-</span>}
              </div></div>
              <div className="col-span-2"><span className="text-slate-400">Status</span><div className="flex items-center gap-2 mt-1"><span className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase ${originalStatusColors.bg} ${originalStatusColors.text} ${originalStatusColors.border}`}>{resource.status}</span></div></div>
            </div>
          </div>

          <div className="bg-slate-800/30 rounded-lg p-3">
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Workload Type</h3>
            <p className="text-sm font-medium text-slate-100">{originalWorkloadType}</p>
            <p className="text-xs text-slate-400 mt-1">{originalWorkloadType === 'Idle' ? 'Low average CPU activity' : originalWorkloadType === 'Bursty' ? 'Large gap between average and peak CPU' : 'Comparatively consistent CPU activity'}</p>
          </div>

          <div className="bg-slate-800/30 rounded-lg p-3">
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Utilization Comparison</h3>
            <ResponsiveContainer width="100%" height={150}>
              <BarChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" /><XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 12 }} /><YAxis tick={{ fill: '#6b7280', fontSize: 12 }} domain={[0, 100]} />
                <Tooltip contentStyle={{ backgroundColor: '#020617', border: '1px solid #1f2937' }} labelStyle={{ color: '#e2e8f0' }} /><Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="before" fill="#60a5fa" name="Current" /><Bar dataKey="after" fill="#34d399" name="Simulated" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="flex flex-col gap-3">
          <div className="bg-slate-800/30 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2"><label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">CPU Scaling</label><span className="text-sm font-bold text-sky-400">{Math.round(cpuScale * 100)}%</span></div>
            <input type="range" min="0.2" max="3" step="0.1" value={cpuScale} onChange={(e) => setCpuScale(parseFloat(e.target.value))} className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-sky-500" aria-label="CPU scaling percentage from 20% to 300%" />
            <div className="mt-2 flex justify-between text-[10px] text-slate-500"><span>20%</span><span>100% baseline</span><span>300%</span></div>
            <p className="text-xs text-slate-400 mt-1">{cpuScale < 1 ? 'Reducing' : cpuScale > 1 ? 'Increasing' : 'No change'} CPU capacity</p>
          </div>
          <button onClick={handleReset} className="w-full px-3 py-2 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors text-slate-300 border border-slate-700">Reset Values</button>
        </div>
      </div>

      <div className="border-t border-slate-800 pt-3 mt-2">
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">Simulated Results</h3>
        <div className="grid gap-2">
          <div className="bg-slate-800/30 rounded-lg p-3"><div className="grid grid-cols-2 gap-2 text-xs">
            <div><span className="text-slate-400">New CPU</span><p className="text-slate-200 font-semibold">{simulated.cpu_usage.toFixed(1)}%</p></div>
            <div><span className="text-slate-400">New Peak CPU</span><p className="text-slate-200 font-semibold">{simulated.max_cpu.toFixed(1)}%</p></div>
            <div><span className="text-slate-400">New Utilization</span><p className="text-slate-200 font-semibold">{simulated.utilization.toFixed(1)}%</p></div>
            <div><span className="text-slate-400">New Priority</span><p className={`font-semibold ${PRIORITY_COLORS[simulated.priority]}`}>{simulated.priority}</p></div>
            <div className="col-span-2"><span className="text-slate-400">New Status</span><div className="flex items-center gap-2 mt-1"><span className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase ${statusColors.bg} ${statusColors.text} ${statusColors.border}`}>{simulated.status}</span></div></div>
          </div></div>

          <div className="bg-slate-800/30 rounded-lg p-3"><div className="flex items-center justify-between"><div><span className="text-slate-400 text-xs">Cost Impact</span><p className="text-xs text-slate-300 mt-1">₹{resource.estimated_cost.toFixed(2)}/hr -&gt; <span className="font-semibold text-slate-100">₹{simulated.cost.toFixed(2)}/hr</span></p></div><div className="text-right"><span className={`text-sm font-bold ${simulated.costChange < 0 ? 'text-emerald-400' : simulated.costChange > 0 ? 'text-rose-400' : 'text-slate-400'}`}>{simulated.costChange > 0 ? '+' : ''}{simulated.costChange.toFixed(2)} ₹</span></div></div></div>

          <div className={`rounded-lg p-3 border ${simulated.recommendation === 'Recommended Change' ? 'bg-emerald-500/5 border-emerald-500/20' : simulated.recommendation === 'Not Recommended' ? 'bg-rose-500/5 border-rose-500/20' : 'bg-slate-800/30 border-slate-700'}`}><p className={`text-xs font-semibold ${simulated.recommendationColor}`}>{simulated.recommendation}</p><p className="text-xs text-slate-300 mt-1">{simulated.recommendation === 'Recommended Change' ? `Scaling would improve resource efficiency by changing status from ${resource.status} to ${simulated.status}` : simulated.recommendation === 'Not Recommended' ? `Scaling would worsen resource efficiency by changing status from ${resource.status} to ${simulated.status}` : 'Scaling will not change the resource status'}</p></div>

          <div className="bg-slate-800/30 rounded-lg p-3"><div className="flex items-center justify-between"><div><span className="text-slate-400 text-xs">New Workload Type</span><p className="text-sm font-medium text-slate-100 mt-1">{simulated.workloadType}</p></div>{simulated.workloadType !== originalWorkloadType && <span className="text-xs text-amber-400 font-semibold">Changed</span>}</div></div>

          {simulated.ec2_instance && EC2_DETAILS[simulated.ec2_instance] && <div className={`rounded-lg p-3 border ${EC2_DETAILS[simulated.ec2_instance].color}`}><span className="text-slate-400 text-xs">Recommended Instance</span><p className="text-sm font-bold text-slate-100 mt-1">{simulated.ec2_instance}</p><p className="text-xs text-slate-300 mt-1">{EC2_DETAILS[simulated.ec2_instance].family}</p><p className="text-xs text-slate-300 mt-2"><strong>Why:</strong> {simulated.ec2_explanation}</p><div className="mt-2 text-xs"><span className="text-slate-500">CPU:</span><p className="font-semibold">{EC2_DETAILS[simulated.ec2_instance].cpu}</p></div><div className="mt-2 text-xs"><span className="text-slate-500">Use Case:</span><p className="font-semibold text-slate-100">{EC2_DETAILS[simulated.ec2_instance].use_case}</p></div></div>}
        </div>
      </div>
    </div>
  )
}
