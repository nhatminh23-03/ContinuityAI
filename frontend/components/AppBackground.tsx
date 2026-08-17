"use client";

import { useEffect, useState } from "react";
import Grainient from "@/components/Grainient/Grainient";

/**
 * Full-viewport ambient background layer. Sits behind every surface including
 * the sidebar; content never scrolls it away. Purely decorative, so it is
 * hidden from assistive tech and ignores pointer events.
 */
export function AppBackground() {
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(query.matches);
    const onChange = (event: MediaQueryListEvent) => setReducedMotion(event.matches);
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, []);

  return (
    <div aria-hidden className="fixed inset-0 -z-10 pointer-events-none">
      <Grainient
        color1="#e98138"
        color2="#ffffff"
        color3="#3B82F6"
        timeSpeed={reducedMotion ? 0 : 0.25}
        colorBalance={0}
        warpStrength={1}
        warpFrequency={5}
        warpSpeed={2}
        warpAmplitude={50}
        blendAngle={0}
        blendSoftness={0.05}
        rotationAmount={500}
        noiseScale={1.9}
        grainAmount={0}
        grainScale={0.2}
        grainAnimated
        contrast={1.5}
        gamma={1}
        saturation={1}
        centerX={0}
        centerY={0}
        zoom={0.9}
      />
    </div>
  );
}
