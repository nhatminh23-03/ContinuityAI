/**
 * The 10 frozen endpoints. docs/API_CONTRACT.md section 7.
 *
 * Adding an 11th is a Category C decision.
 */

import { request } from './client';
import type {
  ApprovePlanRequest,
  ApprovePlanResponse,
  BackupCandidateRequest,
  BackupCandidateResponse,
  CapabilityDetail,
  EvidenceResponse,
  GraphResponse,
  MitigationPlanRequest,
  MitigationPlanResponse,
  PlatformListResponse,
  SimulationRequest,
  SimulationResponse,
  SystemDetail,
  SystemListResponse,
} from '@/types/api';

export const api = {
  /** 1 */
  listPlatforms: () =>
    request<PlatformListResponse>('/platforms', { fixture: 'platforms' }),

  /** 2 */
  listPlatformSystems: (platformId: string) =>
    request<SystemListResponse>(`/platforms/${platformId}/systems`, {
      fixture: 'payments-systems',
    }),

  /** 3 */
  getSystem: (systemId: string) =>
    request<SystemDetail>(`/systems/${systemId}`, { fixture: 'payment-gateway' }),

  /** 4 */
  getSystemGraph: (systemId: string, focusCapabilityId?: string) =>
    request<GraphResponse>(`/systems/${systemId}/graph`, {
      query: { focus_capability_id: focusCapabilityId },
      fixture: 'payment-gateway-graph',
    }),

  /** 5 */
  getCapability: (capabilityId: string) =>
    request<CapabilityDetail>(`/capabilities/${capabilityId}`, {
      fixture: 'incident-recovery',
    }),

  /** 6 */
  getCapabilityEvidence: (capabilityId: string, engineerId?: string) =>
    request<EvidenceResponse>(`/capabilities/${capabilityId}/evidence`, {
      query: { engineer_id: engineerId },
      fixture: 'incident-recovery-evidence',
    }),

  /** 7 */
  runSimulation: (body: SimulationRequest) =>
    request<SimulationResponse>('/simulations', {
      method: 'POST',
      body,
      fixture: 'alex-simulation',
    }),

  /** 8 */
  compareBackupCandidates: (body: BackupCandidateRequest) =>
    request<BackupCandidateResponse>('/recommendations/backup-candidates', {
      method: 'POST',
      body,
      fixture: 'backup-candidates',
    }),

  /** 9 */
  createMitigationPlan: (body: MitigationPlanRequest) =>
    request<MitigationPlanResponse>('/mitigation-plans', {
      method: 'POST',
      body,
      fixture: 'mitigation-plan',
    }),

  /** 10 */
  approveMitigationPlan: (planId: string, body: ApprovePlanRequest) =>
    request<ApprovePlanResponse>(`/mitigation-plans/${planId}/approve`, {
      method: 'POST',
      body,
      fixture: 'mitigation-plan-approved',
    }),
};

/** Query keys for TanStack Query. */
export const queryKeys = {
  platforms: ['platforms'] as const,
  platformSystems: (id: string) => ['platforms', id, 'systems'] as const,
  system: (id: string) => ['systems', id] as const,
  systemGraph: (id: string, focus?: string) => ['systems', id, 'graph', focus] as const,
  capability: (id: string) => ['capabilities', id] as const,
  capabilityEvidence: (id: string, engineerId?: string) =>
    ['capabilities', id, 'evidence', engineerId] as const,
};
