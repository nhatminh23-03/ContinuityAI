/**
 * TypeScript mirror of docs/API_CONTRACT.md.
 *
 * Enum values and field names are frozen. Changing one is a Category C decision
 * requiring both developers and an entry in docs/DECISIONS.md.
 *
 * The frontend renders these values. It never recomputes readiness, exposure,
 * continuity risk, risk class, evidence confidence, or technical overlap.
 */

/* ---------- enums (contract section 5) ---------- */

export type BusinessCriticality = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type OperationalCriticality = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type ReadinessLevel =
  | 'NONE'
  | 'EXPOSED'
  | 'ASSISTED'
  | 'PRACTICED'
  | 'VALIDATED';

export type CapabilityExposure =
  | 'COVERED'
  | 'DEGRADED'
  | 'CRITICAL_GAP'
  | 'INSUFFICIENT_EVIDENCE';

export type ContinuityRiskClass = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
export type EvidenceStrength = 'WEAK' | 'MODERATE' | 'STRONG';
export type EvidenceConfidence = 'LOW' | 'MEDIUM' | 'HIGH';
export type Freshness = 'FRESH' | 'AGING' | 'STALE';

export type KnowledgeDriftStatus =
  | 'NEW_RISK'
  | 'RISK_INCREASED'
  | 'STABLE'
  | 'RISK_REDUCED';

export type EvidenceSourceType =
  | 'COMMIT'
  | 'PULL_REQUEST'
  | 'CODE_REVIEW'
  | 'ISSUE'
  | 'TICKET'
  | 'INCIDENT'
  | 'DOCUMENT'
  | 'TECHNICAL_DISCUSSION'
  | 'MANAGER_ATTESTATION';

export type EvidenceRole =
  | 'EXPOSURE'
  | 'CONTRIBUTION'
  | 'ASSISTED_EXECUTION'
  | 'INDEPENDENT_EXECUTION'
  | 'KNOWLEDGE_CAPTURE';

export type GraphNodeType =
  | 'PLATFORM'
  | 'SYSTEM'
  | 'COMPONENT'
  | 'CAPABILITY'
  | 'ENGINEER'
  | 'EVIDENCE';

export type GraphEdgeType =
  | 'HAS_SYSTEM'
  | 'HAS_COMPONENT'
  | 'REQUIRES_CAPABILITY'
  | 'DEMONSTRATES'
  | 'SUPPORTED_BY'
  | 'DECLARED_OWNER';

export type SimulationType = 'ENGINEER_UNAVAILABLE';
export type SimulationScopeType = 'SYSTEM' | 'PLATFORM';
export type TechnicalOverlap = 'LOW' | 'MEDIUM' | 'HIGH';
export type MitigationPlanStatus = 'DRAFT' | 'APPROVED';

export type MitigationTaskType =
  | 'KNOWLEDGE_REVIEW'
  | 'SHADOWING'
  | 'PRACTICE'
  | 'RECOVERY_DRILL'
  | 'DOCUMENTATION'
  | 'ARCHITECTURE_REVIEW';

export type CriticalitySource = 'HUMAN_CONFIRMED' | 'AI_SUGGESTED';

/** How a manager disputes an assessment. Every value is an evidence operation,
 *  never an outcome — scores change because evidence changes (DEC-10). */
export type ChallengeType =
  | 'LINK_EVIDENCE'
  | 'MANAGER_ATTESTATION'
  | 'CORRECT_CAPABILITY_MAPPING';

export type ErrorCode =
  | 'NOT_FOUND'
  | 'VALIDATION_ERROR'
  /** Only reachable when the backend has API_TOKEN configured (DEC-13). */
  | 'UNAUTHORIZED'
  | 'INSUFFICIENT_EVIDENCE'
  | 'AI_EXTRACTION_FAILED'
  | 'GRAPH_INCONSISTENCY'
  | 'SIMULATION_FAILED'
  | 'MITIGATION_GENERATION_FAILED'
  | 'INTERNAL_ERROR';

/* ---------- error envelope (contract section 9) ---------- */

export interface ApiErrorBody {
  code: ErrorCode;
  message: string;
  details?: Record<string, unknown>;
}

export interface ApiErrorResponse {
  error: ApiErrorBody;
}

/* ---------- platforms (contract 6.1, 8.1) ---------- */

export interface PlatformSummary {
  platform_id: string;
  name: string;
  description: string | null;
  system_count: number;
  critical_gap_count: number;
  /**
   * Capabilities resting on exactly one adequate engineer — "one person away from a gap".
   * Not derivable from `degraded_capability_count`, which also counts capabilities with no
   * adequate engineer at all (DEC-07). Contract 6.1, added by DEC-17.
   */
  single_expert_dependency_count: number;
  /** Highest system risk. The MVP calculates no platform-level score. */
  highest_system_risk_index: number | null;
  drift_status: KnowledgeDriftStatus;
}

export interface PlatformListResponse {
  platforms: PlatformSummary[];
}

export interface PlatformRef {
  platform_id: string;
  name: string;
}

/* ---------- systems (contract 6.2, 6.3, 8.2, 8.3) ---------- */

export interface SystemSummary {
  system_id: string;
  platform_id: string;
  name: string;
  description: string | null;
  business_criticality: BusinessCriticality;
  continuity_risk_index: number | null;
  continuity_risk_class: ContinuityRiskClass | null;
  exposure: CapabilityExposure;
  evidence_confidence: EvidenceConfidence;
  critical_gap_count: number;
  degraded_capability_count: number;
  covered_capability_count: number;
  insufficient_evidence_count: number;
  drift_status: KnowledgeDriftStatus;
}

export interface SystemListResponse {
  platform: PlatformRef;
  systems: SystemSummary[];
}

export interface ComponentSummary {
  component_id: string;
  name: string;
  description: string | null;
  capability_ids: string[];
}

/** Declared ownership is not demonstrated coverage. Keep both visible. */
export interface DeclaredOwnership {
  engineer_id: string;
  name: string;
  source: string;
  mismatch_detected: boolean;
}

export interface SystemDetail extends SystemSummary {
  criticality_source?: CriticalitySource;
  rules_triggered?: string[];
  declared_ownership?: DeclaredOwnership | null;
  components: ComponentSummary[];
}

/* ---------- capabilities (contract 6.4, 6.5, 8.5) ---------- */

export interface EngineerRef {
  engineer_id: string;
  name: string;
  readiness: ReadinessLevel;
}

export interface EngineerCoverage {
  engineer_id: string;
  name: string;
  readiness: ReadinessLevel;
  freshness: Freshness;
  evidence_confidence: EvidenceConfidence;
  last_demonstrated_at?: string | null;
}

export interface CapabilityRef {
  capability_id: string;
  name: string;
}

/** One adjustment behind the Continuity Risk Index. Read with the class anchor
 *  (LOW 20 · MODERATE 50 · HIGH 70 · CRITICAL 90), the deltas explain position
 *  within a band. Optional and additive (DEC-11). */
export interface IndexModifier {
  code: string;
  delta: number;
}

export interface CapabilityDetail {
  capability_id: string;
  component_id: string;
  system_id: string;
  name: string;
  description: string;
  operational_criticality: OperationalCriticality;
  exposure: CapabilityExposure;
  continuity_risk_index: number | null;
  continuity_risk_class: ContinuityRiskClass | null;
  evidence_confidence: EvidenceConfidence;
  /** Machine-readable rule reason codes. The frontend owns the display copy. */
  rules_triggered?: string[];
  index_modifiers?: IndexModifier[];
  primary_engineer: EngineerRef | null;
  best_remaining_coverage: EngineerRef | null;
  engineer_coverage: EngineerCoverage[];
}

/* ---------- evidence (contract 6.7, 8.6) ---------- */

export interface Provenance {
  source: string;
  record_id: string;
  source_url?: string | null;
}

export interface EvidenceRecord {
  evidence_id: string;
  source_type: EvidenceSourceType;
  source_reference: string;
  source_title: string | null;
  artifact_date: string;
  engineer_id: string;
  system_id: string;
  component_id: string | null;
  capability_id: string;
  evidence_role: EvidenceRole;
  evidence_strength: EvidenceStrength;
  summary: string;
  freshness: Freshness;
  provenance: Provenance;
}

/** Absence of evidence, never inability. */
export interface MissingEvidence {
  engineer_id: string;
  engineer_name: string;
  description: string;
}

export interface DeclaredVsDemonstrated {
  declared_owner: { engineer_id: string; name: string; source: string } | null;
  strongest_demonstrated_coverage: { engineer_id: string; name: string } | null;
  mismatch_detected: boolean;
}

export interface EvidenceResponse {
  capability: CapabilityRef;
  assessment: {
    exposure: CapabilityExposure;
    evidence_confidence: EvidenceConfidence;
    rules_triggered?: string[];
  };
  evidence: EvidenceRecord[];
  missing_evidence: MissingEvidence[];
  conflicting_evidence?: EvidenceRecord[];
  declared_vs_demonstrated?: DeclaredVsDemonstrated;
}

/* ---------- graph (contract 6.8-6.10, 8.4) ---------- */

export interface GraphNode {
  id: string;
  type: GraphNodeType;
  label: string;
  status?: string;
  metadata: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: GraphEdgeType;
  metadata: Record<string, unknown>;
}

export interface GraphResponse {
  scope: { type: string; id: string; name: string };
  nodes: GraphNode[];
  edges: GraphEdge[];
}

/* ---------- simulation (contract 8.7) ---------- */

export interface SimulationRequest {
  simulation_type: SimulationType;
  engineer_id: string;
  scope: { type: SimulationScopeType; id: string };
}

export interface SimulationState {
  continuity_risk_index: number;
  continuity_risk_class: ContinuityRiskClass;
  critical_gap_count: number;
  degraded_capability_count: number;
  covered_capability_count: number;
}

export interface CapabilityImpact {
  capability_id: string;
  name: string;
  operational_criticality: OperationalCriticality;
  before: CapabilityExposure;
  after: CapabilityExposure;
  remaining_best_readiness: ReadinessLevel;
}

export interface SimulationResponse {
  simulation_id: string;
  simulation_type: SimulationType;
  engineer: { engineer_id: string; name: string };
  scope: { type: SimulationScopeType; id: string; name: string };
  before: SimulationState;
  after: SimulationState;
  capability_impacts: CapabilityImpact[];
  summary: string | null;
}

/* ---------- backup candidates (contract 8.8) ---------- */

export interface BackupCandidateRequest {
  simulation_id?: string;
  capability_id: string;
  limit?: 1 | 2 | 3;
}

export interface BackupCandidate {
  engineer_id: string;
  name: string;
  technical_overlap: TechnicalOverlap;
  strengths: string[];
  gaps: string[];
  evidence_confidence: EvidenceConfidence;
  supporting_evidence_ids: string[];
}

export interface BackupCandidateResponse {
  capability: CapabilityRef;
  candidates: BackupCandidate[];
  message?: string;
  disclaimer: string;
}

/* ---------- mitigation (contract 8.9, 8.10) ---------- */

export interface MitigationPlanRequest {
  capability_id: string;
  primary_engineer_id: string;
  selected_backup_engineer_id: string;
  simulation_id?: string;
}

export interface MitigationTask {
  task_id: string;
  title: string;
  description: string;
  type: MitigationTaskType;
  acceptance_criteria: string[];
  linked_evidence_ids?: string[];
}

export interface MitigationPlanResponse {
  plan_id: string;
  status: MitigationPlanStatus;
  capability: CapabilityRef;
  source_engineer: { engineer_id: string; name: string };
  backup_candidate: { engineer_id: string; name: string };
  target_readiness: ReadinessLevel;
  tasks: MitigationTask[];
}

/** `tasks` carries manager edits made before approval. Omit to approve as generated. */
export interface ApprovePlanRequest {
  approved_by: string;
  tasks?: MitigationTask[];
}

export interface ApprovePlanResponse {
  plan_id: string;
  status: MitigationPlanStatus;
  approved_by: string;
  approved_at: string;
}

/* ---------- challenge (endpoint 11, DEC-10) ---------- */

/**
 * The manager supplies evidence or a correction — there is deliberately no
 * field for a readiness level, exposure, confidence, or risk index.
 */
export interface ChallengeRequest {
  challenge_type: ChallengeType;
  submitted_by: string;
  comment: string;
  /** LINK_EVIDENCE and MANAGER_ATTESTATION: the engineer whose coverage is concerned. */
  engineer_id?: string;
  /** LINK_EVIDENCE: the artifact extraction missed, by source reference (e.g. "INC-221"). */
  source_reference?: string;
  /** MANAGER_ATTESTATION: the claimed role. Capped at MODERATE strength server-side. */
  evidence_role?: EvidenceRole;
  /** CORRECT_CAPABILITY_MAPPING: the record to move. */
  evidence_id?: string;
  target_capability_id?: string;
}

/** A capability assessment at a point in time, for before/after of a recompute. */
export interface AssessmentSnapshot {
  exposure: CapabilityExposure;
  continuity_risk_index?: number | null;
  continuity_risk_class?: ContinuityRiskClass | null;
  evidence_confidence: EvidenceConfidence;
  readiness?: ReadinessLevel | null;
  rules_triggered?: string[];
}

export interface SystemSnapshot {
  continuity_risk_index?: number | null;
  continuity_risk_class?: ContinuityRiskClass | null;
  exposure: CapabilityExposure;
  critical_gap_count: number;
  degraded_capability_count: number;
  covered_capability_count: number;
}

export interface ChallengeResponse {
  challenge_id: string;
  challenge_type: ChallengeType;
  capability_id: string;
  engineer_id?: string;
  submitted_by: string;
  submitted_at: string;
  /** What actually changed in the evidence layer. */
  evidence_created?: string | null;
  evidence_moved?: string | null;
  /** The recomputation, reported rather than requested. */
  capability_before: AssessmentSnapshot;
  capability_after: AssessmentSnapshot;
  system_before: SystemSnapshot;
  system_after: SystemSnapshot;
  recomputed: boolean;
}
