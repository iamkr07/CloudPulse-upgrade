import { EC2_DETAILS } from '../utils/ec2Utils.js'

const STATUS_STYLES = {
  Normal: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_8px_rgba(16,185,129,0.1)]',
  Underutilized: 'bg-amber-500/10 text-amber-400 border-amber-500/20 shadow-[0_0_8px_rgba(245,158,11,0.1)]',
  Overutilized: 'bg-rose-500/10 text-rose-400 border-rose-500/20 shadow-[0_0_8px_rgba(244,63,94,0.1)]',
}

function priorityStyle(priority) {
  if (priority === "High") return "text-red-400"
  if (priority === "Medium") return "text-yellow-400"
  return "text-green-400"
}

function getUtilizationColor(status) {
  if (status === 'Normal') return 'bg-emerald-500'
  if (status === 'Underutilized') return 'bg-amber-500'
  return 'bg-rose-500'
}

function getHealthDisplay(status) {
  if (status === 'Underutilized') return { label: 'Idle', color: 'text-slate-400 bg-slate-700/20' }
  if (status === 'Normal') return { label: 'Healthy', color: 'text-emerald-400 bg-emerald-700/20' }
  return { label: 'Critical', color: 'text-red-400 bg-red-700/20' }
}

function ResourceTable({ resources = [], isLoading, onSelectResource, selectedResource = null, simulationData = null }) {
  const underutilizedCount = resources.filter(r => r?.status === 'Underutilized').length
  const normalCount = resources.filter(r => r?.status === 'Normal').length
  const overutilizedCount = resources.filter(r => r?.status === 'Overutilized').length

  return (
    <section className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 shadow-sm shadow-slate-900/40">
      <div className="mb-4 flex items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-slate-100 sm:text-base">Resource Analytics</h2>
          <p className="text-xs text-slate-400">Click a row to view detailed analysis</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-500">Showing {resources.length} resources</p>
          <p className="text-xs text-slate-500">U: {underutilizedCount} | N: {normalCount} | O: {overutilizedCount}</p>
        </div>
      </div>
      <div className="overflow-x-auto overflow-y-auto max-h-[400px]">
        <table className="min-w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-xs uppercase tracking-wide text-slate-400">
              <th className="py-2 pr-4">ID</th>
              <th className="px-4 py-2">Utilization</th>
              <th className="px-4 py-2">Priority</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Instance</th>
              <th className="px-4 py-2">Confidence</th>
              <th className="px-4 py-2">Health</th>
              <th className="px-4 py-2">Cost</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-900">
            {isLoading ? (
              <tr>
                <td className="px-4 py-3 text-slate-300" colSpan={8}>
                  Loading...
                </td>
              </tr>
            ) : resources.length === 0 ? (
              <tr>
                <td className="px-4 py-3 text-slate-300" colSpan={8}>
                  No resources found.
                </td>
              </tr>
            ) : (
              resources.map((resource) => {
                const isSelected = selectedResource?.id === resource.id
                const isSimulated = simulationData && resource.id === simulationData.id
                const displayData = isSimulated ? simulationData : resource
                
                const health = getHealthDisplay(displayData.status)
                
                return (
                  <tr 
                    key={`${resource.id}-${resource.status}`}
                    onClick={() => onSelectResource?.(resource)}
                    className={`cursor-pointer group align-middle transition-all ${
                      isSelected
                        ? isSimulated
                          ? 'bg-sky-500/20 border-l-2 border-sky-400 shadow-lg'
                          : 'bg-sky-500/10 hover:bg-sky-500/15 border-l-2 border-sky-400'
                        : 'hover:bg-slate-900/60'
                    }`}
                  >
                    <td className={`py-3 pr-4 font-medium ${
                      isSelected ? 'text-sky-300' : 'text-slate-300 group-hover:text-slate-100'
                    }`}>
                      {resource.id}
                      {isSelected && <span className="ml-2 text-xs text-sky-400">✓</span>}
                      {isSimulated && <span className="ml-1.5 inline-block px-1.5 py-0.5 text-[9px] font-bold rounded-full bg-sky-500/30 text-sky-300 border border-sky-500/50">SIM</span>}
                    </td>
                    <td className={`px-4 py-3 text-xs font-mono ${
                      isSelected ? 'text-sky-300' : 'text-slate-400 group-hover:text-slate-200'
                    }`}>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-slate-800 rounded-full overflow-hidden">
                          <div 
                            className={`h-full transition-all ${getUtilizationColor(displayData.status)}`}
                            style={{ width: `${Math.min(displayData.utilization, 100)}%` }}
                          />
                        </div>
                        <span>{displayData?.utilization?.toFixed(1)}%</span>
                      </div>
                    </td>
                    <td className={`px-4 py-3 text-xs font-bold ${
                      isSelected ? 'text-sky-300' : ''
                    }`}>
                      <span className={priorityStyle(displayData.priority)}>
                        {displayData.priority}
                      </span>
                    </td>
                    <td className={`px-4 py-3 ${isSelected ? 'text-sky-300' : ''}`}>
                      <span className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase ${STATUS_STYLES[displayData.status] || ''}`}>
                        {displayData.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs">
                      {displayData?.ec2_instance && EC2_DETAILS[displayData.ec2_instance] ? (
                        <div className="group relative">
                          <span className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase ${EC2_DETAILS[displayData.ec2_instance].color}`}>
                            {displayData.ec2_instance}
                          </span>
                          <div className="hidden group-hover:block absolute bottom-full left-0 mb-2 w-48 bg-slate-800 border border-slate-700 rounded-lg p-2 shadow-lg z-10">
                            <p className="text-xs font-semibold text-slate-100">{EC2_DETAILS[displayData.ec2_instance].family}</p>
                            <p className="text-xs text-slate-400 mt-1">{EC2_DETAILS[displayData.ec2_instance].description}</p>
                            <p className="text-xs text-slate-500 mt-1">Use case: {EC2_DETAILS[displayData.ec2_instance].use_case}</p>
                          </div>
                        </div>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                    <td className={`px-4 py-3 text-xs font-semibold ${
                      isSelected ? 'text-sky-300' : 'text-cyan-400'
                    }`}>
                      {resource?.confidence?.toFixed(1) ?? '85.0'}%
                    </td>
                    <td className={`px-4 py-3 text-xs ${isSelected ? 'text-sky-300' : ''}`}>
                      <span className={`inline-block px-2 py-1 rounded border ${health.color}`}>
                        {health.label}
                      </span>
                    </td>
                    <td className={`px-4 py-3 text-xs font-mono ${
                      isSelected ? 'text-sky-300' : 'text-slate-400 group-hover:text-slate-200'
                    }`}>
                      ₹{displayData?.cost?.toFixed(2) ?? displayData?.estimated_cost?.toFixed(2) ?? '0.00'}/hr
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default ResourceTable

