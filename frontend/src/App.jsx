import { useEffect, useMemo, useState } from 'react'
import Header from './components/Header.jsx'
import HowItWorksPanel from './components/HowItWorksPanel.jsx'
import LiveDecisionEngine from './components/LiveDecisionEngine.jsx'
import SummaryCards from './components/SummaryCards.jsx'
import ResourceTable from './components/ResourceTable.jsx'
import ChartsSection from './components/ChartsSection.jsx'
import AlertsPanel from './components/AlertsPanel.jsx'
import StandardsPanel from './components/StandardsPanel.jsx'
import ResourceSimulationPanel from './components/ResourceSimulationPanel.jsx'
import ForecastTimeline from './components/ForecastTimeline.jsx'
import { fetchResources } from './services/api.js'

const STATUS_SEVERITY = {
  Overutilized: 'critical',
  Underutilized: 'warning',
  Normal: 'info',
}

function App() {
  const [resources, setResources] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [timeLeft, setTimeLeft] = useState(20)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(new Date())
  const [selectedResource, setSelectedResource] = useState(null)
  const [simulationData, setSimulationData] = useState(null)

  async function loadResources() {
    if (isRefreshing) return
    setIsRefreshing(true)
    try {
      const newResources = await fetchResources()
      console.log("API RESPONSE:", newResources);
      setTimeout(() => {
        setResources(newResources)
        setLastUpdated(new Date())
        setIsLoading(false)
        setIsRefreshing(false)
        setTimeLeft(20)
      }, 400)
    } catch (error) {
      console.error('Failed to load resources from backend', error)
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    loadResources()

    const timerId = setInterval(() => {
      if (isPaused) return // Skip decrementing if paused

      setTimeLeft((prev) => {
        if (prev <= 1) {
          loadResources()
          return 20
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timerId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isPaused]) // Re-run effect if pause state changes

  const summary = useMemo(() => {
    const totalActiveResources = resources.length
    const normalResources = resources.filter((r) => r.status === 'Normal').length
    const underutilizedResources = resources.filter((r) => r.status === 'Underutilized').length
    const overutilizedResources = resources.filter((r) => r.status === 'Overutilized').length
    const activeAlerts = resources.filter((r) => r.status !== 'Normal').length
    return {
      totalActiveResources,
      normalResources,
      underutilizedResources,
      overutilizedResources,
      activeAlerts,
    }
  }, [resources])

  const alerts = useMemo(() => {
    return resources
      .map((resource, idx) => ({
        id: `${resource.id}-${idx}`,
        title: 
          resource.status === 'Overutilized' ? 'Scale up' :
          resource.status === 'Underutilized' ? 'Reduce resources' :
          'Maintain',
        message:
          resource.status === 'Overutilized'
            ? `Overutilized resource ${resource.id}. Scale up to handle load.`
            : resource.status === 'Underutilized'
            ? `Underutilized resource ${resource.id}. Reduce resources to save costs.`
            : `Normal resource ${resource.id}. Maintain current configuration.`,
        severity: STATUS_SEVERITY[resource.status] || 'info',
      }))
  }, [resources])

  const chartData = useMemo(() => {
    const counts = resources.reduce(
      (acc, resource) => {
        acc[resource.status] = (acc[resource.status] || 0) + 1
        return acc
      },
      { Normal: 0, Underutilized: 0, Overutilized: 0 },
    )
    return [
      { name: 'Normal', value: counts.Normal, color: '#22c55e' },
      { name: 'Underutilized', value: counts.Underutilized, color: '#f59e0b' },
      { name: 'Overutilized', value: counts.Overutilized, color: '#ef4444' },
    ]
  }, [resources])

  return (
    <div className={`min-h-screen bg-slate-950 text-slate-100 transition-opacity duration-500 ${isRefreshing ? 'opacity-80' : 'opacity-100'}`}>
      <main className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <Header 
          timeLeft={timeLeft} 
          isRefreshing={isRefreshing} 
          isPaused={isPaused} 
          setIsPaused={setIsPaused} 
          loadResources={loadResources}
          lastUpdated={lastUpdated}
        />

        <HowItWorksPanel />
        <SummaryCards summary={summary} />
        <LiveDecisionEngine resources={resources.slice(0, 3)} />

        {/* MAIN LAYOUT: Resource Table + Sidebar */}
        <div className="grid gap-6 lg:grid-cols-10">
          {/* LEFT COLUMN: Resource Table & Charts */}
          <div className={`flex flex-col gap-6 transition-all duration-300 ${selectedResource ? 'lg:col-span-6' : 'lg:col-span-7'}`}>
            <ResourceTable 
              resources={resources} 
              isLoading={isLoading} 
              onSelectResource={setSelectedResource}
              selectedResource={selectedResource}
              simulationData={simulationData}
            />

            <AlertsPanel alerts={alerts} />
          </div>

          {/* RIGHT SIDEBAR: Simulation Panel / Standards */}
          <div className={`transition-all duration-300 ${selectedResource ? 'lg:col-span-4' : 'lg:col-span-3'}`}>
            <div className="sticky top-6 flex flex-col gap-6">
              {selectedResource ? (
                <>
                  <ResourceSimulationPanel
                    key={selectedResource.id}
                    resource={selectedResource}
                    onClose={() => {
                      setSelectedResource(null)
                      setSimulationData(null)
                    }}
                    onSimulationChange={setSimulationData}
                    simulationData={simulationData}
                  />
                  <ForecastTimeline resource={selectedResource} simulationData={simulationData} />
                </>
              ) : (
                <StandardsPanel />
              )}
            </div>
          </div>
        </div>

        {/* GRAPHS AT THE BOTTOM */}
        <div className="mt-2">
          <ChartsSection cpuData={resources} statusData={chartData} />
        </div>
      </main>
    </div>
  )
}

export default App
