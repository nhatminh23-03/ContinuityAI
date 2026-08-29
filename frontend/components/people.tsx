/**
 * People are always monochrome. Readiness renders as a five-step grey ladder
 * with a text label — never a colour, number, percentage, or rank.
 */

import type { ReadinessLevel } from '@/types/api';
import { READINESS_COPY } from '@/lib/copy';

const LADDER_STEPS: Record<ReadinessLevel, number> = {
  NONE: 0,
  EXPOSED: 1,
  ASSISTED: 2,
  PRACTICED: 3,
  VALIDATED: 5,
};

const BAR_HEIGHTS = [4, 6, 8, 10, 12];

export function ReadinessLadder({ level }: { level: ReadinessLevel }) {
  const filled = LADDER_STEPS[level];
  return (
    <span
      className="inline-flex items-center gap-2"
      role="img"
      aria-label={`Evidence shows: ${READINESS_COPY[level]}`}
    >
      <span className="flex items-end gap-[2px]" aria-hidden>
        {BAR_HEIGHTS.map((height, index) => (
          <span
            key={index}
            className={`motion-ladder ${index < filled ? 'bg-slate-600' : 'bg-slate-300'}`}
            style={{
              width: 3,
              height,
              borderRadius: 1,
              animationDelay: `${index * 40}ms`,
            }}
          />
        ))}
      </span>
      <span className="text-xs font-medium text-slate-700">{READINESS_COPY[level]}</span>
    </span>
  );
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase() ?? '')
    .join('');
}

export function EngineerBadge({ name, role }: { name: string; role?: string }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <span
        aria-hidden
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/70 text-xs font-semibold text-slate-700 ring-1 ring-white/60"
      >
        {initials(name)}
      </span>
      <span className="flex flex-col leading-tight">
        <span className="text-sm font-medium text-slate-900">{name}</span>
        {role ? <span className="text-xs text-slate-500">{role}</span> : null}
      </span>
    </span>
  );
}
