'use client';

import { useState } from 'react';
import type { MitigationTask } from '@/types/api';

/**
 * One plan task. Editable while the plan is DRAFT — edits ride on the
 * approve request (contract decision CI-12). No durations, no mode chips:
 * neither is in the DTO.
 */

const TYPE_LABEL: Record<MitigationTask['type'], string> = {
  KNOWLEDGE_REVIEW: 'Knowledge review',
  SHADOWING: 'Shadowing',
  PRACTICE: 'Practice',
  RECOVERY_DRILL: 'Recovery drill',
  DOCUMENTATION: 'Documentation',
  ARCHITECTURE_REVIEW: 'Architecture review',
};

export function TaskCard({
  index,
  total,
  task,
  editable,
  onChange,
}: {
  index: number;
  total: number;
  task: MitigationTask;
  editable: boolean;
  onChange?: (task: MitigationTask) => void;
}) {
  const [editing, setEditing] = useState(false);
  // The textarea holds raw text while it is being typed. Normalising `value` on
  // every keystroke meant a trailing space was stripped before the next
  // character arrived — so no multi-word criterion could be typed — and a
  // newline was filtered away, making the "one per line" instruction below the
  // field describe the one key that did nothing. Only the lifted value is
  // normalised, so what reaches the approve payload is unchanged.
  const [criteriaDraft, setCriteriaDraft] = useState<string | null>(null);
  const criteria = task.acceptance_criteria ?? [];

  return (
    <li className="frosted-card flex flex-col p-5">
      <div className="flex items-center gap-3">
        <span
          aria-hidden
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white/70 text-xs font-semibold text-slate-700 ring-1 ring-white/60"
        >
          {index + 1}
        </span>
        <span className="sr-only">
          Step {index + 1} of {total}.
        </span>
        <span className="glass-chip rounded-full bg-white/40 px-2.5 py-0.5 text-[11px] font-semibold text-slate-600">
          {TYPE_LABEL[task.type]}
        </span>
        {editable ? (
          <button
            type="button"
            onClick={() =>
              setEditing((value) => {
                if (value) setCriteriaDraft(null);
                return !value;
              })
            }
            className="ml-auto text-xs font-medium text-slate-500 underline decoration-slate-300 underline-offset-2 hover:text-slate-900"
          >
            {editing ? 'Done' : 'Edit'}
          </button>
        ) : null}
      </div>

      {editing && onChange ? (
        <div className="mt-3 space-y-2">
          <input
            value={task.title}
            onChange={(event) => onChange({ ...task, title: event.target.value })}
            aria-label="Task title"
            className="w-full rounded-lg border border-slate-900/10 bg-white/80 px-2.5 py-1.5 text-sm font-medium text-slate-900"
          />
          <textarea
            value={task.description}
            onChange={(event) => onChange({ ...task, description: event.target.value })}
            aria-label="Task description"
            rows={3}
            className="w-full rounded-lg border border-slate-900/10 bg-white/80 px-2.5 py-1.5 text-sm text-slate-700"
          />
          <textarea
            value={criteriaDraft ?? criteria.join('\n')}
            onChange={(event) => {
              setCriteriaDraft(event.target.value);
              onChange({
                ...task,
                acceptance_criteria: event.target.value
                  .split('\n')
                  .map((line) => line.trim())
                  .filter(Boolean),
              });
            }}
            aria-label="Acceptance criteria, one per line"
            rows={3}
            className="w-full rounded-lg border border-slate-900/10 bg-white/80 px-2.5 py-1.5 text-xs text-slate-600"
          />
          <p className="text-[11px] text-slate-500">Acceptance criteria, one per line.</p>
        </div>
      ) : (
        <>
          <h3 className="mt-3 text-sm font-semibold text-slate-900">{task.title}</h3>
          <p className="mt-1.5 text-sm leading-relaxed text-slate-700">{task.description}</p>
          {criteria.length > 0 ? (
            <div className="mt-3">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                Acceptance criteria
              </div>
              <ul className="mt-1.5 space-y-1">
                {criteria.map((criterion, criterionIndex) => (
                  <li key={criterionIndex} className="flex items-start gap-2 text-xs text-slate-600">
                    <span aria-hidden className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-slate-400" />
                    {criterion}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </>
      )}

      {task.linked_evidence_ids?.length ? (
        <div className="mt-auto flex flex-wrap gap-1.5 pt-3">
          {task.linked_evidence_ids.map((evidenceId) => (
            <span
              key={evidenceId}
              className="rounded-full bg-white/50 px-2 py-0.5 text-[10px] font-medium text-slate-500 ring-1 ring-slate-900/5"
            >
              {evidenceId}
            </span>
          ))}
        </div>
      ) : null}
    </li>
  );
}
