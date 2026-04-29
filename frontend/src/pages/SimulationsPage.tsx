/**
 * Simulation center page for managing phishing campaigns.
 */

import { useEffect, useState } from 'react';
import { useDashboardStore } from '../store/dashboard';

export function SimulationsPage() {
  const { stacks, selectedStackId, setSelectedStack, isLoading, error, setError } = useDashboardStore();
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    campaign_type: 'phishing',
    target_employee_role: 'HR',
  });

  const [targetEmployees, setTargetEmployees] = useState('');

  const handleCreateCampaign = async () => {
    if (!selectedStackId) {
      setError('Please select a stack first');
      return;
    }

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/simulations/campaigns/create`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            stack_id: selectedStackId,
            campaign_type: formData.campaign_type,
            target_employee_role: formData.target_employee_role,
            company_name: stacks.find((s) => s.id === selectedStackId)?.org_name || 'Organization',
          }),
        }
      );

      if (!response.ok) throw new Error('Campaign creation failed');
      const campaign = await response.json();
      setCampaigns([campaign, ...campaigns]);
      setShowCreateForm(false);
      setFormData({ campaign_type: 'phishing', target_employee_role: 'HR' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create campaign');
    }
  };

  const handleLaunchCampaign = async (campaignId: string) => {
    if (!targetEmployees.trim()) {
      setError('Please enter employee IDs');
      return;
    }

    try {
      const empIds = targetEmployees
        .split('\n')
        .map((id) => id.trim())
        .filter(Boolean);

      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/simulations/campaigns/${campaignId}/launch`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ target_employee_ids: empIds }),
        }
      );

      if (!response.ok) throw new Error('Launch failed');
      const result = await response.json();
      setCampaigns(campaigns.map((c) => (c.campaign_id === campaignId ? { ...c, status: 'sent' } : c)));
      setTargetEmployees('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to launch campaign');
    }
  };

  return (
    <main className="ml-64 mt-16 min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-black p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-2">Simulation Center</h1>
        <p className="text-slate-400 mb-8">Create and manage phishing campaigns for security awareness training</p>

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
                onClick={() => setShowCreateForm(!showCreateForm)}
                className="px-6 py-2 rounded-lg bg-aurora-500 text-black font-medium hover:opacity-90 transition"
              >
                ➕ Create Campaign
              </button>
            )}
          </div>
        </div>

        {/* Create Campaign Form */}
        {showCreateForm && (
          <div className="mb-8 rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl">
            <h2 className="text-2xl font-semibold text-white mb-6">New Campaign</h2>

            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-white mb-2">Campaign Type</label>
                <select
                  value={formData.campaign_type}
                  onChange={(e) => setFormData({ ...formData, campaign_type: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg bg-black/30 border border-white/10 text-white focus:outline-none focus:border-white/30"
                >
                  <option value="phishing">Phishing (Email)</option>
                  <option value="vishing">Vishing (Phone)</option>
                  <option value="smishing">Smishing (SMS)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-white mb-2">Target Role</label>
                <select
                  value={formData.target_employee_role}
                  onChange={(e) => setFormData({ ...formData, target_employee_role: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg bg-black/30 border border-white/10 text-white focus:outline-none focus:border-white/30"
                >
                  <option value="HR">HR/People Ops</option>
                  <option value="Finance">Finance/Accounting</option>
                  <option value="IT">IT/Tech Support</option>
                  <option value="Executive">Executive/C-Suite</option>
                  <option value="Marketing">Marketing/Communications</option>
                  <option value="General">General/All Employees</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-white mb-2">Target Employee IDs (one per line)</label>
                <textarea
                  placeholder="emp_hash_001&#10;emp_hash_002&#10;emp_hash_003"
                  className="w-full px-4 py-2 rounded-lg bg-black/30 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-white/30 font-mono text-sm"
                  rows={4}
                  value={targetEmployees}
                  onChange={(e) => setTargetEmployees(e.target.value)}
                />
              </div>

              <div className="flex gap-4">
                <button
                  onClick={handleCreateCampaign}
                  disabled={isLoading}
                  className="flex-1 px-4 py-3 rounded-lg bg-aurora-500 text-black font-medium hover:opacity-90 disabled:opacity-50 transition"
                >
                  {isLoading ? 'Creating...' : '✨ Generate & Launch'}
                </button>
                <button
                  onClick={() => {
                    setShowCreateForm(false);
                    setTargetEmployees('');
                  }}
                  className="flex-1 px-4 py-3 rounded-lg bg-white/10 text-white font-medium hover:bg-white/20 transition"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Campaigns List */}
        {!selectedStackId ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl text-center">
            <p className="text-slate-400">Select a stack to manage campaigns</p>
          </div>
        ) : campaigns.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl text-center">
            <p className="text-slate-400">No campaigns yet</p>
            <p className="text-slate-500 text-sm mt-2">Create your first phishing simulation campaign</p>
          </div>
        ) : (
          <div className="space-y-4">
            {campaigns.map((campaign) => (
              <div
                key={campaign.campaign_id}
                className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl hover:border-white/20 transition"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-white">
                      {campaign.campaign_type === 'phishing' && '📧'} {campaign.target_role} Campaign
                    </h3>
                    <p className="text-xs text-slate-500 mt-1">{campaign.campaign_id}</p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-lg text-xs font-medium ${
                      campaign.status === 'sent'
                        ? 'bg-amber-500/20 text-amber-300'
                        : 'bg-blue-500/20 text-blue-300'
                    }`}
                  >
                    {campaign.status === 'sent' ? '📤 Sent' : '⏳ Pending'}
                  </span>
                </div>

                <div className="p-4 rounded-lg bg-black/30 border border-white/10 mb-4">
                  <p className="text-xs text-slate-400 font-medium mb-2">Email Subject:</p>
                  <p className="text-sm text-white">{campaign.email_subject}</p>
                </div>

                <p className="text-sm text-slate-300 mb-4">
                  <span className="font-medium">Sender:</span> {campaign.sender_identity}
                </p>

                {campaign.status === 'pending' && (
                  <button
                    onClick={() => handleLaunchCampaign(campaign.campaign_id)}
                    disabled={isLoading}
                    className="w-full px-4 py-2 rounded-lg bg-aurora-500 text-black font-medium hover:opacity-90 disabled:opacity-50 transition"
                  >
                    {isLoading ? 'Launching...' : '🚀 Launch Campaign'}
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
