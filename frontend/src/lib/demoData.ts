export type Metric = {
  label: string;
  value: string;
  detail: string;
};

export type QueueItem = {
  title: string;
  reason: string;
  action: string;
  score: number;
};

export type EmployeeRisk = {
  employee: string;
  role: string;
  score: number;
  level: 'low' | 'medium' | 'high';
  coaching: string;
};

export const metrics: Metric[] = [
  {
    label: 'Matched vulnerabilities',
    value: '12',
    detail: 'Across web, identity, and endpoint surfaces',
  },
  {
    label: 'Critical chains',
    value: '3',
    detail: 'Multi-step paths with higher blast radius',
  },
  {
    label: 'Human risk score',
    value: '68',
    detail: 'Blended click, report, and coaching signals',
  },
  {
    label: 'Simulation coverage',
    value: '4 channels',
    detail: 'Email, SMS, voice, and meeting-based scenarios',
  },
];

export const stackSteps = [
  'Capture the SMB stack with a guided onboarding wizard.',
  'Match declared systems to vulnerability intelligence feeds.',
  'Rank patch items by severity, exploitability, and chain risk.',
  'Explain the result in plain English for non-technical admins.',
];

export const queue: QueueItem[] = [
  {
    title: 'Critical chain: Apache + OpenSSL',
    reason: 'Two manageable issues combine into a remote execution path on the public edge.',
    action: 'Patch OpenSSL first, then Apache.',
    score: 97.5,
  },
  {
    title: 'CVE-2025-34560 on Windows Server',
    reason: 'High-value system with confirmed active-exploitation signal.',
    action: 'Schedule the Windows patch window immediately.',
    score: 94,
  },
  {
    title: 'CVE-2025-24017 on Apache HTTP Server',
    reason: 'Internet-facing service with a high exploit probability.',
    action: 'Patch the web tier and validate restart readiness.',
    score: 89.2,
  },
];

export const humanRisk: EmployeeRisk[] = [
  {
    employee: 'Maya Okafor',
    role: 'Finance Manager',
    score: 82,
    level: 'high',
    coaching: 'Verify payment requests by a second channel before acting.',
  },
  {
    employee: 'Jordan Lee',
    role: 'Operations Lead',
    score: 54,
    level: 'medium',
    coaching: 'Report unexpected MFA prompts and logins from new devices.',
  },
  {
    employee: 'Sam Patel',
    role: 'Support Specialist',
    score: 21,
    level: 'low',
    coaching: 'Keep escalating suspicious messages quickly.',
  },
];
