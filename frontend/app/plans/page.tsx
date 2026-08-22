'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { EngineerBadge } from '@/components/people';
import { PlanStatusChip } from '@/features/mitigation/PlanView';
import { TaskCard } from '@/features/mitigation/TaskCard';
import { loadPlan, type StoredPlan } from '@/features/mitigation/planStore';

/**
 * The session's plan. Plans have no list or read-back endpoint in the
 * frozen contract (GAP-02), so this renders what the session holds — and
 * says so rather than pretending to be an archive.
 */
export default function PlansPage() {
  const [stored, setStored] = useState<StoredPlan | null | 'loading'>('loading');

  useEffect(() => {
    setStored(loadPlan());
  }, []);

  if (stored === 'loading') {
    return (
      <div className="mx-auto max-w-4xl py-6">
        <div className="frosted-card h-40 skeleton" />
      </div>
    );
  }

  if (!stored) {
    return (
      <div className="mx-auto max-w-4xl py-6">
        <h1 className="text-4xl font-medium tracking-tight text-slate-900">Plans</h1>
        <div className="frosted-card mt-8 p-8 text-center">
          <p className="text-sm font-medium text-slate-700">No plan in this session yet.</p>
          <p className="mt-1 text-sm text-slate-500">
            Plans are generated from a capability&apos;s backup comparison after a simulation.
          </p>
          <Link
            href="/"
            className="motion-press mt-5 inline-block rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Go to the dashboard
          </Link>
        </div>
      </div>
    );
  }

  const { plan, approval } = stored;

  return (
    <div className="mx-auto max-w-4xl py-6">
      <h1 className="text-4xl font-medium tracking-tight text-slate-900">Plans</h1>
      <p className="mt-2 text-[15px] text-slate-600">This session&apos;s plan.</p>

      <div className="frosted-card mt-8 p-6">
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="text-lg font-medium text-slate-900">
            Knowledge transfer — {plan.capability.name}
          </h2>
          <PlanStatusChip status={plan.status} />
        </div>
        <div className="mt-4 flex flex-wrap gap-8">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Developing
            </div>
            <div className="mt-1.5">
              <EngineerBadge name={plan.backup_candidate.name} />
            </div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Knowledge source
            </div>
            <div className="mt-1.5">
              <EngineerBadge name={plan.source_engineer.name} />
            </div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Target readiness
            </div>
            <div className="mt-2 text-sm font-medium text-slate-900">{plan.target_readiness}</div>
          </div>
        </div>
        {approval ? (
          <p className="mt-4 rounded-xl bg-white/50 px-3 py-2 text-xs text-slate-600">
            Approved by {approval.approved_by} · {approval.approved_at}
          </p>
        ) : null}
      </div>

      <div className="motion-stagger mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
        {plan.tasks.map((task, index) => (
          <TaskCard key={task.task_id} index={index} task={task} editable={false} />
        ))}
      </div>
    </div>
  );
}
