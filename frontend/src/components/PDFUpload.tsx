import { useRef, useState, DragEvent, ChangeEvent } from 'react';
import { FileText, UploadCloud, X, CheckCircle2, AlertCircle, Loader2, Send, Trash2, Search } from 'lucide-react';
import { IngestStatus } from '../hooks/useFileManagement';
import { DARK } from '../constants/theme';

interface PDFUploadProps {
  indexedFiles: string[];
  pendingFiles: File[];
  searchSelected: Set<string>;
  onToggleSearch: (name: string) => void;
  onAddFiles: (newFiles: File[]) => void;
  onRemovePending: (index: number) => void;
  onRemoveIndexed: (namespaces: string[]) => void;
  onSubmit: () => void;
  slotsAvailable: number;
  isLoading: boolean;
  ingestStatus: IngestStatus;
  ingestError: string | null;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function PDFUpload({
  indexedFiles,
  pendingFiles,
  searchSelected,
  onToggleSearch,
  onAddFiles,
  onRemovePending,
  onRemoveIndexed,
  onSubmit,
  slotsAvailable,
  isLoading,
  ingestStatus,
  ingestError,
}: PDFUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const usedSlots = indexedFiles.length + pendingFiles.length;

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

  return (
    <div className="w-full space-y-3">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-sans font-medium" style={{ color: DARK.textMuted }}>
          Arquivos PDF
        </label>
        <span className="text-xs font-sans" style={{ color: DARK.textFaint }}>{usedSlots}/5 arquivos</span>
      </div>

      {/* Indexed files */}
      {indexedFiles.length > 0 && (
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 px-0.5">
            <Search className="w-3 h-3" style={{ color: DARK.textFaint }} />
            <p className="text-xs font-sans" style={{ color: DARK.textFaint }}>Marque os arquivos que deseja incluir na busca</p>
          </div>
          {indexedFiles.map((name) => {
            const isSelected = searchSelected.has(name);
            return (
              <div
                key={name}
                className="flex items-center gap-3 p-3 rounded-xl transition-colors"
                style={{
                  background: isSelected ? DARK.emeraldSubtle : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${isSelected ? DARK.emeraldBorder : DARK.border}`,
                }}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => onToggleSearch(name)}
                  className="cursor-pointer accent-emerald-400"
                />
                <div
                  className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ background: isSelected ? DARK.emeraldSubtle : 'rgba(255,255,255,0.05)' }}
                >
                  <FileText className="w-4 h-4" style={{ color: isSelected ? DARK.emerald : DARK.textFaint }} />
                </div>
                <p className="flex-1 text-sm font-sans font-medium truncate" style={{ color: DARK.text }}>{name}</p>
                <button
                  onClick={() => onRemoveIndexed([name])}
                  className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-colors group"
                  style={{ background: 'rgba(255,255,255,0.05)' }}
                  title="Remover arquivo"
                >
                  <Trash2 className="w-3.5 h-3.5 transition-colors group-hover:text-red-400" style={{ color: DARK.textFaint }} />
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Pending files */}
      {pendingFiles.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs font-sans px-0.5" style={{ color: DARK.textFaint }}>Aguardando envio</p>
          {pendingFiles.map((file, i) => (
            <div
              key={i}
              className="flex items-center gap-3 p-3 rounded-xl"
              style={{ background: DARK.skySubtle, border: `1px solid ${DARK.skyBorder}` }}
            >
              <div
                className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ background: 'rgba(14,165,233,0.15)' }}
              >
                <FileText className="w-4 h-4" style={{ color: '#38bdf8' }} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-sans font-medium truncate" style={{ color: DARK.text }}>{file.name}</p>
                <p className="text-xs font-sans" style={{ color: DARK.textFaint }}>{formatSize(file.size)}</p>
              </div>
              <button
                onClick={() => onRemovePending(i)}
                disabled={isLoading}
                className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-colors group disabled:opacity-40"
                style={{ background: 'rgba(255,255,255,0.05)' }}
              >
                <X className="w-3.5 h-3.5 transition-colors group-hover:text-red-400" style={{ color: DARK.textFaint }} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Drop zone */}
      {slotsAvailable > 0 && (
        <div
          onClick={() => inputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          className="relative cursor-pointer rounded-xl border-2 border-dashed transition-all duration-200 p-6 flex flex-col items-center justify-center gap-2"
          style={{
            borderColor: dragging ? DARK.accent : DARK.border,
            background: dragging ? DARK.accentSubtle : 'rgba(255,255,255,0.02)',
            transform: dragging ? 'scale(1.01)' : 'scale(1)',
          }}
        >
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center transition-colors"
            style={{ background: dragging ? DARK.accentSubtle : 'rgba(255,255,255,0.05)' }}
          >
            <UploadCloud className="w-5 h-5 transition-colors" style={{ color: dragging ? DARK.accent : DARK.textFaint }} />
          </div>
          <div className="text-center">
            <p className="text-sm font-sans" style={{ color: DARK.textMuted }}>
              Arraste PDFs aqui ou{' '}
              <span style={{ color: DARK.accent }}>clique para selecionar</span>
            </p>
            <p className="text-xs font-sans mt-0.5" style={{ color: DARK.textFaint }}>
              Até {slotsAvailable} arquivo{slotsAvailable > 1 ? 's' : ''} restante{slotsAvailable > 1 ? 's' : ''}
            </p>
          </div>
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf"
            multiple
            className="hidden"
            onChange={handleChange}
          />
        </div>
      )}

      {/* Submit button */}
      {pendingFiles.length > 0 && (
        <button
          onClick={onSubmit}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-sm font-sans font-semibold transition-all duration-200 hover:opacity-90 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`, color: DARK.bg }}
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Indexando...
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              Enviar {pendingFiles.length} arquivo{pendingFiles.length > 1 ? 's' : ''}
            </>
          )}
        </button>
      )}

      {ingestStatus === 'ready' && (
        <div className="flex items-center gap-2 px-1 text-xs font-sans" style={{ color: DARK.emerald }}>
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>
            {searchSelected.size === 0 || searchSelected.size === indexedFiles.length
              ? 'Buscando em todos os arquivos'
              : `Buscando em ${searchSelected.size} de ${indexedFiles.length} arquivo${indexedFiles.length > 1 ? 's' : ''}`}
          </span>
        </div>
      )}

      {ingestStatus === 'error' && (
        <div className="flex items-center gap-2 px-1 text-xs font-sans" style={{ color: '#f87171' }}>
          <AlertCircle className="w-3.5 h-3.5" />
          <span>{ingestError ?? 'Falha ao indexar. Tente novamente.'}</span>
        </div>
      )}
    </div>
  );
}
