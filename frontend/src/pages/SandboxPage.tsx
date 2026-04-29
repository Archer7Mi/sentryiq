/**
 * Sandbox monitoring and audit dashboard page.
 */

import { useEffect, useState } from 'react';
import { useDashboardStore } from '../store/dashboard';

const SEVERITY_COLORS = {
  LOW: 'bg-green-500/20 text-green-300 border-green-500/30',
  MEDIUM: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  HIGH: 'bg-red-500/20 text-red-300 border-red-500/30',
};

const HEALTH_COLORS = {
  HEALTHY: 'bg-green-500/20 text-green-300',
  DEGRADED: 'bg-amber-500/20 text-amber-300',
  UNHEALTHY: 'bg-red-500/20 text-red-300',
  NO_DATA: 'bg-slate-500/20 text-slate-300',
};

export function SandboxPage() {
  const { isLoading, error, setError } = useDashboardStore();
  const [sandboxStatus, setSandboxStatus] = useState<any>(null);
  const [monitoring, setMonitoring] = useState<any>(null);
  const [agentsHealth, setAgentsHealth] = useState<any[]>([]);
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'agents' | 'anomalies'>('overview');

  useEffect(() => {
    fetchSandboxData();
    const interval = setInterval(fetchSandboxData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const fetchSandboxData = async () => {
    try {
      const [statusRes, monitoringRes, healthRes, anomaliesRes] = await Promise.all([
        fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/sandbox/status`),
        fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/sandbox/monitoring/summary`),
        fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/sandbox/agents/health`),
        fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/sandbox/anomalies?limit=50`),
      ]);

      if (statusRes.ok) {
        const data = await statusRes.json();
        setSandboxStatus(data.data);
      }

      if (monitoringRes.ok) {
        const data = await monitoringRes.json();
        setMonitoring(data.data);
      }

      if (healthRes.ok) {
        const data = await healthRes.json();
        setAgentsHealth(data.agents || []);
      }

      if (anomaliesRes.ok) {
        const data = await anomaliesRes.json();
        setAnomalies(data.anomalies || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch sandbox data');
    }
  };

  return (
    <main className="ml-64 mt-16 min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-black p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-2">Sandbox Control Center</h1>
        <p className="text-slate-400 mb-8">NemoClaw agent security and audit monitoring</p>

        {error && (
          <div className="mb-6 p-4 rounded-lg bg-red-500/20 border border-red-500/30 text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Sandbox Status Cards */}
        {sandboxStatus && (
          <div className="grid gap-4 grid-cols-1 md:grid-cols-4 mb-8">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
              <p className="text-sm text-slate-400 mb-2">Status</p>
              <p className="text-2xl font-bold text-white">
                {sandboxStatus.initialized ? '🟢 Active' : '🔴 Inactive'}
              </p>
              <p className="text-xs text-slate-500 mt-2">NemoClaw runtime</p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
              <p className="text-sm text-slate-400 mb-2">Registered Agents</p>
              <p className="text-2xl font-bold text-white">{sandboxStatus.registered_agents}</p>
              <p className="text-xs text-slate-500 mt-2">Sandboxed</p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
              <p className="text-sm text-slate-400 mb-2">Total Executions</p>
              <p className="text-2xl font-bold text-aurora-400">{sandboxStatus.total_executions}</p>
              <p className="text-xs text-slate-500 mt-2">All-time</p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
              <p className="text-sm text-slate-400 mb-2">Anomalies Detected</p>
              <p className="text-2xl font-bold text-orange-400">{monitoring?.high_severity_anomalies || 0}</p>
              <p className="text-xs text-slate-500 mt-2">High severity</p>
            </div>
          </div>
        )}

        {/* Monitoring Summary */}
        {monitoring && (
          <div className="mb-8 rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
            <h2 className="text-lg font-semibold text-white mb-4">Overall Performance</h2>

            <div className="grid gap-4 grid-cols-1 md:grid-cols-3 mb-6">
              <div>
                <p className="text-sm text-slate-400 mb-2">Success Rate</p>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold text-white">
                    {(monitoring.overall_success_rate * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-2 rounded-full bg-black/30 mt-3 overflow-hidden">
                  <div
                    className="h-full bg-aurora-500"
                    style={{ width: `${monitoring.overall_success_rate * 100}%` }}
                  />
                </div>
              </div>

              <div>
                <p className="text-sm text-slate-400 mb-2">Health Distribution</p>
                <div className="flex gap-2 text-sm">
                  <div className="flex flex-col items-center">
                    <span className="text-lg font-bold text-green-400">
                      {monitoring.health_distribution.HEALTHY}
                    </span>
                    <span className="text-xs text-slate-500">Healthy</span>
                  </div>
                  <div className="flex flex-col items-center">
                    <span className="text-lg font-bold text-amber-400">
                      {monitoring.health_distribution.DEGRADED}
                    </span>
                    <span className="text-xs text-slate-500">Degraded</span>
                  </div>
                  <div className="flex flex-col items-center">
                    <span className="text-lg font-bold text-red-400">
                      {monitoring.health_distribution.UNHEALTHY}
                    </span>
                    <span className="text-xs text-slate-500">Unhealthy</span>
                  </div>
                </div>
              </div>

              <div>
                <p className="text-sm text-slate-400 mb-2">Total Anomalies</p>
                <div className="text-3xl font-bold text-white">{monitoring.total_anomalies}</div>
                <p className="text-xs text-slate-500 mt-3">
                  {monitoring.high_severity_anomalies} high severity
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-8 border-b border-white/10">
          {(['overview', 'agents', 'anomalies'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setSelectedTab(tab)}
              className={`px-4 py-3 font-medium transition ${
                selectedTab === tab
                  ? 'text-white border-b-2 border-aurora-500'
                  : 'text-slate-400 hover:text-slate-300'
              }`}
            >
              {tab === 'overview' && '📊 Overview'}
              {tab === 'agents' && '🤖 Agents'}
              {tab === 'anomalies' && '⚠️ Anomalies'}
            </button>
          ))}
        </div>

        {/* Tab Content */}

        {/* Agents Tab */}
        {selectedTab === 'agents' && (
          <div className="space-y-4">
            {agentsHealth.length === 0 ? (
              <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl text-center">
                <p className="text-slate-400">No agents registered</p>
              </div>
            ) : (
              agentsHealth.map((agent) => (
                <div
                  key={agent.agent_name}
                  className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl hover:border-white/20 transition"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-white">{agent.agent_name}</h3>
                      <p className="text-xs text-slate-500 mt-1">
                        Status: <span className={`font-medium ${HEALTH_COLORS[agent.status]}`}>{agent.status}</span>
                      </p>
                    </div>
                    <span className={`px-3 py-1 rounded-lg text-xs font-bold border ${HEALTH_COLORS[agent.status]}`}>
                      {agent.success_rate ? `${(agent.success_rate * 100).toFixed(0)}%` : 'N/A'}
                    </span>
                  </div>

                  <div className="grid gap-3 grid-cols-2 md:grid-cols-5 text-sm">
                    <div>
                      <p className="text-slate-400">Executions</p>
                      <p className="text-white font-medium">{agent.total_executions}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Successful</p>
                      <p className="text-green-400 font-medium">{agent.successful_executions}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Failed</p>
                      <p className="text-red-400 font-medium">{agent.failed_executions}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Avg Duration</p>
                      <p className="text-white font-medium">{agent.average_duration_seconds?.toFixed(2)}s</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Memory Used</p>
                      <p className="text-white font-medium">{agent.total_memory_used_mb}MB</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Anomalies Tab */}
        {selectedTab === 'anomalies' && (
          <div className="space-y-4">
            {anomalies.length === 0 ? (
              <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl text-center">
                <p className="text-slate-400">✅ No anomalies detected</p>
              </div>
            ) : (
              anomalies.map((anomaly, idx) => (
                <div
                  key={idx}
                  className={`rounded-2xl border p-6 backdrop-blur-xl hover:border-white/20 transition ${
                    anomaly.severity === 'HIGH'
                      ? 'border-red-500/30 bg-red-500/10'
                      : anomaly.severity === 'MEDIUM'
                      ? 'border-amber-500/30 bg-amber-500/10'
                      : 'border-green-500/30 bg-green-500/10'
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="text-white font-medium">{anomaly.agent_name}</p>
                      <p className="text-xs text-slate-400 mt-1">{anomaly.timestamp}</p>
                    </div>
                    <span
                      className={`px-3 py-1 rounded-lg text-xs font-bold border ${SEVERITY_COLORS[anomaly.severity]}`}
                    >
                      {anomaly.severity}
                    </span>
                  </div>

                  <ul className="space-y-1 text-sm">
                    {anomaly.reasons.map((reason: string, i: number) => (
                      <li key={i} className="text-slate-300 flex gap-2">
                        <span>•</span>
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>

                  <div className="mt-3 pt-3 border-t border-white/10 text-xs text-slate-400">
                    Duration: {anomaly.duration_seconds?.toFixed(2)}s | Memory: {anomaly.memory_used_mb}MB
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Overview Tab (Recent Anomalies) */}
        {selectedTab === 'overview' && monitoring && (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
            <h2 className="text-lg font-semibold text-white mb-4">Recent Anomalies</h2>

            {monitoring.recent_anomalies && monitoring.recent_anomalies.length > 0 ? (
              <div className="space-y-3">
                {monitoring.recent_anomalies.map((anomaly: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg bg-black/30 border border-white/10 flex justify-between items-center"
                  >
                    <div>
                      <p className="text-sm font-medium text-white">{anomaly.agent_name}</p>
                      <p className="text-xs text-slate-500">{anomaly.reasons?.[0]}</p>
                    </div>
                    <span
                      className={`px-2 py-1 rounded text-xs font-bold ${
                        SEVERITY_COLORS[anomaly.severity as keyof typeof SEVERITY_COLORS]
                      }`}
                    >
                      {anomaly.severity}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-400">No recent anomalies</p>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
