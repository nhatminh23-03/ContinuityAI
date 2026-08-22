import type { ReactNode } from "react";
import { AppBackground } from "@/components/AppBackground";
import { SidebarNav } from "@/components/SidebarNav";
import { PageTransition } from "@/components/PageTransition";

/**
 * The application frame: ambient gradient behind everything, a floating
 * liquid-glass sidebar, and the scrollable content column.
 */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-dvh">
      <AppBackground />
      <div className="flex min-h-dvh gap-6 p-6">
        <aside className="glass-panel sticky top-6 flex h-[calc(100dvh-3rem)] w-64 shrink-0 flex-col rounded-3xl p-5">
          <div className="px-2 pb-6">
            <div className="text-xl font-semibold tracking-tight text-slate-900">
              ContinuityAI
            </div>
            <div className="text-xs font-medium text-slate-600">
              Engineering Resilience
            </div>
          </div>
          <SidebarNav />
          <div className="mt-auto flex items-center gap-3 rounded-xl px-2 pt-4">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white/70 text-xs font-semibold text-slate-700 ring-1 ring-white/60">
              M
            </div>
            <div className="text-xs font-medium text-slate-600">Manager</div>
          </div>
        </aside>
        <main className="min-w-0 flex-1">
          <PageTransition>{children}</PageTransition>
        </main>
      </div>
    </div>
  );
}
