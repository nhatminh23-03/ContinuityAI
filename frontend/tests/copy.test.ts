/**
 * Display-copy maps: frontend-owned wording for rule codes, modifiers, and
 * drift. Wording is descriptive, never evaluative, and never uses the
 * prohibited vocabulary from ENGINEERING_RULES.md.
 */

import { describe, expect, it } from 'vitest';
import { DRIFT_COPY, MODIFIER_COPY, RULE_COPY, ruleCopy } from '../lib/copy';

const PROHIBITED = /irreplaceable|critical employee|best employee|cannot|weak engineer|low-value/i;

describe('display copy maps', () => {
  it('maps known rule codes to descriptive copy', () => {
    expect(ruleCopy('SINGLE_VALIDATED_ENGINEER')).toBe(
      'One engineer has repeatedly demonstrated this',
    );
    expect(ruleCopy('CRITICAL_CAPABILITY_DEGRADED')).toBe(
      'A business-critical capability lacks a resilient backup',
    );
  });

  it('renders an unrecognised code as its raw value', () => {
    expect(ruleCopy('SOME_FUTURE_CODE')).toBe('SOME_FUTURE_CODE');
  });

  it('uses no prohibited vocabulary anywhere', () => {
    for (const value of [...Object.values(RULE_COPY), ...Object.values(MODIFIER_COPY)]) {
      expect(value).not.toMatch(PROHIBITED);
    }
  });

  it('covers all four drift values', () => {
    expect(Object.keys(DRIFT_COPY).sort()).toEqual([
      'NEW_RISK',
      'RISK_INCREASED',
      'RISK_REDUCED',
      'STABLE',
    ]);
  });
});
