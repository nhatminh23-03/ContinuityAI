/**
 * Zod mirror of docs/API_CONTRACT.md — the runtime half of the contract lock.
 *
 * `types/api.ts` locks the shapes at compile time; these schemas prove at test
 * time that every shared fixture (and, when pointed at it, any live payload)
 * actually satisfies the contract. Objects are strict: an undeclared field is
 * contract drift and must fail, not pass silently.
 */

import { z } from 'zod';

/* ---------- enums (contract section 5) ---------- */

export const businessCriticality = z.enum(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']);
export const operationalCriticality = z.enum(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']);
export const readinessLevel = z.enum(['NONE', 'EXPOSED', 'ASSISTED', 'PRACTICED', 'VALIDATED']);
export const capabilityExposure = z.enum([
  'COVERED',
  'DEGRADED',
  'CRITICAL_GAP',
  'INSUFFICIENT_EVIDENCE',
]);
export const continuityRiskClass = z.enum(['LOW', 'MODERATE', 'HIGH', 'CRITICAL']);
export const evidenceStrength = z.enum(['WEAK', 'MODERATE', 'STRONG']);
export const evidenceConfidence = z.enum(['LOW', 'MEDIUM', 'HIGH']);
export const freshness = z.enum(['FRESH', 'AGING', 'STALE']);
export const knowledgeDriftStatus = z.enum([
  'NEW_RISK',
  'RISK_INCREASED',
  'STABLE',
  'RISK_REDUCED',
]);
export const evidenceSourceType = z.enum([
  'COMMIT',
  'PULL_REQUEST',
  'CODE_REVIEW',
  'ISSUE',
  'TICKET',
  'INCIDENT',
  'DOCUMENT',
  'TECHNICAL_DISCUSSION',
  'MANAGER_ATTESTATION',
]);
export const evidenceRole = z.enum([
  'EXPOSURE',
  'CONTRIBUTION',
  'ASSISTED_EXECUTION',
  'INDEPENDENT_EXECUTION',
  'KNOWLEDGE_CAPTURE',
]);
export const graphNodeType = z.enum([
  'PLATFORM',
  'SYSTEM',
  'COMPONENT',
  'CAPABILITY',
  'ENGINEER',
  'EVIDENCE',
]);
export const graphEdgeType = z.enum([
  'HAS_SYSTEM',
  'HAS_COMPONENT',
  'REQUIRES_CAPABILITY',
  'DEMONSTRATES',
  'SUPPORTED_BY',
  'DECLARED_OWNER',
]);
export const simulationType = z.enum(['ENGINEER_UNAVAILABLE']);
export const simulationScopeType = z.enum(['SYSTEM', 'PLATFORM']);
export const technicalOverlap = z.enum(['LOW', 'MEDIUM', 'HIGH']);
export const mitigationPlanStatus = z.enum(['DRAFT', 'APPROVED']);
export const mitigationTaskType = z.enum([
  'KNOWLEDGE_REVIEW',
  'SHADOWING',
  'PRACTICE',
  'RECOVERY_DRILL',
  'DOCUMENTATION',
  'ARCHITECTURE_REVIEW',
]);
export const criticalitySource = z.enum(['HUMAN_CONFIRMED', 'AI_SUGGESTED']);
export const challengeType = z.enum([
  'LINK_EVIDENCE',
  'MANAGER_ATTESTATION',
  'CORRECT_CAPABILITY_MAPPING',
]);
export const errorCode = z.enum([
  'NOT_FOUND',
  'VALIDATION_ERROR',
  'UNAUTHORIZED',
  'INSUFFICIENT_EVIDENCE',
  'AI_EXTRACTION_FAILED',
  'GRAPH_INCONSISTENCY',
  'SIMULATION_FAILED',
  'MITIGATION_GENERATION_FAILED',
  'INTERNAL_ERROR',
]);

/* ---------- shared scalars ---------- */

const riskIndex = z.number().int().min(0).max(100);
const count = z.number().int().min(0);
const isoDate = z.iso.date();
const isoDateTime = z.iso.datetime();
const metadata = z.record(z.string(), z.unknown());

/* ---------- error envelope (section 9) ---------- */

export const apiErrorResponseSchema = z.strictObject({
  error: z.strictObject({
    code: errorCode,
    message: z.string(),
    details: z.record(z.string(), z.unknown()).optional(),
  }),
});

/* ---------- platforms (6.1, 8.1) ---------- */

export const platformSummarySchema = z.strictObject({
  platform_id: z.string(),
  name: z.string(),
  description: z.string().nullable().optional(),
  system_count: count,
  critical_gap_count: count,
  single_expert_dependency_count: count,
  highest_system_risk_index: riskIndex.nullable(),
  drift_status: knowledgeDriftStatus,
});

export const platformListResponseSchema = z.strictObject({
  platforms: z.array(platformSummarySchema),
});

const platformRefSchema = z.strictObject({ platform_id: z.string(), name: z.string() });

/* ---------- systems (6.2, 6.3, 8.2, 8.3) ---------- */

export const systemSummarySchema = z.strictObject({
  system_id: z.string(),
  platform_id: z.string(),
  name: z.string(),
  description: z.string().nullable().optional(),
  business_criticality: businessCriticality,
  continuity_risk_index: riskIndex.nullable(),
  continuity_risk_class: continuityRiskClass.nullable(),
  exposure: capabilityExposure,
  evidence_confidence: evidenceConfidence,
  critical_gap_count: count,
  degraded_capability_count: count,
  covered_capability_count: count,
  insufficient_evidence_count: count,
  drift_status: knowledgeDriftStatus,
});

export const systemListResponseSchema = z.strictObject({
  platform: platformRefSchema,
  systems: z.array(systemSummarySchema),
});

export const systemDetailSchema = systemSummarySchema.extend({
  criticality_source: criticalitySource.optional(),
  rules_triggered: z.array(z.string()).optional(),
  declared_ownership: z
    .strictObject({
      engineer_id: z.string(),
      name: z.string(),
      source: z.string(),
      mismatch_detected: z.boolean(),
    })
    .nullable()
    .optional(),
  components: z.array(
    z.strictObject({
      component_id: z.string(),
      name: z.string(),
      description: z.string().nullable().optional(),
      capability_ids: z.array(z.string()),
    }),
  ),
});

/* ---------- capabilities (6.4, 6.5, 8.5) ---------- */

const engineerRefSchema = z.strictObject({
  engineer_id: z.string(),
  name: z.string(),
  readiness: readinessLevel,
});

export const engineerCoverageSchema = z.strictObject({
  engineer_id: z.string(),
  name: z.string(),
  readiness: readinessLevel,
  freshness,
  evidence_confidence: evidenceConfidence,
  last_demonstrated_at: isoDate.nullable().optional(),
});

const capabilityRefSchema = z.strictObject({ capability_id: z.string(), name: z.string() });

export const capabilityDetailSchema = z.strictObject({
  capability_id: z.string(),
  component_id: z.string(),
  system_id: z.string(),
  name: z.string(),
  description: z.string(),
  operational_criticality: operationalCriticality,
  exposure: capabilityExposure,
  continuity_risk_index: riskIndex.nullable(),
  continuity_risk_class: continuityRiskClass.nullable(),
  evidence_confidence: evidenceConfidence,
  rules_triggered: z.array(z.string()).optional(),
  index_modifiers: z
    .array(z.strictObject({ code: z.string(), delta: z.number().int() }))
    .optional(),
  primary_engineer: engineerRefSchema.nullable().optional(),
  best_remaining_coverage: engineerRefSchema.nullable().optional(),
  engineer_coverage: z.array(engineerCoverageSchema),
});

/* ---------- evidence (6.7, 8.6) ---------- */

export const evidenceRecordSchema = z.strictObject({
  evidence_id: z.string(),
  source_type: evidenceSourceType,
  source_reference: z.string(),
  source_title: z.string().nullable().optional(),
  artifact_date: isoDate,
  engineer_id: z.string(),
  system_id: z.string(),
  component_id: z.string().nullable().optional(),
  capability_id: z.string(),
  evidence_role: evidenceRole,
  evidence_strength: evidenceStrength,
  summary: z.string(),
  freshness,
  provenance: z.strictObject({
    source: z.string(),
    record_id: z.string(),
    source_url: z.string().nullable().optional(),
  }),
});

export const evidenceResponseSchema = z.strictObject({
  capability: capabilityRefSchema,
  assessment: z.strictObject({
    exposure: capabilityExposure,
    evidence_confidence: evidenceConfidence,
    rules_triggered: z.array(z.string()).optional(),
  }),
  evidence: z.array(evidenceRecordSchema),
  missing_evidence: z
    .array(
      z.strictObject({
        engineer_id: z.string(),
        engineer_name: z.string(),
        description: z.string(),
      }),
    )
    .optional(),
  conflicting_evidence: z.array(evidenceRecordSchema).optional(),
  declared_vs_demonstrated: z
    .strictObject({
      declared_owner: z
        .strictObject({ engineer_id: z.string(), name: z.string(), source: z.string() })
        .nullable()
        .optional(),
      strongest_demonstrated_coverage: z
        .strictObject({ engineer_id: z.string(), name: z.string() })
        .nullable()
        .optional(),
      mismatch_detected: z.boolean(),
    })
    .optional(),
});

/* ---------- graph (6.8-6.10, 8.4) ---------- */

export const graphResponseSchema = z.strictObject({
  scope: z.strictObject({ type: z.string(), id: z.string(), name: z.string() }),
  nodes: z.array(
    z.strictObject({
      id: z.string(),
      type: graphNodeType,
      label: z.string(),
      status: z.string().optional(),
      metadata: metadata.optional(),
    }),
  ),
  edges: z.array(
    z.strictObject({
      source: z.string(),
      target: z.string(),
      type: graphEdgeType,
      metadata: metadata.optional(),
    }),
  ),
});

/* ---------- simulation (8.7) ---------- */

const simulationStateSchema = z.strictObject({
  continuity_risk_index: riskIndex,
  continuity_risk_class: continuityRiskClass,
  critical_gap_count: count,
  degraded_capability_count: count,
  covered_capability_count: count,
});

export const simulationResponseSchema = z.strictObject({
  simulation_id: z.string(),
  simulation_type: simulationType,
  engineer: z.strictObject({ engineer_id: z.string(), name: z.string() }),
  scope: z.strictObject({ type: simulationScopeType, id: z.string(), name: z.string() }),
  before: simulationStateSchema,
  after: simulationStateSchema,
  capability_impacts: z.array(
    z.strictObject({
      capability_id: z.string(),
      name: z.string(),
      operational_criticality: operationalCriticality,
      before: capabilityExposure,
      after: capabilityExposure,
      remaining_best_readiness: readinessLevel,
    }),
  ),
  summary: z.string().nullable().optional(),
});

/* ---------- backup candidates (8.8) ---------- */

export const backupCandidateResponseSchema = z.strictObject({
  capability: capabilityRefSchema,
  candidates: z.array(
    z.strictObject({
      engineer_id: z.string(),
      name: z.string(),
      technical_overlap: technicalOverlap,
      strengths: z.array(z.string()),
      gaps: z.array(z.string()),
      evidence_confidence: evidenceConfidence,
      supporting_evidence_ids: z.array(z.string()).optional(),
    }),
  ),
  message: z.string().nullable().optional(),
  disclaimer: z.string(),
});

/* ---------- mitigation (8.9, 8.10) ---------- */

export const mitigationTaskSchema = z.strictObject({
  task_id: z.string(),
  title: z.string(),
  description: z.string(),
  type: mitigationTaskType,
  acceptance_criteria: z.array(z.string()).optional(),
  linked_evidence_ids: z.array(z.string()).optional(),
});

export const mitigationPlanResponseSchema = z.strictObject({
  plan_id: z.string(),
  status: mitigationPlanStatus,
  capability: capabilityRefSchema,
  source_engineer: z.strictObject({ engineer_id: z.string(), name: z.string() }),
  backup_candidate: z.strictObject({ engineer_id: z.string(), name: z.string() }),
  target_readiness: readinessLevel,
  tasks: z.array(mitigationTaskSchema),
});

export const approvePlanResponseSchema = z.strictObject({
  plan_id: z.string(),
  status: mitigationPlanStatus,
  approved_by: z.string(),
  approved_at: isoDateTime,
});

/* ---------- challenge (endpoint 11, DEC-10) ---------- */

const assessmentSnapshotSchema = z.strictObject({
  exposure: capabilityExposure,
  continuity_risk_index: riskIndex.nullable().optional(),
  continuity_risk_class: continuityRiskClass.nullable().optional(),
  evidence_confidence: evidenceConfidence,
  readiness: readinessLevel.nullable().optional(),
  rules_triggered: z.array(z.string()).optional(),
});

const systemSnapshotSchema = z.strictObject({
  continuity_risk_index: riskIndex.nullable().optional(),
  continuity_risk_class: continuityRiskClass.nullable().optional(),
  exposure: capabilityExposure,
  critical_gap_count: count,
  degraded_capability_count: count,
  covered_capability_count: count,
});

export const challengeResponseSchema = z.strictObject({
  challenge_id: z.string(),
  challenge_type: challengeType,
  capability_id: z.string(),
  engineer_id: z.string().nullable().optional(),
  submitted_by: z.string(),
  submitted_at: isoDateTime,
  evidence_created: z.string().nullable().optional(),
  evidence_moved: z.string().nullable().optional(),
  capability_before: assessmentSnapshotSchema,
  capability_after: assessmentSnapshotSchema,
  system_before: systemSnapshotSchema,
  system_after: systemSnapshotSchema,
  recomputed: z.boolean(),
});

/* ---------- fixture coverage map (the contract-lock test drives this) ---------- */

export const fixtureSchemas = {
  'platforms': platformListResponseSchema,
  'payments-systems': systemListResponseSchema,
  'identity-systems': systemListResponseSchema,
  'payment-gateway': systemDetailSchema,
  'payment-gateway-graph': graphResponseSchema,
  'incident-recovery': capabilityDetailSchema,
  'incident-recovery-evidence': evidenceResponseSchema,
  'alex-simulation': simulationResponseSchema,
  'backup-candidates': backupCandidateResponseSchema,
  'mitigation-plan': mitigationPlanResponseSchema,
  'mitigation-plan-approved': approvePlanResponseSchema,
  'challenge-attest-jordan': challengeResponseSchema,
} as const;
