/**
 * What the comparison deliberately ignores. The API disclaimer renders
 * verbatim; the list is static frontend copy per PRD §11.6 and the
 * mockup-correction list.
 */
const NOT_CONSIDERED = [
  'Current workload',
  'Career goals',
  'Performance history',
  'Leave and on-call schedules',
  'Timezone',
  'Team priorities',
  'Staffing constraints',
];

export function NotConsideredPanel({ disclaimer }: { disclaimer: string }) {
  return (
    <div className="frosted-card p-6">
      <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3" className="h-4 w-4 text-slate-500" aria-hidden>
          <circle cx="8" cy="8" r="6.5" />
          <path d="M8 7.5v3.5M8 5v.5" strokeLinecap="round" />
        </svg>
        Not considered in this comparison
      </h2>
      <ul className="mt-3 flex flex-wrap gap-2">
        {NOT_CONSIDERED.map((item) => (
          <li
            key={item}
            className="rounded-full bg-white/50 px-3 py-1 text-xs font-medium text-slate-600 ring-1 ring-slate-900/5"
          >
            {item}
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs leading-relaxed text-slate-500">{disclaimer}</p>
      <p className="mt-2 text-xs text-slate-500">
        The manager chooses. Nothing here assigns anyone to anything.
      </p>
    </div>
  );
}
