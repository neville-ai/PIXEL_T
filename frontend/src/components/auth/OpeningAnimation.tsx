import React, { useLayoutEffect, useRef } from 'react';
import { LogoPixelT } from '@/components/ui/LogoPixelT';
import { stageIndex, type OpeningStage } from '@/utils/openingTimeline';
import '@/assets/opening.css';

export interface OpeningAnimationProps {
  /** Current stage from `useOpeningAnimation`. */
  stage: OpeningStage;
  /**
   * The real logo placeholder in the branding panel. It is the FLIP target:
   * the single animated logo lands exactly on this rectangle, then hands off.
   */
  targetRef: React.RefObject<HTMLDivElement>;
}

export interface PixelDef {
  left: number;
  top: number;
  size: number;
  background: string;
  fromX: number;
  fromY: number;
  stagger: number;
}

/*
 * Pixel coordinates are sampled from the official logo asset's alpha mask
 * (`Final Concept Logo PIXEL-T.png`, 645x387 RGBA, ink bbox x54 y134 w548 h142).
 *
 * The reference (`Analysis output 2.png` @ 2.5s / 3.3s) shows the pixels forming
 * ONLY the left "P-pixel" symbol — a compact, roughly square cluster — while the
 * "PIXEL-T" wordmark and its tagline resolve separately to its right. So the
 * mask is restricted to the mark's horizontal run (asset x54..209); the wordmark
 * occupies x250..601 with a 40px empty column gap between them.
 *
 * A 9x9 grid over the inset mark region yields cells whose alpha coverage
 * exceeded 30%; the four closest to the mark core are FOCAL (0.7–1.6s), the
 * rest SUPPORTING (1.6–2.5s). Values are in the 540x140 logo-box space (the
 * ink box scaled by 0.9854), so the cluster overlays the official mark exactly
 * at scale 1 and the dissolve into the full logo is same-geometry.
 *
 * The four corner "brackets" visible around the mark in the reference are part
 * of the official artwork itself (a scanner-frame motif drawn into the P), so
 * no separate bracket elements are rendered.
 */
export const FOCAL_PIXELS: PixelDef[] = [
  { left: 76.9, top: 69.5, size: 11, background: '#29B8B8', fromX: 0.0, fromY: -0.4, stagger: 0 },
  { left: 76.9, top: 80.8, size: 11, background: '#18A6A6', fromX: 0.0, fromY: 8.7, stagger: 160 },
  { left: 76.9, top: 58.1, size: 9, background: '#5FD8D8', fromX: 0.0, fromY: -9.5, stagger: 320 },
  { left: 88.7, top: 69.5, size: 11, background: '#29B8B8', fromX: 9.5, fromY: -0.4, stagger: 480 },
];

export const SUPPORTING_PIXELS: PixelDef[] = [
  { left: 88.7, top: 80.8, size: 11, background: '#29B8B8', fromX: 9.5, fromY: 8.7, stagger: 0 },
  { left: 65.0, top: 58.1, size: 13, background: '#18A6A6', fromX: -9.5, fromY: -9.5, stagger: 70 },
  { left: 88.7, top: 58.1, size: 9, background: '#5FD8D8', fromX: 9.5, fromY: -9.5, stagger: 140 },
  { left: 76.9, top: 92.1, size: 13, background: '#29B8B8', fromX: 0.0, fromY: 17.7, stagger: 210 },
  { left: 76.9, top: 46.8, size: 13, background: '#18A6A6', fromX: 0.0, fromY: -18.5, stagger: 280 },
  { left: 65.0, top: 92.1, size: 9, background: '#5FD8D8', fromX: -9.5, fromY: 17.7, stagger: 350 },
  { left: 88.7, top: 92.1, size: 13, background: '#29B8B8', fromX: 9.5, fromY: 17.7, stagger: 420 },
];

/* The logo element's intrinsic box equals the ink box (540x140). Keeping it
   fixed means the FLIP only ever has to compute a scale and a translation,
   and the pixel grid inside it stays registered to the artwork at every
   scale. */
const LOGO_BOX_WIDTH = 540;
const LOGO_BOX_HEIGHT = 140;

function pixelStyle(def: PixelDef): React.CSSProperties {
  return {
    left: def.left,
    top: def.top,
    width: def.size,
    height: def.size,
    background: def.background,
    '--dx': `${def.fromX}px`,
    '--dy': `${def.fromY}px`,
    '--stagger': `${def.stagger}ms`,
  } as React.CSSProperties;
}

/**
 * Full-screen overlay that plays the approved 10-stage opening timeline.
 *
 * Rendering rules:
 * - `aria-hidden` and `pointer-events: none` at all times: it can never trap
 *   focus, block the form, or leak decorative content to screen readers.
 * - Exactly ONE logo element exists during the whole animation. It is moved
 *   with numeric FLIP transforms (transform only, never layout animation)
 *   from the viewport center onto the real placeholder rectangle.
 * - The pixel grid is a child of that same logo element, so it is always
 *   registered to the artwork and inherits its transform for free.
 * - The overlay unmounts after the nominal 10s timeline completes.
 */
export const OpeningAnimation: React.FC<OpeningAnimationProps> = ({ stage, targetRef }) => {
  const idx = stageIndex(stage);
  const stageIdxRef = useRef(idx);
  stageIdxRef.current = idx;

  const logoRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    const apply = () => {
      const logo = logoRef.current;
      const target = targetRef.current;
      if (!logo || !target) return;

      try {
        const currentIdx = stageIdxRef.current;
        const viewportW = window.innerWidth;
        const viewportH = window.innerHeight;
        const targetRect = target.getBoundingClientRect();

        const baseW = LOGO_BOX_WIDTH;
        const baseH = LOGO_BOX_HEIGHT;

        /* Fit the 540px box to the viewport so the forming logo never
           overflows narrow screens. The same factor is applied to the whole
           element, so the pixel grid stays registered. */
        const fit = Math.min(1, (viewportW * 0.8) / baseW);

        let scale: number;
        let x: number;
        let y: number;
        let moveMs: number;

        if (currentIdx <= 5) {
          /* Stages 1-6: the MARK cluster is centered in the viewport. The
             identity moment (stage 6) scales 100% -> 113% over exactly 2000 ms.

             The pixels (and, once visible, the mark) occupy the mark band of
             the 540-box (asset x54..209 -> box x53..206, centre ~129.5), which
             is left of the box's own centre (270). Per the reference the forming
             composition centres on the MARK, not the full logo, so the box is
             shifted right by the scaled distance from the mark centre to the box
             centre. This is folded into the transform (not CSS `left`) so the
             same element can later be repositioned to the target via
             `targetRect.left` for stages 7-10 with no residual offset. */
          const zoom = currentIdx >= 5 ? 1.13 : 1;
          scale = fit * zoom;
          const markCentreBox = (53 + 206) / 2; // 129.5
          const markShift = (baseW / 2 - markCentreBox) * scale;
          x = (viewportW - baseW * scale) / 2 + markShift;
          y = (viewportH - baseH * scale) / 2;
          if (currentIdx <= 3) moveMs = 0;
          else if (currentIdx === 4) moveMs = 0;
          else moveMs = 2000; // identity moment: 100% -> 113% over 2.0s
        } else {
          /* Stages 7-10: docked on the branding panel placeholder. */
          scale = targetRect.width > 0 ? targetRect.width / baseW : 1;
          x = targetRect.left;
          y = targetRect.top;
          moveMs = currentIdx === 6 ? 1000 : 250; // transition 6.0s -> 7.0s
        }

        logo.style.setProperty('--logo-move-ms', `${moveMs}ms`);
        logo.style.transform = `translate(${x}px, ${y}px) scale(${scale})`;
      } catch {
        // Defensive: measurement failures must never crash the Login page.
        // The overlay is non-blocking, so Login stays usable regardless.
      }
    };

    apply();

    const handleResize = () => apply();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [idx, targetRef]);

  const focalIn = idx >= 1 && idx < 4;
  const supportingIn = idx >= 2 && idx < 4;
  const logoVisible = idx >= 4;
  const logoHandedOff = idx >= 8;

  const logoClassName = [
    'pixel-t-intro__logo',
    logoHandedOff ? 'is-handed-off' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className="pixel-t-intro" data-stage={stage} aria-hidden="true" role="presentation">
      <div className="pixel-t-intro__bg pixel-t-navy-surface" />
      <div className="pixel-t-intro__glow" aria-hidden="true" />

      <div ref={logoRef} className={logoClassName}>
        <div className="pixel-t-intro__pixels" aria-hidden="true">
          {FOCAL_PIXELS.map((def, i) => (
            <span
              key={`focal-${i}`}
              className={`pixel-t-intro__pixel${focalIn ? ' is-in' : ''}`}
              style={pixelStyle(def)}
            />
          ))}
          {SUPPORTING_PIXELS.map((def, i) => (
            <span
              key={`support-${i}`}
              className={`pixel-t-intro__pixel${supportingIn ? ' is-in' : ''}`}
              style={pixelStyle(def)}
            />
          ))}
        </div>

        <div className={`pixel-t-intro__logo-art pixel-t-logo-box${logoVisible ? ' is-visible' : ''}`}>
          {/* Same high-contrast variant the branding-panel placeholder uses, so the
              centered identity moment reads on navy and the FLIP handoff is a
              continuous single logo (no dark→light swap mid-transition). */}
          <LogoPixelT variant="light" />
        </div>
      </div>
    </div>
  );
};

export default OpeningAnimation;