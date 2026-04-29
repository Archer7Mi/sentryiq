/**
 * Compliance mapping and reporting page.
 */

import { useDashboardStore } from '../store/dashboard';

const FRAMEWORK_INFO = {
  NDPA: {
    name: 'Nigeria Data Protection Regulation',
    description: 'Focuses on personal data protection in Nigeria',
    color: 'from-green-500 to-emerald-500',
  },
  POPIA: {
    name: 'Protection of Personal Information Act',
    description: 'South Africa\'s data protection framework',
    color: 'from-blue-500 to-cyan-500',
  },
  'Kenya DPA': {
    name: 'Kenya Data Protection Act 2019',
    description: 'Kenya\'s data protection legislation',
    color: 'from-red-500 to-pink-500',
  },
  'ISO27001': {
    name: 'ISO/IEC 27001:2022',
    description: 'Information security management system standard',
    color: 'from-purple-500 to-violet-500',
  },
  'PCI-DSS': {
    name: 'Payment Card Industry Data Security Standard',
    description: 'Payment card data protection requirements',
    color: 'from-amber-500 to-orange-500',
  },
};

export function CompliancePage() {
  const { stacks, selectedStackId, setSelectedStack } = useDashboardStore();
  const selectedStack = stacks.find((s) => s.id === selectedStackId);

  return (
    <main className="ml-64 mt-16 min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-black p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-2">Compliance Mapping</h1>
        <p className="text-slate-400 mb-8">CVE vulnerabilities mapped to compliance frameworks</p>

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

        {/* Compliance Frameworks */}
        {!selectedStack ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl text-center">
            <p className="text-slate-400">Select a stack to view compliance mapping</p>
          </div>
        ) : selectedStack.compliance_frameworks.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl text-center">
            <p className="text-slate-400">No compliance frameworks configured for this stack</p>
          </div>
        ) : (
          <div className="space-y-4">
            {selectedStack.compliance_frameworks.map((framework) => {
              const info = FRAMEWORK_INFO[framework as keyof typeof FRAMEWORK_INFO] || {
                name: framework,
                description: 'Custom compliance framework',
                color: 'from-slate-500 to-slate-600',
              };

              return (
                <div
                  key={framework}
                  className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl hover:border-white/20 transition"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-white">{info.name}</h3>
                      <p className="text-sm text-slate-400 mt-1">{info.description}</p>
                    </div>
                    <span className="px-3 py-1 rounded-lg bg-white/10 text-white text-xs font-medium">
                      {framework}
                    </span>
                  </div>

                  <div className="grid gap-4 grid-cols-1 md:grid-cols-2 mb-4">
                    <div className="p-4 rounded-lg bg-black/30 border border-white/10">
                      <p className="text-xs text-slate-400 font-medium mb-2">Compliance Status</p>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                        <span className="text-sm text-white">Pending Assessment</span>
                      </div>
                    </div>
                    <div className="p-4 rounded-lg bg-black/30 border border-white/10">
                      <p className="text-xs text-slate-400 font-medium mb-2">Applicability</p>
                      <span className="text-sm text-white">Organization-wide</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-lg bg-black/30 border border-white/10">
                    <p className="text-xs text-slate-400 font-medium mb-2">Mapped Requirements</p>
                    <ul className="space-y-1 text-sm text-slate-300">
                      <li>✓ Personal data protection</li>
                      <li>✓ Incident response</li>
                      <li>✓ Access control</li>
                      <li>✓ Data retention</li>
                    </ul>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}
