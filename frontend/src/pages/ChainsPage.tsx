/**
 * Vulnerability chains visualization page.
 */

import { useEffect } from 'react';
import { useDashboardStore } from '../store/dashboard';

const OUTCOME_ICONS = {
  RCE: '💀',
  PRIVESC: '⬆️',
  EXFIL: '📤',
  AUTH_BYPASS: '🔓',
  CHAIN_ATTACK: '⛓️',
};

export function ChainsPage() {
  const { stacks, selectedStackId, setSelectedStack, chains, fetchChains, analyzeChains, isLoading, error } = useDashboardStore();
  const stackChains = selectedStackId ? chains[selectedStackId] || [] : [];

  // Fetch chains when stack changes
  useEffect(() => {
    if (selectedStackId) {
      fetchChains(selectedStackId);
    }
  }, [selectedStackId, fetchChains]);

  return (
    <main className="ml-64 mt-16 min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-black p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-2">Attack Chains</h1>
        <p className="text-slate-400 mb-8">Multi-hop vulnerability chains detected in your infrastructure</p>

        {error && (
          <div className="mb-6 p-4 rounded-lg bg-red-500/20 border border-red-500/30 text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Stack Selector */}
        <div className="mb-8 rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
          <label className="block text-sm font-medium text-white mb-3">Select Stack</label>
          <div className="flex gap-4">
            <select
              value={selectedStackId || ''}
              onChange={(e) => setSelectedStack(e.target.value || null)}
              className="flex-1 px-4 py-2 rounded-lg bg-black/30 border border-white/10 text-white focus:outline-none focus:border-white/30"
            >
              <option value="">-- Choose a stack --</option>
              {stacks.map((stack) => (
                <option key={stack.id} value={stack.id}>
                  {stack.org_name}
                </option>
              ))}
            </select>
            {selectedStackId && (
              <button
                onClick={() => analyzeChains(selectedStackId)}
                disabled={isLoading}
                className="px-6 py-2 rounded-lg bg-aurora-500 text-black font-medium hover:opacity-90 disabled:opacity-50 transition"
              >
                {isLoading ? 'Analyzing...' : '🧠 Analyze Chains'}
              </button>
            )}
          </div>
        </div>

        {/* Chains */}
        {!selectedStackId ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl text-center">
            <p className="text-slate-400">Select a stack to view attack chains</p>
          </div>
        ) : stackChains.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl text-center">
            <p className="text-slate-400">No chains detected for this stack</p>
            <p className="text-slate-500 text-sm mt-2">Click "Analyze Chains" to detect multi-hop vulnerability paths</p>
          </div>
        ) : (
          <div className="space-y-4">
            {stackChains
              .sort((a, b) => b.chain_score - a.chain_score)
              .map((chain) => (
                <div
                  key={chain.chain_id}
                  className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl hover:border-white/20 transition"
                >
                  <div className="flex items-center gap-4 mb-4">
                    <div className="text-3xl">
                      {OUTCOME_ICONS[chain.attack_outcome] || '⚠️'}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-white">Chain {chain.chain_id.substring(0, 8)}</h3>
                      <p className="text-xs text-slate-400 mt-1">
                        Outcome: <span className="text-amber-300 font-medium">{chain.attack_outcome}</span>
                      </p>
                    </div>
                    <div className="ml-auto">
                      <p className="text-right text-sm font-semibold text-white">
                        {chain.chain_score.toFixed(1)}
                      </p>
                      <p className="text-xs text-slate-400">Chain Score</p>
                    </div>
                  </div>

                  {/* CVE Chain */}
                  <div className="mb-4 p-4 rounded-lg bg-black/30 border border-white/10">
                    <p className="text-xs font-medium text-slate-400 mb-2">CVE Chain ({chain.cve_ids.length} vulnerabilities):</p>
                    <div className="flex items-center gap-2 flex-wrap">
                      {chain.cve_ids.map((cve, idx) => (
                        <div key={cve} className="flex items-center">
                          <span className="px-2 py-1 rounded bg-slate-700 text-white text-xs font-mono">
                            {cve}
                          </span>
                          {idx < chain.cve_ids.length - 1 && (
                            <span className="mx-2 text-slate-500">→</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Narrative */}
                  <div>
                    <p className="text-sm font-semibold text-white mb-2">Attack Narrative:</p>
                    <p className="text-slate-300 text-sm leading-relaxed">
                      {chain.chain_narrative || 'Chain analysis pending...'}
                    </p>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </main>
  );
}
