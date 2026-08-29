'use client';

import { useEffect, useId, useRef, useState } from 'react';

/**
 * A one-line explanation attached to a term, shown at the first place that term
 * appears. The interface carries seven distinct vocabularies — risk index,
 * coverage, evidence confidence, drift, readiness, criticality, overlap — and a
 * reader meets most of them before any documentation.
 *
 * The tooltip is absolutely positioned so opening it never moves the content
 * underneath, and it is described rather than labelled: screen readers announce
 * the explanation as part of the term it belongs to, so the hint is not a
 * separate thing to navigate to.
 */
export function InfoHint({ label, text }: { label: string; text: string }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const wrapRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      setOpen(false);
      // Registered in the capture phase and stopped here so the drawer or modal
      // underneath does not also close on the same press. Escape should dismiss
      // the thing most recently opened, and that is this tooltip.
      event.stopPropagation();
    };
    // A hint left open behind a click elsewhere is clutter, not information.
    const onPointerDown = (event: PointerEvent) => {
      if (!wrapRef.current?.contains(event.target as Node)) setOpen(false);
    };
    window.addEventListener('keydown', onKey, true);
    window.addEventListener('pointerdown', onPointerDown);
    return () => {
      window.removeEventListener('keydown', onKey, true);
      window.removeEventListener('pointerdown', onPointerDown);
    };
  }, [open]);

  return (
    <span ref={wrapRef} className="relative inline-flex items-center align-middle">
      <button
        type="button"
        aria-label={`What does ${label} mean?`}
        aria-expanded={open}
        aria-describedby={open ? id : undefined}
        // Opens rather than toggles. Hovering already opened it, so a toggle
        // here closed the hint on the one gesture most likely to follow a
        // hover — pointing at the term and clicking it. Closing is left to
        // mouseleave, blur, Escape, and a pointer down outside, all of which
        // work for touch and keyboard as well.
        onClick={() => setOpen(true)}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        className="motion-press flex h-4 w-4 items-center justify-center rounded-full text-slate-400 hover:bg-white/60 hover:text-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-slate-400"
      >
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-3.5 w-3.5" aria-hidden>
          <circle cx="8" cy="8" r="6.25" />
          <path d="M8 7.25v3.5" strokeLinecap="round" />
          <path d="M8 5.1v.1" strokeLinecap="round" />
        </svg>
      </button>
      {open ? (
        <span
          id={id}
          role="tooltip"
          className="motion-fade absolute left-1/2 top-full z-40 mt-1.5 w-64 -translate-x-1/2 rounded-xl bg-slate-900 px-3 py-2 text-[11px] font-normal normal-case leading-relaxed tracking-normal text-white shadow-lg"
        >
          {text}
        </span>
      ) : null}
    </span>
  );
}
