/**
 * Stack management page with registration wizard.
 */

import { useState } from 'react';
import { useDashboardStore } from '../store/dashboard';

export function StacksPage() {
  const { stacks, addStack } = useDashboardStore();
  const [showWizard, setShowWizard] = useState(false);
  const [formData, setFormData] = useState({
    org_name: '',
    cpe_identifiers: '',
    internet_facing_cpes: '',
    compliance_frameworks: '',
  });

  const handleAddStack = () => {
    if (!formData.org_name) {
      alert('Organization name is required');
      return;
    }

    const newStack = {
      id: `stack-${Date.now()}`,
      org_name: formData.org_name,
      cpe_identifiers: formData.cpe_identifiers.split('\n').filter(Boolean),
      internet_facing_cpes: formData.internet_facing_cpes.split('\n').filter(Boolean),
      compliance_frameworks: formData.compliance_frameworks.split(',').map((f) => f.trim()).filter(Boolean),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    addStack(newStack);
    setFormData({ org_name: '', cpe_identifiers: '', internet_facing_cpes: '', compliance_frameworks: '' });
    setShowWizard(false);
  };

  return (
    <main className="ml-64 mt-16 min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-black p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Stack Registry</h1>
            <p className="text-slate-400">Manage your organization's infrastructure stacks</p>
          </div>
          <button
            onClick={() => setShowWizard(!showWizard)}
            className="px-6 py-3 rounded-lg bg-aurora-500 text-black font-medium hover:opacity-90 transition"
          >
            ➕ Register Stack
          </button>
        </div>

        {/* Registration Wizard */}
        {showWizard && (
          <div className="mb-8 rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl">
            <h2 className="text-2xl font-semibold text-white mb-6">New Stack Registration</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">Organization Name</label>
                <input
                  type="text"
                  placeholder="e.g., TechCorp Nigeria Ltd"
                  className="w-full px-4 py-2 rounded-lg bg-black/30 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-white/30"
                  value={formData.org_name}
                  onChange={(e) => setFormData({ ...formData, org_name: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-white mb-2">CPE Identifiers (one per line)</label>
                <textarea
                  placeholder="cpe:2.3:a:apache:apache:2.4.51:*:*:*:*:*:*:*&#10;cpe:2.3:a:nginx:nginx:1.21.0:*:*:*:*:*:*:*"
                  className="w-full px-4 py-2 rounded-lg bg-black/30 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-white/30 font-mono text-sm"
                  rows={4}
                  value={formData.cpe_identifiers}
                  onChange={(e) => setFormData({ ...formData, cpe_identifiers: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-white mb-2">Internet-Facing CPEs (one per line)</label>
                <textarea
                  placeholder="cpe:2.3:a:apache:apache:2.4.51:*:*:*:*:*:*:*"
                  className="w-full px-4 py-2 rounded-lg bg-black/30 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-white/30 font-mono text-sm"
                  rows={3}
                  value={formData.internet_facing_cpes}
                  onChange={(e) => setFormData({ ...formData, internet_facing_cpes: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-white mb-2">Compliance Frameworks (comma-separated)</label>
                <input
                  type="text"
                  placeholder="NDPA, POPIA, ISO27001"
                  className="w-full px-4 py-2 rounded-lg bg-black/30 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-white/30"
                  value={formData.compliance_frameworks}
                  onChange={(e) => setFormData({ ...formData, compliance_frameworks: e.target.value })}
                />
              </div>

              <div className="flex gap-4">
                <button
                  onClick={handleAddStack}
                  className="flex-1 px-4 py-3 rounded-lg bg-aurora-500 text-black font-medium hover:opacity-90 transition"
                >
                  Create Stack
                </button>
                <button
                  onClick={() => setShowWizard(false)}
                  className="flex-1 px-4 py-3 rounded-lg bg-white/10 text-white font-medium hover:bg-white/20 transition"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Stacks List */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl">
          {stacks.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-slate-400 text-lg">No stacks registered yet</p>
              <p className="text-slate-500 text-sm mt-2">Register your first organization stack to begin</p>
            </div>
          ) : (
            <div className="space-y-4">
              {stacks.map((stack) => (
                <div
                  key={stack.id}
                  className="p-4 rounded-lg bg-black/30 border border-white/10 hover:border-white/20 transition"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-lg font-semibold text-white">{stack.org_name}</h3>
                      <p className="text-xs text-slate-500 mt-1">{stack.id}</p>
                      <div className="mt-3 flex gap-2 flex-wrap">
                        {stack.compliance_frameworks.map((fw) => (
                          <span key={fw} className="px-2 py-1 rounded text-xs bg-amber-500/20 text-amber-300">
                            {fw}
                          </span>
                        ))}
                      </div>
                    </div>
                    <button className="px-4 py-2 rounded-lg bg-white/10 text-white text-sm hover:bg-white/20 transition">
                      View Details
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
