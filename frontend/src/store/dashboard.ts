/**
 * Zustand store for SentryIQ dashboard state.
 * Manages stacks, vulnerabilities, chains, and UI navigation.
 */

import { create } from 'zustand';

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
  currentPage: 'dashboard' | 'stacks' | 'vulnerabilities' | 'chains' | 'compliance';
  setCurrentPage: (page: DashboardStore['currentPage']) => void;

  // Stacks
  stacks: SMBStack[];
  selectedStackId: string | null;
  setSelectedStack: (stackId: string | null) => void;
  addStack: (stack: SMBStack) => void;
  updateStack: (stack: SMBStack) => void;

  // Vulnerabilities
  vulnerabilities: Record<string, Vulnerability[]>; // keyed by stack_id
  fetchVulnerabilities: (stackId: string) => void;

  // Chains
  chains: Record<string, Chain[]>; // keyed by stack_id
  fetchChains: (stackId: string) => void;

  // UI State
  isLoading: boolean;
  error: string | null;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useDashboardStore = create<DashboardStore>((set) => ({
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
  fetchVulnerabilities: (stackId) => {
    // Implementation: fetch from backend
    set((state) => ({
      vulnerabilities: {
        ...state.vulnerabilities,
        [stackId]: [],
      },
    }));
  },

  // Chains
  chains: {},
  fetchChains: (stackId) => {
    // Implementation: fetch from backend
    set((state) => ({
      chains: {
        ...state.chains,
        [stackId]: [],
      },
    }));
  },

  // UI State
  isLoading: false,
  error: null,
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));
