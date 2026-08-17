/**
 * Frontend-owned display copy for machine-readable codes.
 *
 * The API sends reason codes and modifier codes; the wording here is the
 * jointly-reviewable surface (ENGINEERING_RULES.md: display copy lives in the
 * frontend). Keep every line descriptive, never evaluative: a code describes
 * what the evidence shows, not what anyone is worth.
 */

import type { ContinuityRiskClass, KnowledgeDriftStatus } from '@/types/api';

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

export const DRIFT_COPY: Record<KnowledgeDriftStatus, string> = {
  NEW_RISK: 'Drift: new risk',
  RISK_INCREASED: 'Drift: increasing',
  STABLE: 'Drift: stable',
  RISK_REDUCED: 'Drift: improving',
};

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

/** Render an unrecognised code as its raw value rather than hiding it. */
export function ruleCopy(code: string): string {
  return RULE_COPY[code] ?? code;
}

export function modifierCopy(code: string): string {
  return MODIFIER_COPY[code] ?? code;
}
