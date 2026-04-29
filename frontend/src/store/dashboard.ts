/**
 * Zustand store for SentryIQ dashboard state.
 * Manages stacks, vulnerabilities, chains, and UI navigation.
 */

import { create } from 'zustand';
import { client } from '../lib/api';

// Types
export interface SMBStack {
  id: string;
  org_name: string;
  cpe_identifiers: string[];
  internet_facing_cpes: string[];
  compliance_frameworks: string[];
  created_at: string;
  updated_at: string;
}

export interface Vulnerability {
  cve_id: string;
  priority_label: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  priority_score: number;
  plain_english_alert: string;
  remediation_steps: string;
  is_part_of_chain: boolean;
}

export interface Chain {
  chain_id: string;
  cve_ids: string[];
  chain_score: number;
  attack_outcome: 'RCE' | 'PRIVESC' | 'EXFIL' | 'AUTH_BYPASS' | 'CHAIN_ATTACK';
  chain_narrative: string;
}

export interface DashboardStore {
  // Navigation
  currentPage: 'dashboard' | 'stacks' | 'vulnerabilities' | 'chains' | 'compliance' | 'simulations' | 'human-risk';
  setCurrentPage: (page: DashboardStore['currentPage']) => void;

  // Stacks
  stacks: SMBStack[];
  selectedStackId: string | null;
  setSelectedStack: (stackId: string | null) => void;
  addStack: (stack: SMBStack) => void;
  updateStack: (stack: SMBStack) => void;

  // Vulnerabilities
  vulnerabilities: Record<string, Vulnerability[]>; // keyed by stack_id
  fetchVulnerabilities: (stackId: string) => Promise<void>;

  // Chains
  chains: Record<string, Chain[]>; // keyed by stack_id
  fetchChains: (stackId: string) => Promise<void>;

  // AI Operations
  synthesizeAlerts: (stackId: string) => Promise<void>;
  analyzeChains: (stackId: string) => Promise<void>;

  // UI State
  isLoading: boolean;
  error: string | null;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useDashboardStore = create<DashboardStore>((set, get) => ({
  // Navigation
  currentPage: 'dashboard',
  setCurrentPage: (page) => set({ currentPage: page }),

  // Stacks
  stacks: [],
  selectedStackId: null,
  setSelectedStack: (stackId) => set({ selectedStackId: stackId }),
  addStack: (stack) =>
    set((state) => ({
      stacks: [...state.stacks, stack],
      selectedStackId: stack.id,
    })),
  updateStack: (stack) =>
    set((state) => ({
      stacks: state.stacks.map((s) => (s.id === stack.id ? stack : s)),
    })),

  // Vulnerabilities
  vulnerabilities: {},
  fetchVulnerabilities: async (stackId) => {
    set({ isLoading: true, error: null });
    try {
      const response = await client.getAlerts(stackId);
      set((state) => ({
        vulnerabilities: {
          ...state.vulnerabilities,
          [stackId]: response.alerts,
        },
      }));
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to fetch vulnerabilities' });
    } finally {
      set({ isLoading: false });
    }
  },

  // Chains
  chains: {},
  fetchChains: async (stackId) => {
    set({ isLoading: true, error: null });
    try {
      const response = await client.getChains(stackId);
      set((state) => ({
        chains: {
          ...state.chains,
          [stackId]: response.chains,
        },
      }));
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to fetch chains' });
    } finally {
      set({ isLoading: false });
    }
  },

  // AI Operations
  synthesizeAlerts: async (stackId) => {
    set({ isLoading: true, error: null });
    try {
      await client.synthesizeAlerts(stackId);
      // Refresh vulnerabilities after synthesis
      await get().fetchVulnerabilities(stackId);
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to synthesize alerts' });
    } finally {
      set({ isLoading: false });
    }
  },

  analyzeChains: async (stackId) => {
    set({ isLoading: true, error: null });
    try {
      await client.analyzeChains(stackId);
      // Refresh chains after analysis
      await get().fetchChains(stackId);
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to analyze chains' });
    } finally {
      set({ isLoading: false });
    }
  },

  // UI State
  isLoading: false,
  error: null,
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));
