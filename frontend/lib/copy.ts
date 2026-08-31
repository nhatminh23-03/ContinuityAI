/**
 * Frontend-owned display copy for machine-readable codes.
 *
 * The API sends reason codes, enum values and modifier codes; the wording here
 * is the jointly-reviewable surface (ENGINEERING_RULES.md: display copy lives in
 * the frontend). Keep every line descriptive, never evaluative: a code describes
 * what the evidence shows, not what anyone is worth.
 *
 * PRD §22.3 governs every string below — a gap expresses the absence of
 * evidence, never a person's inability.
 *
 * This file is the single home for user-facing wording. Components import from
 * here rather than inlining labels, so the whole vocabulary can be reviewed in
 * one place and the same concept never gets two names on two screens.
 */

import type {
  CapabilityExposure,
  EvidenceConfidence,
  MitigationPlanStatus,
  OperationalCriticality,
  ContinuityRiskClass,
  EvidenceRole,
  EvidenceStrength,
  Freshness,
  KnowledgeDriftStatus,
  ReadinessLevel,
} from '@/types/api';

/** Capability- and system-level rule reason codes (closed list owned by the backend). */
export const RULE_COPY: Record<string, string> = {
  // capability-level
  CRITICAL_CAPABILITY: 'Business-critical capability',
  HIGH_CAPABILITY: 'High-importance capability',
  NO_PRACTICED_OR_VALIDATED_COVERAGE: 'No engineer has demonstrated this unaided',
  SINGLE_VALIDATED_ENGINEER: 'One engineer has repeatedly demonstrated this',
  SINGLE_PRACTICED_ENGINEER: 'One engineer has demonstrated this once',
  NO_PRACTICED_OR_VALIDATED_BACKUP: 'No second engineer has demonstrated it',
  ADEQUATE_BACKUP_PRESENT: 'More than one engineer has demonstrated this',
  INSUFFICIENT_EVIDENCE: 'Not enough evidence for a responsible assessment',
  LOW_EVIDENCE_CONFIDENCE: 'Supporting evidence is thin or single-source',
  CONFLICTING_EVIDENCE: 'Sources disagree; human review recommended',
  STALE_ADEQUATE_COVERAGE: 'The only hands-on evidence has gone stale',
  MISSING_RUNBOOK: 'No runbook exists for this capability',
  INCOMPLETE_RUNBOOK: 'The runbook is incomplete',
  CURRENT_RUNBOOK: 'The runbook is current',
  // system-level
  CRITICAL_CAPABILITY_GAP: 'A business-critical capability has no adequate coverage',
  HIGH_CAPABILITY_GAP: 'A high-importance capability has no adequate coverage',
  CRITICAL_CAPABILITY_DEGRADED: 'A business-critical capability lacks a resilient backup',
  HIGH_CAPABILITY_DEGRADED: 'A high-importance capability lacks a resilient backup',
  SOLE_EXPERT_CAPABILITY: 'A capability depends on a single expert',
  MULTIPLE_SOLE_EXPERT_CAPABILITIES: 'Multiple capabilities depend on a single expert',
  INSUFFICIENT_EVIDENCE_PRESENT: 'Some capabilities lack enough evidence to assess',
};

/** Index-modifier codes (DEC-11) — the arithmetic behind the index. */
export const MODIFIER_COPY: Record<string, string> = {
  SOLE_ADEQUATE_ENGINEER: 'Only one engineer has demonstrated this',
  BEST_ALTERNATIVE_ASSISTED: 'The next-strongest engineer has only assisted',
  BEST_ALTERNATIVE_EXPOSED_OR_NONE: 'No alternative engineer has hands-on evidence',
  SECOND_PRACTICED_ENGINEER: 'A second engineer has demonstrated this',
  SECOND_VALIDATED_ENGINEER: 'A second engineer has repeatedly demonstrated this',
  RUNBOOK_MISSING: 'No runbook exists',
  RUNBOOK_INCOMPLETE: 'The runbook is incomplete',
  RUNBOOK_CURRENT: 'The runbook is current',
};

/**
 * Capability coverage state.
 *
 * The API calls this field `exposure`, which is the organisation's exposure to
 * losing the capability. Three unrelated things in this contract are spelled
 * "exposure" — this field, the `EXPOSED` readiness level, and the `EXPOSURE`
 * evidence role — and they mean different, in one case nearly opposite, things.
 * The enum values are frozen; the words a manager reads are not, so each of the
 * three is named for what it actually describes and the word itself is retired
 * from the interface.
 */
export const EXPOSURE_COPY: Record<CapabilityExposure, string> = {
  COVERED: 'Covered',
  DEGRADED: 'No resilient backup',
  CRITICAL_GAP: 'No proven coverage',
  INSUFFICIENT_EVIDENCE: 'Not enough evidence',
};

/**
 * The same enum is also carried by a system, where ENGINEERING_RULES.md line 250
 * defines it as the worst of that system's capabilities — not a property of the
 * system. Refund Engine reports CRITICAL_GAP while four of its five capabilities
 * are covered, so the capability wording above would state, unqualified, that a
 * system with proven coverage has none. The old label "Critical gap" survived
 * this because a state name asserts nothing; a sentence does. These say whose
 * state is being reported.
 */
export const SYSTEM_EXPOSURE_COPY: Record<CapabilityExposure, string> = {
  COVERED: 'All covered',
  DEGRADED: 'Worst: no resilient backup',
  CRITICAL_GAP: 'Worst: no proven coverage',
  INSUFFICIENT_EVIDENCE: 'Worst: not enough evidence',
};

/**
 * What the evidence shows an engineer has done. Never a rating of the person,
 * and never a ranking — the ladder is ordinal about *demonstrated activity*, and
 * the absence of evidence is stated as exactly that.
 */
export const READINESS_COPY: Record<ReadinessLevel, string> = {
  NONE: 'No evidence',
  EXPOSED: 'Reviewed or discussed',
  ASSISTED: 'Helped with support',
  PRACTICED: 'Done independently',
  VALIDATED: 'Proven repeatedly',
};

/**
 * Compact readiness words for dense summaries — the capability list packs a
 * whole coverage tally onto one line, where the full phrases would not fit.
 * Same meanings, and "exposed" is still retired: it is the one word in this
 * contract that means two opposite things.
 */
export const READINESS_SHORT_COPY: Record<ReadinessLevel, string> = {
  NONE: 'no evidence',
  EXPOSED: 'reviewed',
  ASSISTED: 'assisted',
  PRACTICED: 'independent',
  VALIDATED: 'proven',
};

export const DRIFT_COPY: Record<KnowledgeDriftStatus, string> = {
  NEW_RISK: 'Newly at risk',
  RISK_INCREASED: 'Getting riskier',
  STABLE: 'No change',
  RISK_REDUCED: 'Improving',
};

/** What an engineer did in one artifact. Describes the act, not the actor. */
export const EVIDENCE_ROLE_COPY: Record<EvidenceRole, string> = {
  EXPOSURE: 'Reviewed or discussed it',
  CONTRIBUTION: 'Contributed to it',
  ASSISTED_EXECUTION: 'Did it with support',
  INDEPENDENT_EXECUTION: 'Did it independently',
  KNOWLEDGE_CAPTURE: 'Wrote it down',
};

/** How much weight one artifact carries. A property of the evidence, not the engineer. */
export const EVIDENCE_STRENGTH_COPY: Record<EvidenceStrength, string> = {
  STRONG: 'Strong signal',
  MODERATE: 'Moderate signal',
  WEAK: 'Weak signal',
};

export const CONFIDENCE_COPY: Record<EvidenceConfidence, string> = {
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
};

export const FRESHNESS_COPY: Record<Freshness, string> = {
  FRESH: 'Recent',
  AGING: 'Aging',
  STALE: 'Old',
};

/** Where a record came from. Unknown sources are prettified rather than hidden. */
export const PROVENANCE_SOURCE_COPY: Record<string, string> = {
  synthetic_incident_dataset: 'Incident record',
  synthetic_document_dataset: 'Internal document',
  synthetic_issue_dataset: 'Issue tracker',
  synthetic_repository_export: 'Code repository',
  synthetic_ticket_dataset: 'Ticket system',
  synthetic_review_dataset: 'Code review',
  manager_attestation: 'Manager attestation',
};

/** Business dependence on a capability. The enum is shouted; a sentence is not. */
export const CRITICALITY_COPY: Record<OperationalCriticality, string> = {
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
  CRITICAL: 'Business-critical',
};

export const PLAN_STATUS_COPY: Record<MitigationPlanStatus, string> = {
  DRAFT: 'Draft',
  APPROVED: 'Approved',
};

/**
 * The approval gate is the one place a person's name is attached to a decision,
 * and it was printing a database key. Unknown ids fall back to the raw value
 * rather than being hidden, the same contract `ruleCopy` keeps.
 */
const APPROVER_COPY: Record<string, string> = {
  eng_manager_sarah: 'Sarah, engineering manager',
};

export function approverCopy(id: string): string {
  return APPROVER_COPY[id] ?? id;
}

/**
 * Locale and zone are pinned rather than left to the reader's machine: this
 * string is rendered during the server pass and again on hydration, and a
 * floating locale makes those two disagree.
 */
export function formatApprovedAt(iso: string): string {
  const at = new Date(iso);
  if (Number.isNaN(at.getTime())) return iso;
  return `${at.toLocaleString('en-GB', {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'UTC',
  })} UTC`;
}

/** Class anchors, display only — used to show the server's own arithmetic in
 *  the Why panel. Never used to band an index into a class. */
export const CLASS_ANCHOR: Record<ContinuityRiskClass, number> = {
  LOW: 20,
  MODERATE: 50,
  HIGH: 70,
  CRITICAL: 90,
};

/** Static simulation strings (contract decision CI-32). */
export const SIM_DISCLAIMER = 'This models coverage loss. It does not predict an outage.';
export const SIM_BANNER = 'Nothing has changed in your real data.';

/**
 * Primary action wording. The product's central question is conditional — "what
 * happens if this person is unavailable?" — so the button that asks it is
 * phrased as that question rather than as the name of the mechanism behind it.
 */
export const ACTION_COPY = {
  simulate: "What if someone's unavailable?",
  simulateShort: 'What if?',
  simulateFor: (name: string) => `What if ${name} is unavailable?`,
};

/**
 * The plan screen is the only irreversible control in the product, so it states
 * what approving does and — just as important — what it does not set in motion.
 * Phrased as absence of a mechanism, never as a prohibition.
 */
export const PLAN_COPY = {
  ordered: 'The tasks run in order — each one builds on the one before it.',
  approveNote:
    'Approving records these tasks and who approved them. Nothing is assigned, scheduled, or notified from here, and this screen offers no way to un-approve.',
  humanGate: 'A human approves every plan.',
  empty:
    'No tasks were drafted for this plan. Nothing here is ready to approve — regenerate from the backup comparison, or pick a different engineer.',
};

export const CHALLENGE_COPY = {
  addMissing: 'Add evidence',
  addMissingFor: (name: string) => `Add evidence for ${name}`,
  back: 'Back to evidence',
  intro:
    'A manager changes evidence, never a score. The assessment recomputes from what you add or correct.',
};

/**
 * The graph draws four kinds of edge and only one of them is evidence. An
 * earlier caption said "every line is recorded evidence", which was wrong about
 * the containment, requirement and declared-ownership lines — a third of them.
 */
export const GRAPH_COPY = {
  knowledgeMap:
    'Rings from the centre out: the system, its components, the capabilities each component needs, and the engineers with recorded evidence. Focusing a capability adds an outer ring of the evidence records themselves. Solid lines are demonstrated coverage, thicker the more an engineer has demonstrated; dashed lines are declared ownership and the link from a record to the engineer it supports.',
  knowledgeMapHint: 'Click a capability to focus it.',
};

/**
 * One-line explanations for the vocabulary a first-time reader meets before any
 * documentation. Rendered by InfoHint at the first place each term appears.
 */
export const HINT_COPY = {
  riskIndex:
    'A comparison number from 0 to 100 — not a probability. Higher means more capability would be lost if the people who hold it became unavailable.',
  coverage:
    'Whether the capability would survive one person becoming unavailable. It depends both on how many engineers have independently demonstrated it and on how much the business depends on it.',
  evidenceConfidence:
    'How much this assessment rests on strong, recent, multi-source evidence — not how capable anyone is.',
  drift: "How this system's continuity risk has moved since the previous assessment.",
  readiness:
    'What the recorded evidence shows an engineer has done with this capability. It is never a rating of the person.',
  technicalOverlap:
    'How much demonstrated capability this engineer already shares with the work being covered. Derived from evidence, never from workload, availability or performance.',
  criticality: 'How much the business depends on this capability being available.',
  highestSystemRisk:
    'The score of the single riskiest system inside this platform. Platforms are not scored on their own — this number belongs to one of the systems listed below.',
  platform:
    'A platform groups systems. Each system contains components, and each component needs capabilities — the level where evidence and coverage are actually assessed.',
} as const;

/** Render an unrecognised code as its raw value rather than hiding it. */
export function ruleCopy(code: string): string {
  return RULE_COPY[code] ?? code;
}

export function modifierCopy(code: string): string {
  return MODIFIER_COPY[code] ?? code;
}

/**
 * An evidence id is derived from the artifact reference it came from —
 * `evidence_inc_184` is the record for incident INC-184 — so the reference can
 * be recovered without a lookup. The plan screen cites these as the
 * justification for its opening task, and a database key is not a citation.
 * Anything that does not match the shape is left exactly as received.
 */
export function evidenceReference(evidenceId: string): string {
  const parts = evidenceId.replace(/^evidence_/, '').split('_');
  if (parts.length < 2 || !parts.every(Boolean)) return evidenceId;
  return `${parts[0].toUpperCase()}-${parts.slice(1).join('-').toUpperCase()}`;
}

/** An unmapped source still reads as words rather than as a database key. */
export function provenanceSourceCopy(source: string): string {
  const mapped = PROVENANCE_SOURCE_COPY[source];
  if (mapped) return mapped;
  const words = source.replace(/^synthetic_/, '').replaceAll('_', ' ').trim();
  return words.charAt(0).toUpperCase() + words.slice(1);
}
