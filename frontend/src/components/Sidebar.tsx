/**
 * Sidebar navigation component.
 */

import { useDashboardStore } from '../store/dashboard';

export interface NavItem {
  id: 'dashboard' | 'stacks' | 'vulnerabilities' | 'chains' | 'compliance' | 'simulations' | 'human-risk';
  label: string;
  icon: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
  { id: 'stacks', label: 'Stacks', icon: '🖥️' },
  { id: 'vulnerabilities', label: 'Alerts', icon: '🚨' },
  { id: 'chains', label: 'Chains', icon: '🔗' },
  { id: 'compliance', label: 'Compliance', icon: '✅' },
  { id: 'simulations', label: 'Simulations', icon: '📧' },
  { id: 'human-risk', label: 'Human Risk', icon: '👥' },
];

export function Sidebar() {
  const { currentPage, setCurrentPage } = useDashboardStore();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 border-r border-white/10 bg-black/40 backdrop-blur-xl">
      <div className="p-6">
        <h2 className="text-2xl font-bold text-white">SentryIQ</h2>
        <p className="text-xs text-slate-400 mt-1">Security Platform</p>
      </div>

      <nav className="mt-8 space-y-2 px-4">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => setCurrentPage(item.id as any)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition ${
              currentPage === item.id
                ? 'bg-white/15 text-white border border-white/20'
                : 'text-slate-300 hover:bg-white/5'
            }`}
          >
            <span className="text-lg">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="absolute bottom-6 left-6 right-6 p-4 rounded-lg bg-white/5 border border-white/10">
        <p className="text-xs text-slate-400">Phase 5 Complete</p>
        <p className="text-sm text-white font-medium mt-1">Human Shield Ready</p>
      </div>
    </aside>
  );
}
