/**
 * Compile-time proof that every shared fixture satisfies its contract type.
 *
 * This file is never imported at runtime. It exists so `npm run typecheck` fails the
 * moment a fixture and its TypeScript type drift apart — the frontend counterpart of
 * the backend's tests/test_contract_routes.py. Together they are the Phase 1
 * integration gate: one fixture set, validated by both sides.
 */

import alexSimulation from '../../public/fixtures/alex-simulation.json';
import backupCandidates from '../../public/fixtures/backup-candidates.json';
import incidentRecoveryEvidence from '../../public/fixtures/incident-recovery-evidence.json';
import incidentRecovery from '../../public/fixtures/incident-recovery.json';
import mitigationPlanApproved from '../../public/fixtures/mitigation-plan-approved.json';
import mitigationPlan from '../../public/fixtures/mitigation-plan.json';
import paymentGatewayGraph from '../../public/fixtures/payment-gateway-graph.json';
import paymentGateway from '../../public/fixtures/payment-gateway.json';
import paymentsSystems from '../../public/fixtures/payments-systems.json';
import platforms from '../../public/fixtures/platforms.json';

import type {
  ApprovePlanResponse,
  BackupCandidateResponse,
  CapabilityDetail,
  EvidenceResponse,
  GraphResponse,
  MitigationPlanResponse,
  PlatformListResponse,
  SimulationResponse,
  SystemDetail,
  SystemListResponse,
} from '@/types/api';

export const checkedFixtures = {
  platforms: platforms as PlatformListResponse,
  paymentsSystems: paymentsSystems as SystemListResponse,
  paymentGateway: paymentGateway as SystemDetail,
  paymentGatewayGraph: paymentGatewayGraph as GraphResponse,
  incidentRecovery: incidentRecovery as CapabilityDetail,
  incidentRecoveryEvidence: incidentRecoveryEvidence as EvidenceResponse,
  alexSimulation: alexSimulation as SimulationResponse,
  backupCandidates: backupCandidates as BackupCandidateResponse,
  mitigationPlan: mitigationPlan as MitigationPlanResponse,
  mitigationPlanApproved: mitigationPlanApproved as ApprovePlanResponse,
} as const;
