'use client';

import { useEffect, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import type { ApprovePlanResponse, MitigationTask } from '@/types/api';
import { approverCopy, formatApprovedAt, PLAN_COPY, PLAN_STATUS_COPY, READINESS_COPY } from '@/lib/copy';
import { api } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';
import Link from 'next/link';
import { EngineerBadge } from '@/components/people';
import { loadPlan, saveApproval, savePlan } from './planStore';
import { TaskCard } from './TaskCard';

export function PlanStatusChip({ status }: { status: 'DRAFT' | 'APPROVED' }) {
  return status === 'DRAFT' ? (
    <span className="glass-chip rounded-full bg-white/40 px-2.5 py-0.5 text-xs font-semibold text-slate-600">
      {PLAN_STATUS_COPY.DRAFT}
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 rounded-full bg-slate-900 px-2.5 py-0.5 text-xs font-semibold text-white">
      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" className="h-3 w-3" aria-hidden>
        <path d="m3.5 8.5 3 3 6-6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      {PLAN_STATUS_COPY.APPROVED}
    </span>
  );
}

/**
 * Generate → edit → approve. The manager can edit every task before
 * approval; edited tasks are submitted with the approve call (CI-12). The
 * post-approval state renders from session state — there is no read-back
 * endpoint (GAP-02).
 */
export function PlanView({
  capabilityId,
  primaryEngineerId,
  backupEngineerId,
  simulationId,
  systemId,
}: {
  capabilityId: string;
  primaryEngineerId: string;
  backupEngineerId: string;
  simulationId?: string;
  /** Absent on a bare deep link; only the return links depend on it. */
  systemId?: string;
}) {
  const planQuery = useQuery({
    queryKey: ['mitigation-plan', capabilityId, primaryEngineerId, backupEngineerId, simulationId],
    queryFn: () =>
      api.createMitigationPlan({
        capability_id: capabilityId,
        primary_engineer_id: primaryEngineerId,
        selected_backup_engineer_id: backupEngineerId,
        simulation_id: simulationId,
      }),
    staleTime: Infinity,
    // This "query" is a POST that creates a row. A retry would create a second
    // plan for the same request, and garbage collection followed by a revisit
    // would create a third, orphaning the first.
    retry: false,
    gcTime: Infinity,
  });

  // Null until the manager edits something, so the rendered list falls through
  // to the server's tasks. Previously an effect copied them into state, which
  // painted one frame of an empty grid between the skeleton and the content.
  const [editedTasks, setEditedTasks] = useState<MitigationTask[] | null>(null);
  const [approval, setApproval] = useState<ApprovePlanResponse | null>(null);

  useEffect(() => {
    if (!planQuery.data) return;
    savePlan(planQuery.data);
    // Revisiting a plan approved earlier in the session: the approve response is
    // not readable back from the API (GAP-02), so it is rehydrated from the
    // store rather than the screen reverting to a draft.
    const stored = loadPlan();
    if (stored?.approval && stored.plan.plan_id === planQuery.data.plan_id) {
      setApproval(stored.approval);
      setEditedTasks(stored.plan.tasks);
    }
  }, [planQuery.data]);

  const approveMutation = useMutation({
    mutationFn: (finalTasks: MitigationTask[] | null) =>
      api.approveMitigationPlan(planQuery.data?.plan_id ?? '', {
        approved_by: 'eng_manager_sarah',
        ...(finalTasks ? { tasks: finalTasks } : {}),
      }),
    onSuccess: (response, finalTasks) => {
      setApproval(response);
      saveApproval(response, finalTasks ?? planQuery.data?.tasks ?? []);
    },
  });

  if (planQuery.isPending) {
    return (
      <div className="space-y-4">
        <div className="text-sm text-slate-600">Generating the transfer plan…</div>
        <div className="frosted-card h-24 skeleton" />
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="frosted-card h-56 skeleton" />
          <div className="frosted-card h-56 skeleton" />
        </div>
      </div>
    );
  }

  if (planQuery.isError) {
    return (
      <div className="frosted-card p-6 text-sm text-slate-600">
        The plan could not be generated.
        <span className="mt-1 block text-xs text-slate-500">
          {planQuery.error instanceof ApiError ? `Error code: ${planQuery.error.code}` : ''}
        </span>
      </div>
    );
  }

  const plan = planQuery.data;
  const tasks = editedTasks ?? plan.tasks;
  const edited = editedTasks !== null;
  const status = approval?.status ?? plan.status;

  const candidatesHref = systemId
    ? `/systems/${systemId}/candidates?capability=${capabilityId}${
        simulationId ? `&simulation=${simulationId}` : ''
      }`
    : null;

  return (
    <div>
      {candidatesHref && status === 'DRAFT' ? (
        <Link
          href={candidatesHref}
          className="mb-3 inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 hover:underline"
        >
          <span aria-hidden>‹</span>
          Choose a different backup
        </Link>
      ) : null}
      <div className="frosted-card p-6">
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="text-lg font-medium text-slate-900">
            Knowledge transfer — {plan.capability.name}
          </h2>
          <PlanStatusChip status={status} />
        </div>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
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
            <div className="mt-2 text-sm font-medium text-slate-900">
              {READINESS_COPY[plan.target_readiness]}
              <span className="ml-1.5 text-xs font-normal text-slate-500">
                (target, not achieved)
              </span>
            </div>
          </div>
        </div>
        {approval ? (
          <p className="mt-4 rounded-xl bg-white/50 px-3 py-2 text-xs text-slate-600">
            Approved by {approverCopy(approval.approved_by)} ·{' '}
            {formatApprovedAt(approval.approved_at)}
          </p>
        ) : null}
      </div>

      {tasks.length === 0 ? (
        <div className="frosted-card mt-6 p-6 text-sm text-slate-600">{PLAN_COPY.empty}</div>
      ) : (
        <>
          <p className="mt-6 text-xs text-slate-600">{PLAN_COPY.ordered}</p>
          {/* One column, in order. A two-column grid presented the tasks as peers
              doable in any order, but each one depends on the last — shadowing
              before an unaided drill, the drill before writing up its gaps. */}
          <ol className="motion-stagger mt-3 space-y-4">
            {tasks.map((task, index) => (
              <TaskCard
                key={task.task_id}
                index={index}
                total={tasks.length}
                task={task}
                editable={status === 'DRAFT'}
                onChange={(nextTask) =>
                  setEditedTasks((current) =>
                    (current ?? plan.tasks).map((t) =>
                      t.task_id === nextTask.task_id ? nextTask : t,
                    ),
                  )
                }
              />
            ))}
          </ol>
        </>
      )}

      {status === 'DRAFT' && tasks.length > 0 ? (
        <div className="mt-6 flex flex-wrap items-center justify-end gap-x-4 gap-y-2">
          {approveMutation.isError ? (
            <span className="text-xs text-slate-600">
              {approveMutation.error instanceof ApiError &&
              approveMutation.error.code === 'VALIDATION_ERROR'
                ? 'Only a draft plan can be approved.'
                : 'The approval could not be submitted.'}
            </span>
          ) : null}
          <p className="max-w-md text-xs leading-relaxed text-slate-500">
            {PLAN_COPY.humanGate} {PLAN_COPY.approveNote}
          </p>
          <button
            type="button"
            disabled={approveMutation.isPending}
            onClick={() => approveMutation.mutate(edited ? tasks : null)}
            className="motion-press rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          >
            {approveMutation.isPending ? 'Approving…' : 'Approve plan'}
          </button>
        </div>
      ) : (
        <div className="frosted-card motion-rise mt-6 flex flex-wrap items-center justify-between gap-4 p-5">
          <div className="flex items-center gap-3">
            <span
              aria-hidden
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-900 text-white"
            >
              <svg
                viewBox="0 0 16 16"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="h-4 w-4"
              >
                <path d="m3.5 8.5 3 3 6-6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </span>
            <div>
              <div className="text-sm font-medium text-slate-900">Plan approved</div>
              <div className="text-xs text-slate-500">
                {approval
                  ? `Approved by ${approverCopy(approval.approved_by)} · ${formatApprovedAt(approval.approved_at)}`
                  : 'This plan has already been approved.'}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {systemId ? (
              <Link
                href={`/systems/${systemId}`}
                className="motion-press rounded-xl px-4 py-2 text-sm font-medium text-slate-600 hover:bg-white/50 hover:text-slate-900"
              >
                Back to the system
              </Link>
            ) : null}
            <Link
              href="/plans"
              className="motion-press rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
            >
              View all plans
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
