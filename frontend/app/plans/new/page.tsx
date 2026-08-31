import Link from 'next/link';
import { PlanView } from '@/features/mitigation/PlanView';
import { FlowSteps, goldenPathSteps } from '@/components/FlowSteps';

export default async function NewPlanPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = await searchParams;
  const capability = typeof query.capability === 'string' ? query.capability : undefined;
  const backup = typeof query.backup === 'string' ? query.backup : undefined;
  const primary = typeof query.primary === 'string' ? query.primary : undefined;
  const simulation = typeof query.simulation === 'string' ? query.simulation : undefined;
  // Optional: present when the flow was entered from the backup comparison,
  // absent on a bare deep link. Only the back-links depend on it.
  const system = typeof query.system === 'string' ? query.system : undefined;

  if (!capability || !backup || !primary) {
    return (
      <div className="mx-auto max-w-3xl py-6">
        <FlowSteps steps={goldenPathSteps({ stage: 'plan', systemId: system, capabilityId: capability })} />
        <div className="frosted-card mt-4 p-6">
          <h1 className="text-lg font-medium text-slate-900">Not enough to draft a plan</h1>
          <p className="mt-2 text-sm text-slate-600">
            A plan needs a capability, a knowledge source, and a selected backup. Pick a backup on a
            capability&apos;s comparison screen and the plan is drafted from there.
          </p>
          <Link
            href={system ? `/systems/${system}` : '/'}
            className="motion-press mt-4 inline-block rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            {system ? 'Back to the system' : 'Back to the dashboard'}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl py-6">
      <FlowSteps
        steps={goldenPathSteps({
          stage: 'plan',
          systemId: system,
          capabilityId: capability,
          simulationId: simulation,
        })}
      />
      <h1 className="mt-4 text-3xl font-medium tracking-tight text-slate-900">Mitigation plan</h1>
      <p className="mt-1 text-[15px] text-slate-600">
        Review and edit the generated tasks, then approve. Edits are submitted with the approval.
      </p>
      <div className="mt-6">
        <PlanView
          capabilityId={capability}
          primaryEngineerId={primary}
          backupEngineerId={backup}
          simulationId={simulation}
          systemId={system}
        />
      </div>
    </div>
  );
}
