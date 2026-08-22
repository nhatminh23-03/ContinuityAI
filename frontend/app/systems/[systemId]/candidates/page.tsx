import Link from 'next/link';
import { CandidatesView } from '@/features/recommendations/CandidatesView';
import { FlowSteps, goldenPathSteps } from '@/components/FlowSteps';

export default async function CandidatesPage({
  params,
  searchParams,
}: {
  params: Promise<{ systemId: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { systemId } = await params;
  const query = await searchParams;
  const capability = typeof query.capability === 'string' ? query.capability : undefined;
  const simulation = typeof query.simulation === 'string' ? query.simulation : undefined;

  // Candidates are always compared for one capability. Defaulting to a fixed
  // one would answer a question nobody asked, with a capability that may not
  // even belong to this system — say what is missing instead.
  if (!capability) {
    return (
      <div className="mx-auto max-w-3xl py-6">
        <FlowSteps steps={goldenPathSteps({ stage: 'candidates', systemId })} />
        <div className="frosted-card mt-4 p-6">
          <h1 className="text-lg font-medium text-slate-900">Which capability?</h1>
          <p className="mt-2 text-sm text-slate-600">
            Backup candidates are compared for a single capability. Choose one on the system, then
            simulate the owner being unavailable.
          </p>
          <Link
            href={`/systems/${systemId}`}
            className="motion-press mt-4 inline-block rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Back to the system
          </Link>
        </div>
      </div>
    );
  }

  return (
    <CandidatesView systemId={systemId} capabilityId={capability} simulationId={simulation} />
  );
}
