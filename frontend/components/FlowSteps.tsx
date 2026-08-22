import Link from 'next/link';

export type FlowStepState = 'done' | 'current' | 'upcoming';

export interface FlowStep {
  label: string;
  state: FlowStepState;
  /** Only completed steps navigate. A step already taken is the only one whose
   *  destination is known — an upcoming step's parameters do not exist yet. */
  href?: string;
}

/**
 * The four stages of the golden path: system, simulation, backup comparison,
 * plan. Rendered on each screen in the flow so the manager can see where the
 * current screen sits and step back without relying on browser history.
 *
 * Nothing here enforces an order. The rail reports position; the routes remain
 * independently reachable, and each one guards its own inputs.
 */
export function FlowSteps({ steps }: { steps: FlowStep[] }) {
  return (
    <nav aria-label="Progress">
      <ol className="flex flex-wrap items-center gap-y-2">
        {steps.map((step, index) => (
          <li key={step.label} className="flex items-center">
            {index > 0 ? (
              <span aria-hidden className="mx-2 h-px w-5 shrink-0 bg-slate-900/15 sm:w-8" />
            ) : null}
            <StepBody step={step} index={index} />
          </li>
        ))}
      </ol>
    </nav>
  );
}

function StepBody({ step, index }: { step: FlowStep; index: number }) {
  const marker = (
    <span
      aria-hidden
      className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold ${
        step.state === 'upcoming'
          ? 'bg-white/60 text-slate-400 ring-1 ring-slate-900/10'
          : 'bg-slate-900 text-white'
      }`}
    >
      {step.state === 'done' ? (
        <svg
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          className="h-2.5 w-2.5"
        >
          <path d="m3.5 8.5 3 3 6-6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ) : (
        index + 1
      )}
    </span>
  );

  const label = (
    <span
      className={
        step.state === 'current'
          ? 'text-xs font-semibold text-slate-900'
          : step.state === 'done'
            ? 'text-xs font-medium text-slate-600'
            : 'text-xs font-medium text-slate-400'
      }
    >
      {step.label}
    </span>
  );

  if (step.state === 'done' && step.href) {
    return (
      <Link
        href={step.href}
        className="motion-press flex items-center gap-2 rounded-lg px-1.5 py-1 hover:bg-white/50 hover:[&>span:last-child]:text-slate-900"
      >
        {marker}
        {label}
      </Link>
    );
  }

  return (
    <span
      aria-current={step.state === 'current' ? 'step' : undefined}
      className="flex items-center gap-2 px-1.5 py-1"
    >
      {marker}
      {label}
    </span>
  );
}

const STAGE_ORDER = ['system', 'simulate', 'candidates', 'plan'] as const;
export type FlowStage = (typeof STAGE_ORDER)[number];

const STAGE_LABEL: Record<FlowStage, string> = {
  system: 'System',
  simulate: 'Simulate',
  candidates: 'Choose backup',
  plan: 'Plan & approve',
};

/**
 * Builds the rail for one screen. Back-links are emitted only where the target
 * is fully determined — without a system id there is no system to return to, so
 * the step still shows as complete but does not pretend to navigate.
 */
export function goldenPathSteps({
  stage,
  systemId,
  capabilityId,
  simulationId,
}: {
  stage: FlowStage;
  systemId?: string;
  capabilityId?: string;
  simulationId?: string;
}): FlowStep[] {
  const currentIndex = STAGE_ORDER.indexOf(stage);

  const href = (target: FlowStage): string | undefined => {
    if (!systemId) return undefined;
    if (target === 'system') return `/systems/${systemId}`;
    if (!capabilityId) return undefined;
    const params = new URLSearchParams({ capability: capabilityId });
    if (target === 'simulate') {
      params.set('simulate', '1');
      return `/systems/${systemId}?${params.toString()}`;
    }
    if (simulationId) params.set('simulation', simulationId);
    return `/systems/${systemId}/candidates?${params.toString()}`;
  };

  return STAGE_ORDER.map((target, index) => {
    const state: FlowStepState =
      index < currentIndex ? 'done' : index === currentIndex ? 'current' : 'upcoming';
    return {
      label: STAGE_LABEL[target],
      state,
      href: state === 'done' ? href(target) : undefined,
    };
  });
}
