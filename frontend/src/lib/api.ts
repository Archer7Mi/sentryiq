/**
 * API client for communicating with SentryIQ backend.
 * Handles all HTTP requests to FastAPI endpoints.
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Types matching backend models
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

class SentryIQClient {
  private baseUrl: string;

  constructor(baseUrl: string = BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Health check endpoint.
   */
  async health(): Promise<{ status: string; service: string }> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) throw new Error(`Health check failed: ${response.statusText}`);
    return response.json();
  }

  /**
   * Synthesize plain-English alerts for all vulnerabilities in a stack.
   */
  async synthesizeAlerts(stackId: string): Promise<{
    stack_id: string;
    alerts_generated: number;
    total_vulnerabilities: number;
  }> {
    const response = await fetch(`${this.baseUrl}/api/ai/vulnerabilities/${stackId}/synthesize`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error(`Synthesis failed: ${response.statusText}`);
    return response.json();
  }

  /**
   * Analyze vulnerability chains for a stack.
   */
  async analyzeChains(stackId: string): Promise<{
    stack_id: string;
    chains_analyzed: number;
    total_chains: number;
  }> {
    const response = await fetch(`${this.baseUrl}/api/ai/chains/${stackId}/analyze`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error(`Chain analysis failed: ${response.statusText}`);
    return response.json();
  }

  /**
   * Get vulnerability alerts for a stack.
   */
  async getAlerts(stackId: string, priority?: string): Promise<{
    stack_id: string;
    total_alerts: number;
    alerts: Vulnerability[];
  }> {
    const url = new URL(`${this.baseUrl}/api/ai/vulnerabilities/${stackId}`);
    if (priority) url.searchParams.append('priority', priority);

    const response = await fetch(url.toString());
    if (!response.ok) throw new Error(`Failed to fetch alerts: ${response.statusText}`);
    return response.json();
  }

  /**
   * Get vulnerability chains for a stack.
   */
  async getChains(stackId: string): Promise<{
    stack_id: string;
    total_chains: number;
    chains: Chain[];
  }> {
    const response = await fetch(`${this.baseUrl}/api/ai/chains/${stackId}`);
    if (!response.ok) throw new Error(`Failed to fetch chains: ${response.statusText}`);
    return response.json();
  }
}

export const client = new SentryIQClient();
