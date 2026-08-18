'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { api, queryKeys } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';
import { MetricStrip } from './MetricStrip';
import { OwnershipCard } from './OwnershipCard';
import { CapabilityPanel } from './CapabilityPanel';
import { CoverageCard } from './CoverageCard';
import { capabilitiesFromGraph, defaultCapabilityId } from './capabilities';
import { EvidenceDrawer } from '@/features/evidence/EvidenceDrawer';
import { SystemGraph } from '@/features/graph/SystemGraph';
import { SimulationOverlay } from '@/features/simulations/SimulationOverlay';
import { WhyPanel } from './WhyPanel';

export function SystemDetailView({
  systemId,
  capabilityParam,
  evidenceOpen = false,
  engineerParam,
  focusParam,
  whyOpen = false,
  simulateOpen = false,
}: {
  systemId: string;
  capabilityParam?: string;
  evidenceOpen?: boolean;
  engineerParam?: string;
  focusParam?: string;
  whyOpen?: boolean;
  simulateOpen?: boolean;
}) {
  const router = useRouter();

  const systemQuery = useQuery({
    queryKey: queryKeys.system(systemId),
    queryFn: () => api.getSystem(systemId),
  });
  const graphQuery = useQuery({
    queryKey: queryKeys.systemGraph(systemId),
    queryFn: () => api.getSystemGraph(systemId),
  });
  const focusedGraphQuery = useQuery({
    queryKey: queryKeys.systemGraph(systemId, focusParam),
    queryFn: () => api.getSystemGraph(systemId, focusParam),
    enabled: Boolean(focusParam),
  });
  const selectedForSim =
    capabilityParam ?? undefined; /* resolved fully below once the graph loads */
  const simCapabilityQuery = useQuery({
    queryKey: queryKeys.capability(selectedForSim ?? ''),
    queryFn: () => api.getCapability(selectedForSim ?? ''),
    enabled: simulateOpen && Boolean(selectedForSim),
  });
  const platformsQuery = useQuery({
    queryKey: queryKeys.platforms,
    queryFn: api.listPlatforms,
  });

  if (systemQuery.isPending || graphQuery.isPending) {
    return (
      <div className="mx-auto max-w-6xl space-y-6 py-6">
        <div className="frosted-card h-28 animate-pulse" />
        <div className="frosted-card h-72 animate-pulse" />
      </div>
    );
  }

  if (systemQuery.isError || graphQuery.isError) {
    const error = systemQuery.error ?? graphQuery.error;
    return (
      <div className="mx-auto max-w-6xl py-6">
        <div className="frosted-card p-6">
          <div className="text-sm font-medium text-slate-900">
            This system could not be loaded.
          </div>
          <div className="mt-1 text-xs text-slate-500">
            {error instanceof ApiError ? `Error code: ${error.code}` : 'Unexpected error.'}
          </div>
          <Link href="/" className="mt-4 inline-block text-xs font-medium text-slate-700 underline">
            Back to the dashboard
          </Link>
        </div>
      </div>
    );
  }

  const system = systemQuery.data;
  const graph = graphQuery.data;
  const capabilities = capabilitiesFromGraph(graph);
  const selectedCapabilityId =
    capabilityParam && capabilities.some((c) => c.id === capabilityParam)
      ? capabilityParam
      : defaultCapabilityId(capabilities);
  const platformName =
    platformsQuery.data?.platforms.find((p) => p.platform_id === system.platform_id)?.name ??
    system.platform_id;

  return (
    <div className="mx-auto max-w-6xl py-6">
      <nav aria-label="Breadcrumb" className="text-xs font-medium text-slate-500">
        <Link href="/" className="hover:text-slate-900 hover:underline">
          {platformName}
        </Link>
        <span className="mx-1.5">›</span>
        <span className="text-slate-700">{system.name}</span>
      </nav>

      <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-3xl font-medium tracking-tight text-slate-900">{system.name}</h1>
          {system.description ? (
            <p className="mt-1 max-w-2xl text-[15px] text-slate-600">{system.description}</p>
          ) : null}
        </div>
        <button
          type="button"
          onClick={() =>
            router.replace(
              `/systems/${systemId}?capability=${selectedCapabilityId ?? ''}&simulate=1`,
              { scroll: false },
            )
          }
          className="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800"
        >
          Simulate unavailability
        </button>
      </div>

      <div className="mt-6">
        <MetricStrip
          system={system}
          onWhyClick={() =>
            router.replace(
              `/systems/${systemId}?capability=${selectedCapabilityId ?? ''}&why=1`,
              { scroll: false },
            )
          }
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <SystemGraph
            graph={(focusParam && focusedGraphQuery.data) || graph}
            focusId={focusParam}
            onCapabilityClick={(id) =>
              router.replace(
                focusParam === id
                  ? `/systems/${systemId}?capability=${id}`
                  : `/systems/${systemId}?capability=${id}&focus=${id}`,
                { scroll: false },
              )
            }
            onEvidenceClick={() =>
              selectedCapabilityId &&
              router.replace(
                `/systems/${systemId}?capability=${selectedCapabilityId}${
                  focusParam ? `&focus=${focusParam}` : ''
                }&evidence=1`,
                { scroll: false },
              )
            }
          />
          {selectedCapabilityId ? (
            <CoverageCard
              capabilityId={selectedCapabilityId}
              onViewEvidence={(engineerId) =>
                router.replace(
                  `/systems/${systemId}?capability=${selectedCapabilityId}&evidence=1&engineer=${engineerId}`,
                  { scroll: false },
                )
              }
            />
          ) : null}
        </div>
        <div className="space-y-6">
          <OwnershipCard ownership={system.declared_ownership} />
          <CapabilityPanel
            capabilities={capabilities}
            edges={graph.edges}
            selectedId={selectedCapabilityId}
            onSelect={(id) =>
              router.replace(`/systems/${systemId}?capability=${id}`, { scroll: false })
            }
            onViewEvidence={(id) =>
              router.replace(`/systems/${systemId}?capability=${id}&evidence=1`, {
                scroll: false,
              })
            }
          />
        </div>
      </div>

      {simulateOpen ? (
        <SimulationOverlay
          systemId={systemId}
          defaultEngineerId={simCapabilityQuery.data?.primary_engineer?.engineer_id}
          selectedCapabilityId={selectedCapabilityId}
          onClose={() =>
            router.replace(`/systems/${systemId}?capability=${selectedCapabilityId ?? ''}`, {
              scroll: false,
            })
          }
        />
      ) : null}

      {whyOpen ? (
        <WhyPanel
          system={system}
          capabilityId={selectedCapabilityId}
          onClose={() =>
            router.replace(`/systems/${systemId}?capability=${selectedCapabilityId ?? ''}`, {
              scroll: false,
            })
          }
        />
      ) : null}

      {evidenceOpen && selectedCapabilityId ? (
        <EvidenceDrawer
          capabilityId={selectedCapabilityId}
          engineerId={engineerParam}
          engineerName={
            engineerParam
              ? graph.nodes.find((node) => node.id === engineerParam)?.label
              : undefined
          }
          onClose={() =>
            router.replace(`/systems/${systemId}?capability=${selectedCapabilityId}`, {
              scroll: false,
            })
          }
        />
      ) : null}
    </div>
  );
}
