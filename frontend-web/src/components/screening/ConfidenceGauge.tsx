// ============================================================
// SafeSkin AI – ConfidenceGauge Component
// Animated arc gauge showing AI confidence percentage
// ============================================================
import React, { useEffect, useRef } from 'react';
import { clsx } from 'clsx';

interface ConfidenceGaugeProps {
  confidence: number;   // 0–1 (e.g., 0.87)
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

const sizeMap = {
  sm: { viewBox: 160, cx: 80, cy: 80, r: 60, sw: 12, textSize: 'text-xl', subSize: 'text-xs' },
  md: { viewBox: 200, cx: 100, cy: 100, r: 75, sw: 14, textSize: 'text-3xl', subSize: 'text-sm' },
  lg: { viewBox: 240, cx: 120, cy: 120, r: 90, sw: 16, textSize: 'text-4xl', subSize: 'text-sm' },
};

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.85) return '#10B981'; // success
  if (confidence >= 0.65) return '#F59E0B'; // warning
  return '#EF4444';                          // danger
}

function getConfidenceLabel(confidence: number): string {
  if (confidence >= 0.85) return 'High Confidence';
  if (confidence >= 0.65) return 'Moderate Confidence';
  return 'Low Confidence';
}

export const ConfidenceGauge: React.FC<ConfidenceGaugeProps> = ({
  confidence,
  size = 'md',
  showLabel = true,
  className,
}) => {
  const { viewBox, cx, cy, r, sw, textSize, subSize } = sizeMap[size];
  const arcRef = useRef<SVGPathElement>(null);
  const pct = Math.min(Math.max(confidence, 0), 1);
  const color = getConfidenceColor(pct);
  const label = getConfidenceLabel(pct);

  // Arc: A standard gauge (speedometer style)
  // Starts at bottom-left (150 degrees) and goes clockwise to bottom-right (390 degrees)
  const startAngle = 140;
  const endAngle = 400;
  const totalAngle = 260; // 400 - 140

  const toRad = (deg: number) => (deg * Math.PI) / 180;

  // Point on circle
  const pt = (deg: number) => ({
    x: cx + r * Math.cos(toRad(deg)),
    y: cy + r * Math.sin(toRad(deg)),
  });

  // Full track arc path
  const trackStart = pt(startAngle);
  const trackEnd = pt(endAngle);
  // Sweep flag is 1 (clockwise), largeArc is 1 (since 260 > 180)
  const trackPath = `M ${trackStart.x} ${trackStart.y} A ${r} ${r} 0 1 1 ${trackEnd.x} ${trackEnd.y}`;

  // Fill arc path (proportional to confidence)
  const fillAngle = startAngle + totalAngle * pct;
  const fillEnd = pt(fillAngle);
  const largeArc = (totalAngle * pct) > 180 ? 1 : 0;
  const fillPath = `M ${trackStart.x} ${trackStart.y} A ${r} ${r} 0 ${largeArc} 1 ${fillEnd.x} ${fillEnd.y}`;

  // Animate the fill path length on mount
  useEffect(() => {
    if (!arcRef.current) return;
    const length = arcRef.current.getTotalLength();
    arcRef.current.style.strokeDasharray = String(length);
    arcRef.current.style.strokeDashoffset = String(length);
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (arcRef.current) {
          arcRef.current.style.transition = 'stroke-dashoffset 1.8s cubic-bezier(0.4,0,0.2,1)';
          arcRef.current.style.strokeDashoffset = '0';
        }
      });
    });
  }, [pct]);

  return (
    <div className={clsx('flex flex-col items-center', className)}>
      <svg
        width={viewBox}
        height={viewBox * 0.75}
        viewBox={`0 0 ${viewBox} ${viewBox * 0.75}`}
        className="overflow-visible"
        aria-label={`Confidence: ${Math.round(pct * 100)}%`}
      >
        {/* Gradient definition */}
        <defs>
          <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#EF4444" />
            <stop offset="50%" stopColor="#F59E0B" />
            <stop offset="100%" stopColor="#10B981" />
          </linearGradient>
          {/* Glow filter */}
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Track */}
        <path
          d={trackPath}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth={sw}
          strokeLinecap="round"
        />

        {/* Gradient fill arc */}
        <path
          ref={arcRef}
          d={fillPath}
          fill="none"
          stroke={color}
          strokeWidth={sw}
          strokeLinecap="round"
          filter="url(#glow)"
        />

        {/* Center value */}
        <text x={cx} y={cy - 8} textAnchor="middle" dominantBaseline="middle">
          <tspan
            className={`${textSize} font-bold fill-slate-800`}
            style={{ fontSize: size === 'sm' ? 22 : size === 'md' ? 32 : 40, fontWeight: 700, fill: '#1e293b' }}
          >
            {Math.round(pct * 100)}%
          </tspan>
        </text>
        <text x={cx} y={cy + (size === 'sm' ? 16 : 22)} textAnchor="middle">
          <tspan
            style={{ fontSize: size === 'sm' ? 10 : 12, fontWeight: 500, fill: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}
          >
            Confidence
          </tspan>
        </text>

        {/* Min/Max labels */}
        <text x={trackStart.x - 4} y={trackStart.y + 14} textAnchor="middle"
          style={{ fontSize: 10, fill: '#94a3b8' }}>0%</text>
        <text x={trackEnd.x + 4} y={trackEnd.y + 14} textAnchor="middle"
          style={{ fontSize: 10, fill: '#94a3b8' }}>100%</text>
      </svg>

      {/* Color-coded label */}
      {showLabel && (
        <div className="mt-1">
          <span
            className={clsx(
              'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold',
              pct >= 0.85
                ? 'bg-success-50 text-success-700'
                : pct >= 0.65
                ? 'bg-warning-50 text-warning-700'
                : 'bg-danger-50 text-danger-700',
            )}
          >
            <span
              className={clsx(
                'w-1.5 h-1.5 rounded-full',
                pct >= 0.85 ? 'bg-success-500' : pct >= 0.65 ? 'bg-warning-500' : 'bg-danger-500',
              )}
            />
            {label}
          </span>
        </div>
      )}
    </div>
  );
};

export default ConfidenceGauge;
