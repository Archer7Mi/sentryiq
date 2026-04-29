/**
 * Dashboard overview page with metrics and summaries.
 */

import { useDashboardStore } from '../store/dashboard';
import { MetricCard } from './MetricCard';

export function DashboardPage() {
  const { stacks, vulnerabilities, chains } = useDashboardStore();

  const totalVulns = Object.values(vulnerabilities).reduce((sum, vulns) => sum + vulns.length, 0);
  const totalChains = Object.values(chains).reduce((sum, chs) => sum + chs.length, 0);
  const criticalCount = Object.values(vulnerabilities).reduce(
    (sum, vulns) => sum + vulns.filter((v) => v.priority_label === 'CRITICAL').length,
    0
  );

  const metrics = [
    { label: 'Registered Stacks', value: stacks.length, detail: 'Organizations' },
    { label: 'Total Alerts', value: totalVulns, detail: 'Vulnerabilities' },
    { label: 'Chains Detected', value: totalChains, detail: 'Attack paths' },
    { label: 'Critical Priority', value: criticalCount, detail: 'Immediate action' },
  ];

  return (
    <main className="ml-64 mt-16 min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-black p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-2">Security Overview</h1>
        <p className="text-slate-400 mb-8">Real-time vulnerability intelligence for your organization</p>

        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          {metrics.map((metric) => (
            <MetricCard key={metric.label} label={metric.label} value={metric.value} detail={metric.detail} />
          ))}
        </div>

        <div className="grid gap-8 grid-cols-1 lg:grid-cols-2">
          {/* Recent Alerts */}
          <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
            <h2 className="text-lg font-semibold text-white mb-4">Recent Alerts</h2>
            <div className="space-y-2">
              {totalVulns === 0 ? (
                <p className="text-slate-400 text-sm">No alerts yet. Add a stack to begin.</p>
              ) : (
                <p className="text-slate-300 text-sm">{totalVulns} active vulnerabilities across all stacks</p>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
            <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <button className="w-full px-4 py-2 rounded-lg bg-aurora-500/20 text-aurora-300 hover:bg-aurora-500/30 transition text-sm font-medium">
                ➕ Register New Stack
              </button>
              <button className="w-full px-4 py-2 rounded-lg bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 transition text-sm font-medium">
                🔄 Sync CVE Data
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
