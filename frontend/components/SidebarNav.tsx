"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/**
 * Three destinations, not four. A simulation is always run against a system the
 * manager is already looking at, so a top-level entry offered a second,
 * context-free way to start one — a dropdown of system names, chosen blind.
 * `/simulations` still resolves for anyone holding the link; it is simply not
 * advertised as a place to begin. Supersedes the four-entry decision in
 * docs/UI_REVIEW.md.
 */
const NAV_ITEMS = [
  {
    href: "/",
    label: "Home",
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-5 w-5">
        <rect x="3" y="3" width="6" height="6" rx="1" />
        <rect x="11" y="3" width="6" height="6" rx="1" />
        <rect x="3" y="11" width="6" height="6" rx="1" />
        <rect x="11" y="11" width="6" height="6" rx="1" />
      </svg>
    ),
  },
  {
    href: "/systems",
    label: "Systems",
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-5 w-5">
        <rect x="3" y="3" width="5" height="5" rx="1" />
        <rect x="12" y="12" width="5" height="5" rx="1" />
        <path d="M8 5.5h4.5v6.5" />
        <path d="M5.5 8v4.5H12" />
      </svg>
    ),
  },
  {
    href: "/plans",
    label: "Plans",
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-5 w-5">
        <rect x="4" y="3" width="12" height="14" rx="2" />
        <path d="M7.5 7.5h5M7.5 10.5h5M7.5 13.5h3" />
      </svg>
    ),
  },
];

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <nav aria-label="Primary" className="flex flex-col gap-1">
      {NAV_ITEMS.map((item) => {
        const active =
          item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={`nav-item motion-press flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium ${
              active
                ? "bg-white/70 text-slate-900 shadow-sm ring-1 ring-white/60"
                : "text-slate-600 hover:bg-white/40 hover:text-slate-900"
            }`}
          >
            {item.icon}
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
