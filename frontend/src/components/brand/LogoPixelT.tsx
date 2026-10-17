import React, { useState } from 'react';
// Official transparent PNG (RGBA) — the approved "Final Concept" logo asset.
// The image carries no background of its own (all four corners are alpha 0),
// so it blends directly into the navy panel. The transparent padding inside
// the file is compensated by the `.pixel-t-logo-box` geometry wrapper in
// opening.css, which is a pure sizing element: no background, no border, no
// shadow.
import logoSource from '@/assets/pixel-t-logo-transparent.png';
// Derived light variant (see `variant` prop): same silhouette/alpha as the
// original, but the wordmark is remapped to a near-white with the official
// teal accents preserved, so it reads clearly on the navy panel.
import logoLightSrc from '@/assets/pixel-t-logo-light.png';

export interface LogoPixelTProps {
  /** Accessible alt text. Defaults to the official brand name. */
  alt?: string;
  /** Extra classes applied to the wrapper element. */
  className?: string;
  /**
   * `"transparent"` (default) renders the official dark asset.
   * `"light"` renders the derived high-contrast asset, which keeps the exact
   * silhouette and teal accents but lifts the wordmark to ~8.4:1 contrast on
   * the Deep Medical Navy panel (the original measures only ~1.1:1 there).
   */
  variant?: 'transparent' | 'light';
  /**
   * Optional precise sizing, used where the visible "ink" of the logo must
   * occupy an exact box (e.g. the 64px AppShell header).
   *
   * The official PNG is 645x387 but its visible artwork ("ink") only occupies
   * the bbox x54 y134 w548 h142 — the rest is fully transparent padding. When
   * `inkHeight` is given, the wrapper is sized to the ink box and the image is
   * offset by the padding so the artwork lands exactly inside it. When omitted,
   * the previous auto-sized behaviour is used unchanged.
   */
  inkHeight?: number;
}

// Official asset geometry. Shared by the intro animation and the AppShell so
// both derive their offsets from the same measured numbers instead of guessing.
export const LOGO_ASSET_GEOMETRY = {
  width: 645,
  height: 387,
  inkX: 54,
  inkY: 134,
  inkWidth: 548,
  inkHeight: 142,
} as const;

/**
 * Official PIXEL-T logo (Final Concept — P-Pixel / Alternative 2).
 *
 * Uses the approved transparent PNG from references/intro
 * (`pixel-t-logo-transparent.png`, copied byte-identical into src/assets).
 * The logo is never redrawn with SVG/CSS, and no white-box background comes
 * from the file itself — the `.pixel-t-logo-box` wrapper is a pure geometry
 * element that only compensates the asset's transparent padding. If the asset
 * fails to load, an accessible text wordmark is rendered as a graceful
 * fallback so the layout stays usable.
 */
export const LogoPixelT: React.FC<LogoPixelTProps> = ({
  alt = 'PIXEL-T',
  className = '',
  variant = 'transparent',
  inkHeight,
}) => {
  const [hasFailed, setHasFailed] = useState(false);

  const logoSrc = variant === 'light' ? logoLightSrc : logoSource;

  if (hasFailed) {
    return (
      <span
        role="img"
        aria-label={alt}
        className={`inline-block font-bold tracking-tight text-primary-900 dark:text-dark-text ${className}`}
      >
        PIXEL-T
      </span>
    );
  }

  // Legacy path: no explicit ink sizing requested, behave exactly as before.
  if (inkHeight === undefined) {
    return (
      <img
        src={logoSrc}
        alt={alt}
        className={`block h-auto ${className}`}
        draggable={false}
        onError={() => setHasFailed(true)}
      />
    );
  }

  // Precise path: size the wrapper to the visible artwork and push the
  // transparent padding outside of it. All numbers derive from the measured
  // asset geometry above — nothing is hand-tuned per call site.
  const scale = inkHeight / LOGO_ASSET_GEOMETRY.inkHeight;

  return (
    <span
      className={`relative block shrink-0 ${className}`}
      style={{
        width: LOGO_ASSET_GEOMETRY.inkWidth * scale,
        height: inkHeight,
      }}
    >
      <img
        src={logoSrc}
        alt={alt}
        className="absolute max-w-none"
        draggable={false}
        onError={() => setHasFailed(true)}
        style={{
          width: LOGO_ASSET_GEOMETRY.width * scale,
          height: LOGO_ASSET_GEOMETRY.height * scale,
          left: -LOGO_ASSET_GEOMETRY.inkX * scale,
          top: -LOGO_ASSET_GEOMETRY.inkY * scale,
        }}
      />
    </span>
  );
};

export default LogoPixelT;
