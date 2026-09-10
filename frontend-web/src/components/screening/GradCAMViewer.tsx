// ============================================================
// SafeSkin AI – GradCAMViewer Component
// Side-by-side original + Grad-CAM heatmap display
// ============================================================
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Info, Eye, EyeOff, AlertTriangle } from 'lucide-react';
import { clsx } from 'clsx';

interface GradCAMViewerProps {
  originalUrl: string;
  gradcamUrl: string;
  confidence: number;
  className?: string;
}

export const GradCAMViewer: React.FC<GradCAMViewerProps> = ({
  originalUrl,
  gradcamUrl,
  confidence,
  className,
}) => {
  const [showOverlay, setShowOverlay] = useState(true);
  const [blendMode, setBlendMode] = useState<'side-by-side' | 'overlay'>('side-by-side');

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.4 }}
      className={clsx('space-y-4', className)}
    >
      {/* ── Controls ──────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-slate-700">AI Attention Map</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-secondary-100 text-secondary-600 font-medium">
            Grad-CAM
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* Toggle overlay */}
          <button
            onClick={() => setShowOverlay((o) => !o)}
            className={clsx(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border',
              'transition-colors duration-200',
              showOverlay
                ? 'bg-secondary-50 border-secondary-200 text-secondary-700'
                : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300',
            )}
          >
            {showOverlay ? <Eye size={13} /> : <EyeOff size={13} />}
            {showOverlay ? 'Heatmap On' : 'Heatmap Off'}
          </button>
          {/* View mode */}
          <div className="flex rounded-lg border border-slate-200 overflow-hidden text-xs font-medium">
            <button
              onClick={() => setBlendMode('side-by-side')}
              className={clsx(
                'px-2.5 py-1.5 transition-colors',
                blendMode === 'side-by-side'
                  ? 'bg-primary-500 text-white'
                  : 'bg-white text-slate-600 hover:bg-slate-50',
              )}
            >
              Split
            </button>
            <button
              onClick={() => setBlendMode('overlay')}
              className={clsx(
                'px-2.5 py-1.5 transition-colors border-l border-slate-200',
                blendMode === 'overlay'
                  ? 'bg-primary-500 text-white'
                  : 'bg-white text-slate-600 hover:bg-slate-50',
              )}
            >
              Overlay
            </button>
          </div>
        </div>
      </div>

      {/* ── Image display ──────────────────────────────────────── */}
      {blendMode === 'side-by-side' ? (
        <div className="grid grid-cols-2 gap-3">
          {/* Original */}
          <div className="space-y-2">
            <p className="text-xs font-medium text-slate-500 text-center">Original</p>
            <div className="rounded-xl overflow-hidden border border-slate-200 bg-slate-50">
              <img
                src={originalUrl}
                alt="Original skin image"
                className="w-full object-contain max-h-52"
              />
            </div>
          </div>
          {/* Grad-CAM */}
          <div className="space-y-2">
            <p className="text-xs font-medium text-secondary-600 text-center font-semibold">
              AI Attention Heatmap
            </p>
            <div className="rounded-xl overflow-hidden border border-secondary-200 bg-slate-50 relative">
              {showOverlay ? (
                <img
                  src={gradcamUrl}
                  alt="Grad-CAM attention heatmap"
                  className="w-full object-contain max-h-52"
                />
              ) : (
                <img
                  src={originalUrl}
                  alt="Original image without heatmap"
                  className="w-full object-contain max-h-52 opacity-50"
                />
              )}
              {/* Confidence badge */}
              <div className="absolute top-2 right-2 px-2 py-0.5 rounded-md bg-black/50 text-white text-xs font-semibold">
                {Math.round(confidence * 100)}% conf.
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Overlay mode: stack images */
        <div className="space-y-2">
          <p className="text-xs font-medium text-slate-500 text-center">Overlay View</p>
          <div className="rounded-xl overflow-hidden border border-slate-200 relative">
            <img
              src={originalUrl}
              alt="Original"
              className="w-full object-contain max-h-64"
            />
            {showOverlay && (
              <img
                src={gradcamUrl}
                alt="Heatmap overlay"
                className="absolute inset-0 w-full h-full object-contain opacity-60 mix-blend-multiply"
              />
            )}
          </div>
        </div>
      )}

      {/* ── Color scale legend ─────────────────────────────────── */}
      <div className="flex items-center gap-3">
        <span className="text-xs text-slate-500 shrink-0">Attention:</span>
        <div className="flex-1 h-2 rounded-full overflow-hidden"
          style={{ background: 'linear-gradient(to right, #1e3a5f, #0ea5e9, #10b981, #f59e0b, #ef4444)' }}
        />
        <div className="flex items-center justify-between text-xs text-slate-400 gap-2">
          <span>Low</span>
          <span>High</span>
        </div>
      </div>

      {/* ── Disclaimer ─────────────────────────────────────────── */}
      <div className="flex items-start gap-2 p-3 rounded-xl bg-blue-50/80 border border-blue-100">
        <Info size={14} className="text-blue-500 shrink-0 mt-0.5" />
        <p className="text-xs text-blue-700 leading-relaxed">
          <strong>What is Grad-CAM?</strong> Gradient-weighted Class Activation Mapping highlights
          the image regions that most influenced the AI's decision — shown in red/yellow (high
          attention). This is for transparency only and does not constitute a clinical finding.
        </p>
      </div>

      {/* Low confidence warning */}
      {confidence < 0.65 && (
        <div className="flex items-start gap-2 p-3 rounded-xl bg-warning-50 border border-warning-200">
          <AlertTriangle size={14} className="text-warning-600 shrink-0 mt-0.5" />
          <p className="text-xs text-warning-700">
            Low confidence ({Math.round(confidence * 100)}%) — the heatmap may not be reliable.
            Please consult a dermatologist.
          </p>
        </div>
      )}
    </motion.div>
  );
};

export default GradCAMViewer;
