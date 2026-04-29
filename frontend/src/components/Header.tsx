/**
 * Dashboard header with organization info and controls.
 */

import { useDashboardStore } from '../store/dashboard';

export function Header() {
  const { selectedStackId, stacks } = useDashboardStore();
  const selectedStack = stacks.find((s) => s.id === selectedStackId);

  return (
    <header className="fixed top-0 left-64 right-0 h-16 border-b border-white/10 bg-black/40 backdrop-blur-xl px-8 flex items-center justify-between">
      <div>
        <h1 className="text-lg font-semibold text-white">
          {selectedStack?.org_name || 'SentryIQ'}
        </h1>
        <p className="text-xs text-slate-400">
          {selectedStack ? `ID: ${selectedStack.id.substring(0, 8)}...` : 'No stack selected'}
        </p>
      </div>

      <div className="flex items-center gap-4">
        <button className="px-4 py-2 rounded-lg bg-white/10 text-white text-sm hover:bg-white/15 transition">
          Settings
        </button>
        <button className="px-4 py-2 rounded-lg bg-aurora-500 text-black text-sm font-medium hover:opacity-90 transition">
          Export Report
        </button>
      </div>
    </header>
  );
}
