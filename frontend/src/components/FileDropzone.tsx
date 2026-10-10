/**
 * FileDropzone — drag-and-drop or click-to-browse file uploader.
 *
 * Security:
 * - Validates file extension client-side (defence in depth; backend is canonical).
 * - Enforces max 10 MB client-side. Backend re-validates.
 * - The actual file upload happens via `uploadDocument` which sends FormData;
 *   no `dangerouslySetInnerHTML` or eval is used anywhere.
 */

import { useCallback } from 'react';
import { useDropzone, type FileRejection } from 'react-dropzone';

const MAX_SIZE = 10 * 1024 * 1024; // 10 MB
const ACCEPT_EXT = ['.txt', '.pdf', '.docx'];

export interface FileDropzoneProps {
  onFile: (file: File) => void;
  disabled?: boolean;
}

function isAllowed(name: string): boolean {
  const lower = name.toLowerCase();
  return ACCEPT_EXT.some((ext) => lower.endsWith(ext));
}

export function FileDropzone({ onFile, disabled }: FileDropzoneProps) {
  const onDrop = useCallback(
    (accepted: File[], rejections: FileRejection[]) => {
      if (rejections.length > 0) return;
      const f = accepted[0];
      if (f && isAllowed(f.name)) onFile(f);
    },
    [onFile],
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    multiple: false,
    maxSize: MAX_SIZE,
    disabled,
    accept: {
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
  });

  return (
    <div
      {...getRootProps({
        className: `dropzone${isDragActive ? ' dropzone--active' : ''}${
          isDragReject ? ' dropzone--reject' : ''
        }${disabled ? ' dropzone--disabled' : ''}`,
      })}
      data-testid="file-dropzone"
      role="button"
      tabIndex={0}
      aria-disabled={disabled}
    >
      <input {...getInputProps()} data-testid="file-input" />
      <p className="dropzone__hint">
        {isDragActive
          ? 'Drop the file here…'
          : 'Drag & drop a .txt, .pdf, or .docx (max 10 MB), or click to browse'}
      </p>
    </div>
  );
}
