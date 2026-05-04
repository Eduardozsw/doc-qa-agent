import { useRef, useState, DragEvent, ChangeEvent } from 'react';
import { Plus, X, Loader2, Trash2, FileText } from 'lucide-react';
import { IngestStatus } from '../hooks/useFileManagement';
import { JobState } from '../hooks/useJobPolling';
import { DARK } from '../constants/theme';
import { DrivePickerButton } from './DrivePickerButton';

function displayName(namespace: string): string {
  const parts = namespace.split('_');
  return parts.length > 2 ? parts.slice(2).join('_') : namespace;
}

interface PDFUploadProps {
  indexedFiles: string[];
  pendingFiles: File[];
  searchSelected: Set<string>;
  onToggleSearch: (name: string) => void;
  onAddFiles: (newFiles: File[]) => void;
  onRemovePending: (index: number) => void;
  onRemoveIndexed: (namespaces: string[]) => void;
  onIngestFromDrive: (files: Array<{ id: string; name: string }>, accessToken: string) => void;
  onSubmit: () => void;
  slotsAvailable: number;
  isLoading: boolean;
  ingestStatus: IngestStatus;
  ingestError: string | null;
  jobStatuses: JobState[];
}

export function PDFUpload({
  indexedFiles, pendingFiles, searchSelected, onToggleSearch, onAddFiles,
  onRemovePending, onRemoveIndexed, onIngestFromDrive, onSubmit, slotsAvailable, isLoading,
  ingestStatus, ingestError, jobStatuses,
}: PDFUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const pickPdfs = (fileList: FileList) => {
    const pdfs = Array.from(fileList).filter(f => f.type === 'application/pdf');
    if (pdfs.length) onAddFiles(pdfs);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    pickPdfs(e.dataTransfer.files);
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) pickPdfs(e.target.files);
    e.target.value = '';
  };

  const selectedCount = searchSelected.size;
  const totalFiles = indexedFiles.length;

  const statusText = () => {
    if (ingestStatus === 'error') return ingestError ?? 'Erro ao indexar';
    if (ingestStatus === 'loading') return 'Indexando...';
    if (totalFiles === 0) return 'Nenhum documento';
    if (selectedCount === 0 || selectedCount === totalFiles) return `${totalFiles} documento${totalFiles !== 1 ? 's' : ''}`;
    return `${selectedCount} de ${totalFiles} selecionado${selectedCount !== 1 ? 's' : ''}`;
  };

  const statusDotColor =
    ingestStatus === 'error' ? '#f87171' :
    ingestStatus === 'partial' ? DARK.accent :
    ingestStatus === 'ready' && totalFiles > 0 ? '#34d399' :
    'rgba(255,255,255,0.2)';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>

      {/* Header */}
      <div style={{
        padding: '14px 16px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        borderBottom: `1px solid ${DARK.borderLight}`,
        flexShrink: 0,
      }}>
        <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.35)' }}>
          Documentos
        </span>
        {slotsAvailable > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <DrivePickerButton
              onFilesSelected={onIngestFromDrive}
              disabled={isLoading}
            />
            <button
              onClick={() => inputRef.current?.click()}
              title="Adicionar PDF"
              style={{
                width: 24, height: 24, borderRadius: 6,
                background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                cursor: 'pointer', color: DARK.accent,
              }}
            >
              <Plus style={{ width: 13, height: 13 }} />
            </button>
          </div>
        )}
        <input ref={inputRef} type="file" accept="application/pdf" multiple style={{ display: 'none' }} onChange={handleChange} />
      </div>

      {/* File list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>

        {/* Indexed files */}
        {indexedFiles.map(name => {
          const sel = searchSelected.has(name);
          return (
            <div
              key={name}
              onClick={() => onToggleSearch(name)}
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '7px 10px', borderRadius: 8, cursor: 'pointer', marginBottom: 2,
                background: sel ? 'rgba(255,255,255,0.06)' : 'transparent',
                transition: 'background 0.15s',
              }}
            >
              <div style={{
                width: 16, height: 16, borderRadius: 4, flexShrink: 0,
                border: `1px solid ${sel ? 'rgba(245,158,11,0.4)' : 'rgba(255,255,255,0.2)'}`,
                background: sel ? 'rgba(245,158,11,0.15)' : 'transparent',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                transition: 'all 0.15s',
              }}>
                {sel && <div style={{ width: 8, height: 8, background: DARK.accent, borderRadius: 2 }} />}
              </div>
              <span style={{
                fontSize: 12, flex: 1,
                overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis',
                color: sel ? 'rgba(255,255,255,0.85)' : 'rgba(255,255,255,0.6)',
                transition: 'color 0.15s',
              }}>
                {displayName(name)}
              </span>
              <button
                onClick={e => { e.stopPropagation(); onRemoveIndexed([name]); }}
                title="Remover"
                style={{
                  width: 20, height: 20, borderRadius: 4, flexShrink: 0,
                  background: 'transparent', border: 'none', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: 'rgba(255,255,255,0.3)',
                }}
              >
                <Trash2 style={{ width: 11, height: 11 }} />
              </button>
            </div>
          );
        })}

        {/* Pending files */}
        {pendingFiles.map((file, i) => (
          <div
            key={i}
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '7px 10px', borderRadius: 8, marginBottom: 2,
              background: 'rgba(14,165,233,0.06)', border: '1px solid rgba(14,165,233,0.15)',
            }}
          >
            <FileText style={{ width: 12, height: 12, color: '#38bdf8', flexShrink: 0 }} />
            <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.65)', flex: 1, overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>
              {file.name}
            </span>
            <button
              onClick={() => onRemovePending(i)}
              disabled={isLoading}
              style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'rgba(255,255,255,0.35)', display: 'flex', alignItems: 'center' }}
            >
              <X style={{ width: 12, height: 12 }} />
            </button>
          </div>
        ))}

        {/* Jobs em andamento */}
        {jobStatuses.map(job => {
          const isProcessing = job.status === 'pending' || job.status === 'processing';
          const isError = job.status === 'error';
          const isDone = job.status === 'done';
          if (isDone) return null;
          return (
            <div
              key={job.job_id}
              style={{
                display: 'flex', alignItems: 'flex-start', gap: 8,
                padding: '7px 10px', borderRadius: 8, marginBottom: 2,
                background: isError ? 'rgba(239,68,68,0.06)' : 'rgba(14,165,233,0.06)',
                border: `1px solid ${isError ? 'rgba(239,68,68,0.15)' : 'rgba(14,165,233,0.15)'}`,
              }}
            >
              {isProcessing && (
                <Loader2 style={{ width: 12, height: 12, color: '#38bdf8', flexShrink: 0, marginTop: 2 }} className="animate-spin" />
              )}
              {isError && <X style={{ width: 12, height: 12, color: '#f87171', flexShrink: 0, marginTop: 2 }} />}
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <div style={{
                  fontSize: 12,
                  color: isError ? '#f87171' : 'rgba(255,255,255,0.65)',
                  overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis',
                }}>
                  {job.filename}
                </div>
                {isError && job.error && (
                  <div style={{ fontSize: 10, color: '#f87171', marginTop: 1, lineHeight: '1.3' }}>
                    {job.error}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Empty state */}
        {totalFiles === 0 && pendingFiles.length === 0 && jobStatuses.length === 0 && (
          <div style={{ padding: '20px 8px', textAlign: 'center', color: 'rgba(255,255,255,0.2)', fontSize: 12 }}>
            Nenhum documento ainda
          </div>
        )}
      </div>

      {/* Drop zone */}
      {slotsAvailable > 0 && (
        <div
          onClick={() => inputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={e => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          style={{
            margin: '0 8px 8px',
            border: `1px dashed ${dragging ? DARK.accent : 'rgba(255,255,255,0.1)'}`,
            borderRadius: 10, padding: '12px 8px',
            textAlign: 'center', cursor: 'pointer',
            color: dragging ? DARK.accent : 'rgba(255,255,255,0.25)',
            fontSize: 11, transition: 'all 0.15s',
            background: dragging ? 'rgba(245,158,11,0.04)' : 'transparent',
          }}
        >
          <div style={{ fontSize: 16, marginBottom: 3 }}>☁</div>
          Arraste PDFs aqui
        </div>
      )}

      {/* Submit */}
      {pendingFiles.length > 0 && (
        <button
          onClick={onSubmit}
          disabled={isLoading}
          style={{
            margin: '0 8px 8px',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            padding: '8px 12px', borderRadius: 8,
            background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`,
            color: DARK.bg, border: 'none',
            cursor: isLoading ? 'default' : 'pointer',
            fontSize: 12, fontWeight: 600,
            opacity: isLoading ? 0.6 : 1,
            flexShrink: 0,
          }}
        >
          {isLoading
            ? <><Loader2 style={{ width: 12, height: 12 }} /> Indexando...</>
            : `Enviar ${pendingFiles.length} arquivo${pendingFiles.length > 1 ? 's' : ''}`}
        </button>
      )}

      {/* Status bar */}
      <div style={{ padding: '10px 16px', borderTop: `1px solid ${DARK.borderLight}`, flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: statusDotColor, flexShrink: 0 }} />
          <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)' }}>{statusText()}</span>
        </div>
      </div>
    </div>
  );
}
