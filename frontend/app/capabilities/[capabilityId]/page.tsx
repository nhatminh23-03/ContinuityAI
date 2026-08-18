import { CapabilityDetailView } from '@/features/systems/CapabilityDetailView';

export default async function CapabilityDetailPage({
  params,
}: {
  params: Promise<{ capabilityId: string }>;
}) {
  const { capabilityId } = await params;
  return <CapabilityDetailView capabilityId={capabilityId} />;
}
