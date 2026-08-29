import type { ApprovePlanResponse, MitigationPlanResponse, MitigationTask } from '@/types/api';

/**
 * Session-scoped plan state. The approve response does not echo the task
 * list and the frozen contract has no plan read-back endpoint (gap register
 * GAP-02), so the post-approval view renders from what this session holds.
 */

const KEY = 'continuityai.mitigation-plan';

type StorageLike = Pick<Storage, 'getItem' | 'setItem'>;

export interface StoredPlan {
  plan: MitigationPlanResponse;
  approval?: ApprovePlanResponse;
}

function defaultStorage(): StorageLike | null {
  return typeof window === 'undefined' ? null : window.sessionStorage;
}

/**
 * Storing the plan must not erase an approval already recorded for it. The
 * previous version wrote `{ plan }` unconditionally, and PlanView calls this
 * whenever the create query resolves — so revisiting an approved plan wiped the
 * approval, redisplayed it as a draft with a live Approve button, and then
 * failed with "Only a draft plan can be approved." Since GAP-02 leaves this
 * store as the only record of an approval, that was silent data loss.
 */
export function savePlan(plan: MitigationPlanResponse, storage = defaultStorage()): void {
  if (!storage) return;
  const existing = loadPlan(storage);
  if (existing?.approval && existing.plan.plan_id === plan.plan_id) return;
  try {
    storage.setItem(KEY, JSON.stringify({ plan } satisfies StoredPlan));
  } catch {
    // Storage can be unavailable or full; the screen still works from memory.
  }
}

export function loadPlan(storage = defaultStorage()): StoredPlan | null {
  try {
    const raw = storage?.getItem(KEY);
    if (!raw) return null;
    return JSON.parse(raw) as StoredPlan;
  } catch {
    return null;
  }
}

export function saveApproval(
  approval: ApprovePlanResponse,
  finalTasks: MitigationTask[],
  storage = defaultStorage(),
): void {
  const stored = loadPlan(storage);
  if (!stored || !storage) return;
  const next: StoredPlan = {
    plan: { ...stored.plan, status: approval.status, tasks: finalTasks },
    approval,
  };
  try {
    storage.setItem(KEY, JSON.stringify(next));
  } catch {
    // As above: a failed write costs the /plans view, not this screen.
  }
}
