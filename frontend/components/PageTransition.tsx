'use client';

import type { ReactNode } from 'react';
import { usePathname } from 'next/navigation';

/**
 * Replays the shared rise-in animation on every route change. Keyed on the
 * pathname rather than merely classed: a CSS animation only restarts when the
 * element is remounted, and the router reuses one component across paths that
 * share a segment — /systems/a to /systems/b would otherwise arrive with no
 * transition at all.
 */
export function PageTransition({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <div key={pathname} className="motion-rise">
      {children}
    </div>
  );
}
