export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-5xl py-6">
      <h1 className="text-4xl font-medium tracking-tight text-slate-900">
        Knowledge Resilience
      </h1>
      <p className="mt-2 text-[15px] text-slate-600">
        Where does critical capability depend on one person?
      </p>

      <div className="mt-8 grid grid-cols-2 gap-6">
        <div className="frosted-card p-6">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Platform
          </div>
          <div className="mt-1 text-2xl font-medium text-slate-900">Payments</div>
          <div className="mt-6 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Highest system risk
          </div>
          <div className="mt-1 flex items-end justify-between">
            <span className="text-5xl font-light tabular-nums text-slate-900">—</span>
            <span className="glass-chip rounded-full px-3 py-1 text-xs font-semibold text-slate-700">
              Dashboard arrives in Phase 6
            </span>
          </div>
        </div>
        <div className="frosted-card p-6">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Platform
          </div>
          <div className="mt-1 text-2xl font-medium text-slate-900">Identity</div>
          <div className="mt-6 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Highest system risk
          </div>
          <div className="mt-1 flex items-end justify-between">
            <span className="text-5xl font-light tabular-nums text-slate-900">—</span>
            <span className="glass-chip rounded-full px-3 py-1 text-xs font-semibold text-slate-700">
              Dashboard arrives in Phase 6
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
