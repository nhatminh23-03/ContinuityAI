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

export function savePlan(plan: MitigationPlanResponse, storage = defaultStorage()): void {
  storage?.setItem(KEY, JSON.stringify({ plan } satisfies StoredPlan));
}

export function loadPlan(storage = defaultStorage()): StoredPlan | null {
  const raw = storage?.getItem(KEY);
  if (!raw) return null;
  try {
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
  storage.setItem(KEY, JSON.stringify(next));
}
