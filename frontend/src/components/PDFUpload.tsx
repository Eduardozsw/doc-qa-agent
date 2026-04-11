import { useRef, useState, DragEvent, ChangeEvent } from 'react';
import { FileText, UploadCloud, X, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

type IngestStatus = 'idle' | 'loading' | 'ready' | 'error';

interface PDFUploadProps {
  file: File | null;
  onFileChange: (file: File | null) => void;
  ingestStatus: IngestStatus;
  ingestError: string | null;
}

export function PDFUpload({ file, onFileChange, ingestStatus, ingestError }: PDFUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.type === 'application/pdf') {
      onFileChange(dropped);
    }
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) onFileChange(selected);
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="w-full">
      <label className="block text-sm font-medium text-slate-600 mb-2">
        Arquivo PDF
      </label>

      {file ? (
        <div className="space-y-2">
          <div className="flex items-center gap-3 p-4 bg-sky-50 border border-sky-200 rounded-xl">
            <div className="flex-shrink-0 w-10 h-10 bg-sky-100 rounded-lg flex items-center justify-center">
              <FileText className="w-5 h-5 text-sky-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-800 truncate">{file.name}</p>
              <p className="text-xs text-slate-400 mt-0.5">{formatSize(file.size)}</p>
            </div>
            <button
              onClick={() => { onFileChange(null); if (inputRef.current) inputRef.current.value = ''; }}
              className="flex-shrink-0 w-7 h-7 rounded-full bg-slate-100 hover:bg-red-100 flex items-center justify-center transition-colors group"
            >
              <X className="w-3.5 h-3.5 text-slate-400 group-hover:text-red-500 transition-colors" />
            </button>
          </div>

          {ingestStatus === 'loading' && (
            <div className="flex items-center gap-2 px-1 text-xs text-slate-500">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Indexando PDF...</span>
            </div>
          )}

          {ingestStatus === 'ready' && (
            <div className="flex items-center gap-2 px-1 text-xs text-emerald-600">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Pronto para perguntas</span>
            </div>
          )}

          {ingestStatus === 'error' && (
            <div className="flex items-center gap-2 px-1 text-xs text-red-500">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>{ingestError ?? 'Falha ao indexar o PDF. Tente novamente.'}</span>
            </div>
          )}
        </div>
      ) : (
        <div
          onClick={() => inputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          className={`
            relative cursor-pointer rounded-xl border-2 border-dashed transition-all duration-200 p-8
            flex flex-col items-center justify-center gap-3
            ${dragging
              ? 'border-sky-400 bg-sky-50 scale-[1.01]'
              : 'border-slate-200 bg-slate-50 hover:border-sky-300 hover:bg-sky-50/50'}
          `}
        >
          <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${dragging ? 'bg-sky-100' : 'bg-white shadow-sm'}`}>
            <UploadCloud className={`w-6 h-6 transition-colors ${dragging ? 'text-sky-500' : 'text-slate-400'}`} />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-slate-600">
              Arraste seu PDF aqui ou <span className="text-sky-600">clique para selecionar</span>
            </p>
            <p className="text-xs text-slate-400 mt-1">Somente arquivos .pdf</p>
          </div>
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={handleChange}
          />
        </div>
      )}
    </div>
  );
}
