import type { EvidenceRecord, EvidenceSourceType } from '@/types/api';
import {
  EVIDENCE_ROLE_COPY,
  EVIDENCE_STRENGTH_COPY,
  FRESHNESS_COPY,
  provenanceSourceCopy,
} from '@/lib/copy';

/**
 * One typed evidence record — the product's differentiator made visible:
 * role, strength, and freshness ride alongside source, date, and excerpt.
 * Badges are neutral grey glass: evidence metadata is not status colour.
 */

const SOURCE_ICON: Record<EvidenceSourceType, React.ReactNode> = {
  INCIDENT: (
    <path d="M8 2.5 14.5 13.5H1.5L8 2.5Zm0 4v3.5M8 11.5v.5" strokeLinecap="round" strokeLinejoin="round" />
  ),
  PULL_REQUEST: (
    <path d="M4.5 3.5a1.5 1.5 0 1 0 0 .01M4.5 5v6m0 0a1.5 1.5 0 1 0 0 .01M11.5 11V6.8c0-.8-.3-1.3-1-1.3H8.2m2 -2L8.2 5.5l2 2" strokeLinecap="round" strokeLinejoin="round" />
  ),
  CODE_REVIEW: (
    <path d="M5.5 5.5 3 8l2.5 2.5m5-5L13 8l-2.5 2.5M9 4.5l-2 7" strokeLinecap="round" strokeLinejoin="round" />
  ),
  COMMIT: (
    <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5ZM1.5 8h4M10.5 8h4" strokeLinecap="round" />
  ),
  ISSUE: (
    <path d="M8 2.5a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11Zm0 5.4v.1" strokeLinecap="round" />
  ),
  TICKET: (
    <path d="M2.5 6.5v-2h11v2a1.5 1.5 0 0 0 0 3v2h-11v-2a1.5 1.5 0 0 0 0-3Z" strokeLinejoin="round" />
  ),
  DOCUMENT: (
    <path d="M4 2.5h5.5L12 5v8.5H4v-11ZM6 7h4M6 9.5h4" strokeLinecap="round" strokeLinejoin="round" />
  ),
  TECHNICAL_DISCUSSION: (
    <path d="M2.5 3.5h11v7H8l-3 2.5v-2.5H2.5v-7Z" strokeLinejoin="round" />
  ),
  MANAGER_ATTESTATION: (
    <path d="M6 8a2.25 2.25 0 1 0 0-4.5A2.25 2.25 0 0 0 6 8Zm-3.5 5.5c0-2 1.6-3.3 3.5-3.3s3.5 1.3 3.5 3.3M10.5 7.5l1.5 1.5 2.5-2.5" strokeLinecap="round" strokeLinejoin="round" />
  ),
};

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="glass-chip inline-flex items-center rounded-full bg-white/40 px-2 py-0.5 text-[11px] font-semibold text-slate-600">
      {children}
    </span>
  );
}

export function EvidenceCard({ record }: { record: EvidenceRecord }) {
  return (
    <article className="frosted-card p-4">
      <header className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <svg
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.3"
          className="h-4 w-4 shrink-0 text-slate-500"
          aria-hidden
        >
          {SOURCE_ICON[record.source_type]}
        </svg>
        <span className="text-sm font-semibold text-slate-900">{record.source_reference}</span>
        <span className="text-xs text-slate-500">{record.artifact_date}</span>
        <span className="ml-auto flex flex-wrap gap-1.5">
          <Badge>{EVIDENCE_ROLE_COPY[record.evidence_role]}</Badge>
          <Badge>{EVIDENCE_STRENGTH_COPY[record.evidence_strength]}</Badge>
          <Badge>{FRESHNESS_COPY[record.freshness]}</Badge>
        </span>
      </header>
      {record.source_title ? (
        <div className="mt-1.5 text-xs font-medium text-slate-600">{record.source_title}</div>
      ) : null}
      <p className="mt-2 border-l-2 border-slate-200 pl-3 text-sm italic leading-relaxed text-slate-700">
        {record.summary}
      </p>
      <footer className="mt-2 text-[11px] text-slate-500">
        {provenanceSourceCopy(record.provenance.source)} · {record.provenance.record_id}
        {record.provenance.source_url ? (
          <>
            {' · '}
            <a
              href={record.provenance.source_url}
              target="_blank"
              rel="noreferrer"
              className="underline decoration-slate-300 underline-offset-2 hover:text-slate-700"
            >
              source
            </a>
          </>
        ) : null}
      </footer>
    </article>
  );
}
