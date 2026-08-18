import { CandidatesView } from '@/features/recommendations/CandidatesView';

export default async function CandidatesPage({
  params,
  searchParams,
}: {
  params: Promise<{ systemId: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { systemId } = await params;
  const query = await searchParams;
  const capability =
    typeof query.capability === 'string' ? query.capability : 'cap_incident_recovery';
  const simulation = typeof query.simulation === 'string' ? query.simulation : undefined;
  return (
    <CandidatesView systemId={systemId} capabilityId={capability} simulationId={simulation} />
  );
}
