import { describe, expect, it } from 'vitest';
import type { ApprovePlanResponse, MitigationPlanResponse } from '../types/api';
import { loadPlan, saveApproval, savePlan } from '../features/mitigation/planStore';

function memoryStorage() {
  const map = new Map<string, string>();
  return {
    getItem: (key: string) => map.get(key) ?? null,
    setItem: (key: string, value: string) => void map.set(key, value),
  };
}

const plan: MitigationPlanResponse = {
  plan_id: 'plan_001',
  status: 'DRAFT',
  capability: { capability_id: 'cap_incident_recovery', name: 'Incident Recovery' },
  source_engineer: { engineer_id: 'eng_alex_chen', name: 'Alex Chen' },
  backup_candidate: { engineer_id: 'eng_maria_gomez', name: 'Maria Gomez' },
  target_readiness: 'PRACTICED',
  tasks: [
    {
      task_id: 'task_001',
      title: 'Review architecture',
      description: 'Review the recovery architecture.',
      type: 'KNOWLEDGE_REVIEW',
      acceptance_criteria: ['Record unanswered questions'],
      linked_evidence_ids: ['evidence_inc_184'],
    },
  ],
};

const approval: ApprovePlanResponse = {
  plan_id: 'plan_001',
  status: 'APPROVED',
  approved_by: 'eng_manager_sarah',
  approved_at: '2026-08-17T12:00:00Z',
};

describe('planStore', () => {
  it('round-trips a plan', () => {
    const storage = memoryStorage();
    savePlan(plan, storage);
    expect(loadPlan(storage)).toEqual({ plan });
  });

  it('merges an approval with the final task list', () => {
    const storage = memoryStorage();
    savePlan(plan, storage);
    const editedTasks = [{ ...plan.tasks[0], title: 'Review architecture (edited)' }];
    saveApproval(approval, editedTasks, storage);
    const stored = loadPlan(storage);
    expect(stored?.approval).toEqual(approval);
    expect(stored?.plan.status).toBe('APPROVED');
    expect(stored?.plan.tasks[0].title).toBe('Review architecture (edited)');
  });

  it('returns null when nothing is stored', () => {
    expect(loadPlan(memoryStorage())).toBeNull();
  });
});
