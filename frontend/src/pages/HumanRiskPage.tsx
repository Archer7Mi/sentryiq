/**
 * Human risk scoring dashboard.
 */

import { useEffect, useState } from 'react';
import { useDashboardStore } from '../store/dashboard';

const RISK_COLORS = {
  LOW: 'bg-green-500/20 text-green-300 border-green-500/30',
  MEDIUM: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  HIGH: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  CRITICAL: 'bg-red-500/20 text-red-300 border-red-500/30',
};

export function HumanRiskPage() {
  const { stacks, selectedStackId, setSelectedStack, isLoading, error } = useDashboardStore();
  const [orgRisk, setOrgRisk] = useState<any>(null);

  useEffect(() => {
    if (selectedStackId) {
      fetchOrgRisk(selectedStackId);
    }
  }, [selectedStackId]);

  const fetchOrgRisk = async (stackId: string) => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/simulations/risk/${stackId}/organization`
      );
      if (!response.ok) throw new Error('Failed to fetch risk');
      const data = await response.json();
      setOrgRisk(data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <main className="ml-64 mt-16 min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-black p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-2">Human Risk Scoring</h1>
        <p className="text-slate-400 mb-8">Employee security awareness and risk profiles</p>

        {error && (
          <div className="mb-6 p-4 rounded-lg bg-red-500/20 border border-red-500/30 text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Stack Selector */}
        <div className="mb-8 rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
          <label className="block text-sm font-medium text-white mb-3">Select Stack</label>
          <select
            value={selectedStackId || ''}
            onChange={(e) => setSelectedStack(e.target.value || null)}
            className="w-full max-w-md px-4 py-2 rounded-lg bg-black/30 border border-white/10 text-white focus:outline-none focus:border-white/30"
          >
            <option value="">-- Choose a stack --</option>
            {stacks.map((stack) => (
              <option key={stack.id} value={stack.id}>
                {stack.org_name}
              </option>
            ))}
          </select>
        </div>

        {/* Organization Risk Summary */}
        {!selectedStackId ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl text-center">
            <p className="text-slate-400">Select a stack to view human risk profile</p>
          </div>
        ) : !orgRisk ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl text-center">
            <p className="text-slate-400">No risk data yet</p>
            <p className="text-slate-500 text-sm mt-2">Run phishing simulations to generate risk scores</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid gap-4 grid-cols-1 md:grid-cols-4">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
                <p className="text-sm text-slate-400 mb-2">Average Risk</p>
                <p className="text-3xl font-bold text-white">{orgRisk.average_risk}</p>
                <p className="text-xs text-slate-500 mt-2">Organization-wide score</p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
                <p className="text-sm text-slate-400 mb-2">Total Employees</p>
                <p className="text-3xl font-bold text-white">{orgRisk.total_employees}</p>
                <p className="text-xs text-slate-500 mt-2">Tracked in system</p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
                <p className="text-sm text-slate-400 mb-2">High Risk</p>
                <p className="text-3xl font-bold text-orange-400">{orgRisk.risk_distribution?.high || 0}</p>
                <p className="text-xs text-slate-500 mt-2">Need training</p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
                <p className="text-sm text-slate-400 mb-2">Low Risk</p>
                <p className="text-3xl font-bold text-green-400">{orgRisk.risk_distribution?.low || 0}</p>
                <p className="text-xs text-slate-500 mt-2">Security champions</p>
              </div>
            </div>

            {/* Risk Distribution */}
            <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
              <h2 className="text-lg font-semibold text-white mb-4">Risk Distribution</h2>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-slate-300">🔴 Critical</span>
                    <span className="text-sm font-medium text-white">0 employees</span>
                  </div>
                  <div className="h-2 rounded-full bg-black/30 overflow-hidden">
                    <div className="h-full bg-red-500" style={{ width: '0%' }} />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-slate-300">🟠 High</span>
                    <span className="text-sm font-medium text-white">{orgRisk.risk_distribution?.high} employees</span>
                  </div>
                  <div className="h-2 rounded-full bg-black/30 overflow-hidden">
                    <div
                      className="h-full bg-orange-500"
                      style={{
                        width: `${
                          orgRisk.total_employees > 0
                            ? (orgRisk.risk_distribution?.high / orgRisk.total_employees) * 100
                            : 0
                        }%`,
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-slate-300">🟡 Medium</span>
                    <span className="text-sm font-medium text-white">{orgRisk.risk_distribution?.medium} employees</span>
                  </div>
                  <div className="h-2 rounded-full bg-black/30 overflow-hidden">
                    <div
                      className="h-full bg-amber-500"
                      style={{
                        width: `${
                          orgRisk.total_employees > 0
                            ? (orgRisk.risk_distribution?.medium / orgRisk.total_employees) * 100
                            : 0
                        }%`,
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-slate-300">🟢 Low</span>
                    <span className="text-sm font-medium text-white">{orgRisk.risk_distribution?.low} employees</span>
                  </div>
                  <div className="h-2 rounded-full bg-black/30 overflow-hidden">
                    <div
                      className="h-full bg-green-500"
                      style={{
                        width: `${
                          orgRisk.total_employees > 0
                            ? (orgRisk.risk_distribution?.low / orgRisk.total_employees) * 100
                            : 0
                        }%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendations */}
            <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
              <h2 className="text-lg font-semibold text-white mb-4">Organization Recommendations</h2>
              <ul className="space-y-2">
                {orgRisk.recommendations?.map((rec: string, idx: number) => (
                  <li key={idx} className="flex gap-3 text-sm text-slate-300">
                    <span className="text-lg">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Top At-Risk Employees */}
            {orgRisk.top_at_risk && orgRisk.top_at_risk.length > 0 && (
              <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
                <h2 className="text-lg font-semibold text-white mb-4">Top At-Risk Employees</h2>
                <div className="space-y-3">
                  {orgRisk.top_at_risk.map((emp: any) => (
                    <div key={emp.employee_id} className="p-4 rounded-lg bg-black/30 border border-white/10">
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-sm font-medium text-white">{emp.employee_id}</span>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-bold border ${
                            RISK_COLORS[emp.risk_level as keyof typeof RISK_COLORS] ||
                            'bg-slate-500/20 text-slate-300 border-slate-500/30'
                          }`}
                        >
                          {emp.risk_level}
                        </span>
                      </div>
                      <p className="text-sm text-slate-300 mb-2">Score: {emp.risk_score.toFixed(1)}/100</p>
                      <p className="text-xs text-slate-400">
                        Simulations: {emp.simulation_history?.sent || 0} sent, {emp.simulation_history?.clicked || 0} clicked
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
