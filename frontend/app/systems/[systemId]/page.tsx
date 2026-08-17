import { SystemDetailView } from '@/features/systems/SystemDetailView';

export default async function SystemDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ systemId: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { systemId } = await params;
  const query = await searchParams;
  const capability = typeof query.capability === 'string' ? query.capability : undefined;
  const engineer = typeof query.engineer === 'string' ? query.engineer : undefined;
  const focus = typeof query.focus === 'string' ? query.focus : undefined;
  return (
    <SystemDetailView
      systemId={systemId}
      capabilityParam={capability}
      evidenceOpen={query.evidence === '1'}
      engineerParam={engineer}
      focusParam={focus}
    />
  );
}
