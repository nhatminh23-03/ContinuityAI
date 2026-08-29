'use client';

import { useSyncExternalStore } from 'react';

const STORAGE_KEY = 'cai-intro-dismissed';

const STEPS = [
  'See where knowledge sits with one person',
  'Test what happens if that person is unavailable',
  'Approve a plan that spreads it to a second engineer',
];

/**
 * Dismissal state lives in localStorage, which React cannot read during the
 * server render. `useSyncExternalStore` is the built-in way to subscribe to
 * exactly that — a value outside React that differs between server and client —
 * and it avoids setting state from inside an effect, which cascades a second
 * render on every mount.
 *
 * Storage can throw outright in a private window or with site data disabled, so
 * both the read and the write are guarded: a hint that reappears next visit is a
 * small cost, a crashed dashboard is not.
 */
const listeners = new Set<() => void>();

function subscribe(onChange: () => void) {
  listeners.add(onChange);
  return () => {
    listeners.delete(onChange);
  };
}

function isDismissed() {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === '1';
  } catch {
    return false;
  }
}

/** Hidden until the client can say otherwise, so a dismissed strip never flashes. */
function isDismissedOnServer() {
  return true;
}

function dismiss() {
  try {
    window.localStorage.setItem(STORAGE_KEY, '1');
  } catch {
    // Ignored on purpose — see the note above.
  }
  listeners.forEach((listener) => listener());
}

/**
 * What this product does, in three clauses, above everything else on a first
 * visit. The dashboard is otherwise a scoreboard: it reports numbers without
 * ever saying what a reader is meant to do with them.
 */
export function FirstRunStrip() {
  const dismissed = useSyncExternalStore(subscribe, isDismissed, isDismissedOnServer);
  if (dismissed) return null;

  return (
    <div className="frosted-card motion-rise mt-6 flex flex-wrap items-center gap-x-3 gap-y-2 px-5 py-3">
      <ol className="motion-stagger flex flex-1 flex-wrap items-center gap-x-2 gap-y-2">
        {STEPS.map((step, index) => (
          <li key={step} className="flex items-center gap-2">
            {index > 0 ? (
              <span aria-hidden className="mr-1 text-slate-300">
                →
              </span>
            ) : null}
            <span
              aria-hidden
              className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-slate-900 text-[10px] font-semibold text-white"
            >
              {index + 1}
            </span>
            <span className="text-xs font-medium text-slate-700">{step}</span>
          </li>
        ))}
      </ol>
      <button
        type="button"
        onClick={dismiss}
        aria-label="Dismiss the introduction"
        className="motion-press flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-slate-400 hover:bg-white/60 hover:text-slate-900"
      >
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-3.5 w-3.5" aria-hidden>
          <path d="m4 4 8 8m0-8-8 8" strokeLinecap="round" />
        </svg>
      </button>
    </div>
  );
}
