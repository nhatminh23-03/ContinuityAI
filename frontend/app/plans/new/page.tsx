import Link from 'next/link';
import { PlanView } from '@/features/mitigation/PlanView';

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

  if (!capability || !backup || !primary) {
    return (
      <div className="mx-auto max-w-3xl py-6">
        <div className="frosted-card p-6 text-sm text-slate-600">
          A plan needs a capability, a knowledge source, and a selected backup. Start from a{' '}
          <Link href="/" className="underline">
            capability&apos;s backup comparison
          </Link>
          .
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl py-6">
      <h1 className="text-3xl font-medium tracking-tight text-slate-900">Mitigation plan</h1>
      <p className="mt-1 text-[15px] text-slate-600">
        Review and edit the generated tasks, then approve. Edits are submitted with the approval.
      </p>
      <div className="mt-6">
        <PlanView
          capabilityId={capability}
          primaryEngineerId={primary}
          backupEngineerId={backup}
          simulationId={simulation}
        />
      </div>
    </div>
  );
}
