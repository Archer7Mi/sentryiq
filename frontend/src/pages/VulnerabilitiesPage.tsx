/**
 * Vulnerabilities alert queue page.
 */

import { useDashboardStore } from '../store/dashboard';

const PRIORITY_COLORS = {
  CRITICAL: 'bg-red-500/20 text-red-300 border-red-500/30',
  HIGH: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  MEDIUM: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  LOW: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
};

export function VulnerabilitiesPage() {
  const { stacks, selectedStackId, setSelectedStack, vulnerabilities } = useDashboardStore();
  const stackVulns = selectedStackId ? vulnerabilities[selectedStackId] || [] : [];

  return (
    <main className="ml-64 mt-16 min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-black p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-2">Alert Queue</h1>
        <p className="text-slate-400 mb-8">Prioritized CVE vulnerabilities for your infrastructure</p>

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

        {/* Alerts List */}
        {!selectedStackId ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl text-center">
            <p className="text-slate-400">Select a stack to view vulnerabilities</p>
          </div>
        ) : stackVulns.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl text-center">
            <p className="text-slate-400">No vulnerabilities for this stack</p>
          </div>
        ) : (
          <div className="space-y-4">
            {stackVulns
              .sort((a, b) => b.priority_score - a.priority_score)
              .map((vuln) => (
                <div
                  key={vuln.cve_id}
                  className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl hover:border-white/20 transition"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start gap-4">
                      <span
                        className={`px-3 py-1 rounded-full text-sm font-bold border ${
                          PRIORITY_COLORS[vuln.priority_label]
                        }`}
                      >
                        {vuln.priority_label}
                      </span>
                      <div>
                        <h3 className="text-lg font-semibold text-white">{vuln.cve_id}</h3>
                        <p className="text-xs text-slate-400 mt-1">Score: {vuln.priority_score.toFixed(1)}/100</p>
                      </div>
                    </div>
                    {vuln.is_part_of_chain && (
                      <span className="px-3 py-1 rounded-lg bg-purple-500/20 text-purple-300 text-xs font-medium">
                        🔗 Part of Chain
                      </span>
                    )}
                  </div>

                  <p className="text-slate-300 mb-4">{vuln.plain_english_alert}</p>

                  <div className="p-4 rounded-lg bg-black/30 border border-white/10">
                    <p className="text-sm font-semibold text-white mb-2">Remediation Steps:</p>
                    <p className="text-sm text-slate-300">{vuln.remediation_steps}</p>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </main>
  );
}
