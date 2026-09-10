// ============================================================
// SafeSkin AI – ImageUploader Component
// Drag-and-drop + file picker + camera capture
// ============================================================
import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  Camera,
  ImagePlus,
  X,
  CheckCircle,
  AlertCircle,
  FileImage,
} from 'lucide-react';
import { clsx } from 'clsx';
import Button from '@/components/ui/Button';

interface ImageUploaderProps {
  onFileSelect: (file: File) => void;
  preview: string | null;
  onRemove: () => void;
  disabled?: boolean;
}

const MAX_SIZE = 10 * 1024 * 1024; // 10 MB
const ACCEPTED_TYPES = { 'image/jpeg': ['.jpg', '.jpeg'], 'image/png': ['.png'] };

export const ImageUploader: React.FC<ImageUploaderProps> = ({
  onFileSelect,
  preview,
  onRemove,
  disabled = false,
}) => {
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: { errors: { code: string }[] }[]) => {
      setError(null);

      if (rejectedFiles.length > 0) {
        const code = rejectedFiles[0]?.errors[0]?.code;
        if (code === 'file-too-large') {
          setError('File is too large. Maximum size is 10 MB.');
        } else if (code === 'file-invalid-type') {
          setError('Please upload a JPEG or PNG image.');
        } else {
          setError('Invalid file. Please try again.');
        }
        return;
      }

      if (acceptedFiles[0]) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    [onFileSelect],
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject, isDragAccept } =
    useDropzone({
      onDrop,
      accept: ACCEPTED_TYPES,
      maxSize: MAX_SIZE,
      maxFiles: 1,
      disabled: disabled || !!preview,
      noClick: !!preview,
    });

  // Camera capture handler
  const handleCameraCapture = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.capture = 'environment'; // Use rear camera on mobile
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) onFileSelect(file);
    };
    input.click();
  };

  // Format file size display
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="w-full">
      {/* ── Preview state ─────────────────────────────────────── */}
      <AnimatePresence mode="wait">
        {preview ? (
          <motion.div
            key="preview"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3 }}
            className="relative rounded-2xl overflow-hidden border-2 border-primary-200 bg-primary-50/30"
          >
            <img
              src={preview}
              alt="Selected skin image preview"
              className="w-full max-h-80 object-contain"
            />

            {/* Overlay bar */}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent px-4 py-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-white">
                  <CheckCircle size={16} className="text-success-400" />
                  <span className="text-sm font-medium">Image ready for analysis</span>
                </div>
                {!disabled && (
                  <button
                    onClick={onRemove}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/20 backdrop-blur-sm text-white text-xs font-medium hover:bg-white/30 transition-colors"
                  >
                    <X size={14} />
                    Remove
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        ) : (
          /* ── Drop zone ────────────────────────────────────── */
          <motion.div
            key="dropzone"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div
              {...getRootProps()}
              className={clsx(
                'relative border-2 border-dashed rounded-2xl p-10',
                'flex flex-col items-center justify-center gap-4 text-center',
                'transition-all duration-300 cursor-pointer',
                'min-h-[240px]',
                // States
                isDragAccept && 'border-success-400 bg-success-50/50',
                isDragReject && 'border-danger-400 bg-danger-50/50',
                isDragActive && !isDragAccept && !isDragReject && 'border-primary-400 bg-primary-50/80',
                !isDragActive && 'border-primary-200 bg-primary-50/30 hover:border-primary-400 hover:bg-primary-50/60',
                disabled && 'opacity-60 cursor-not-allowed',
              )}
            >
              <input {...getInputProps()} />

              {/* Animated background circles */}
              <div className="absolute inset-0 overflow-hidden rounded-2xl pointer-events-none">
                <div className={clsx(
                  'absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full',
                  'transition-all duration-500',
                  isDragActive
                    ? 'w-64 h-64 bg-primary-100/80 opacity-100'
                    : 'w-32 h-32 bg-primary-100/40 opacity-50',
                )} />
              </div>

              {/* Icon */}
              <div className={clsx(
                'relative z-10 w-16 h-16 rounded-2xl flex items-center justify-center',
                'transition-all duration-300',
                isDragAccept ? 'bg-success-100' : isDragReject ? 'bg-danger-100' : 'bg-primary-100',
              )}>
                {isDragAccept ? (
                  <CheckCircle size={32} className="text-success-500" />
                ) : isDragReject ? (
                  <AlertCircle size={32} className="text-danger-500" />
                ) : isDragActive ? (
                  <motion.div
                    animate={{ rotate: [0, -10, 10, 0] }}
                    transition={{ duration: 0.5, repeat: Infinity }}
                  >
                    <Upload size={32} className="text-primary-500" />
                  </motion.div>
                ) : (
                  <ImagePlus size={32} className="text-primary-500" />
                )}
              </div>

              {/* Text */}
              <div className="relative z-10 space-y-1.5">
                <p className="text-base font-semibold text-slate-700">
                  {isDragActive
                    ? isDragReject
                      ? 'Invalid file type'
                      : 'Drop image here'
                    : 'Drag & drop your skin image'}
                </p>
                <p className="text-sm text-slate-500">
                  or click to browse your files
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Supports JPEG, PNG • Max size: 10 MB
                </p>
              </div>

              {/* Accepted formats */}
              <div className="relative z-10 flex items-center gap-2">
                <span className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-white border border-slate-200 text-xs text-slate-500">
                  <FileImage size={12} />
                  JPEG
                </span>
                <span className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-white border border-slate-200 text-xs text-slate-500">
                  <FileImage size={12} />
                  PNG
                </span>
              </div>
            </div>

            {/* Camera capture button */}
            <div className="mt-4 flex items-center justify-center gap-3">
              <div className="h-px flex-1 bg-slate-200" />
              <span className="text-xs text-slate-400 font-medium">or</span>
              <div className="h-px flex-1 bg-slate-200" />
            </div>

            <Button
              variant="outline"
              size="md"
              icon={<Camera size={16} />}
              onClick={handleCameraCapture}
              disabled={disabled}
              className="mt-4 w-full"
            >
              Take a Photo
            </Button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Error message ──────────────────────────────────────── */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="mt-3 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-danger-50 border border-danger-200 text-danger-700 text-sm"
          >
            <AlertCircle size={16} className="shrink-0" />
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Photo tips ─────────────────────────────────────────── */}
      {!preview && (
        <div className="mt-4 p-4 rounded-xl bg-blue-50 border border-blue-100">
          <p className="text-xs font-semibold text-blue-700 mb-2 flex items-center gap-1.5">
            📸 Tips for best results
          </p>
          <ul className="text-xs text-blue-600 space-y-1 list-none">
            <li>✓ Good lighting — natural light is best</li>
            <li>✓ Image sharp and in focus</li>
            <li>✓ Lesion fills most of the frame</li>
            <li>✓ No blurriness or heavy shadows</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default ImageUploader;
