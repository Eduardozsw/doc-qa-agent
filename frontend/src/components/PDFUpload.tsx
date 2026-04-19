import { useRef, useState, DragEvent, ChangeEvent } from 'react';
import { FileText, UploadCloud, X, CheckCircle2, AlertCircle, Loader2, Send, Trash2, Search } from 'lucide-react';

type IngestStatus = 'idle' | 'loading' | 'ready' | 'error';

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
  ingestStatus: IngestStatus;
  ingestError: string | null;
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
  ingestStatus,
  ingestError,
}: PDFUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const totalSlots = indexedFiles.length + pendingFiles.length;

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const pickPdfs = (fileList: FileList) => {
    const pdfs = Array.from(fileList).filter((f) => f.type === 'application/pdf');
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
        <label className="block text-sm font-medium text-slate-600">Arquivos PDF</label>
        <span className="text-xs text-slate-400">{totalSlots}/5 arquivos</span>
      </div>

      {/* Arquivos indexados */}
      {indexedFiles.length > 0 && (
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 px-0.5">
            <Search className="w-3 h-3 text-slate-400" />
            <p className="text-xs text-slate-400">Marque os arquivos que deseja realizar a busca</p>
          </div>

          {indexedFiles.map((name) => {
            const isSelected = searchSelected.has(name);
            return (
              <div
                key={name}
                className={`flex items-center gap-3 p-3 rounded-xl border transition-colors ${
                  isSelected
                    ? 'bg-emerald-50 border-emerald-200'
                    : 'bg-slate-50 border-slate-200'
                }`}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => onToggleSearch(name)}
                  className="accent-emerald-500 cursor-pointer"
                />
                <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${isSelected ? 'bg-emerald-100' : 'bg-slate-100'}`}>
                  <FileText className={`w-4 h-4 ${isSelected ? 'text-emerald-600' : 'text-slate-400'}`} />
                </div>
                <p className="flex-1 text-sm font-medium text-slate-800 truncate">{name}</p>
                <button
                  onClick={() => onRemoveIndexed([name])}
                  className="flex-shrink-0 w-7 h-7 rounded-full bg-slate-100 hover:bg-red-100 flex items-center justify-center transition-colors group"
                  title="Remover arquivo"
                >
                  <Trash2 className="w-3.5 h-3.5 text-slate-400 group-hover:text-red-500 transition-colors" />
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Arquivos pendentes */}
      {pendingFiles.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs text-slate-400 px-0.5">Aguardando envio</p>
          {pendingFiles.map((file, i) => (
            <div key={i} className="flex items-center gap-3 p-3 bg-sky-50 border border-sky-200 rounded-xl">
              <div className="flex-shrink-0 w-8 h-8 bg-sky-100 rounded-lg flex items-center justify-center">
                <FileText className="w-4 h-4 text-sky-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-800 truncate">{file.name}</p>
                <p className="text-xs text-slate-400">{formatSize(file.size)}</p>
              </div>
              <button
                onClick={() => onRemovePending(i)}
                disabled={ingestStatus === 'loading'}
                className="flex-shrink-0 w-7 h-7 rounded-full bg-slate-100 hover:bg-red-100 flex items-center justify-center transition-colors group disabled:opacity-40"
              >
                <X className="w-3.5 h-3.5 text-slate-400 group-hover:text-red-500 transition-colors" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Área de drop */}
      {slotsAvailable > 0 && (
        <div
          onClick={() => inputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          className={`
            relative cursor-pointer rounded-xl border-2 border-dashed transition-all duration-200 p-6
            flex flex-col items-center justify-center gap-2
            ${dragging
              ? 'border-sky-400 bg-sky-50 scale-[1.01]'
              : 'border-slate-200 bg-slate-50 hover:border-sky-300 hover:bg-sky-50/50'}
          `}
        >
          <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${dragging ? 'bg-sky-100' : 'bg-white shadow-sm'}`}>
            <UploadCloud className={`w-5 h-5 transition-colors ${dragging ? 'text-sky-500' : 'text-slate-400'}`} />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-slate-600">
              Arraste PDFs aqui ou <span className="text-sky-600">clique para selecionar</span>
            </p>
            <p className="text-xs text-slate-400 mt-0.5">
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

      {/* Botão enviar */}
      {pendingFiles.length > 0 && (
        <button
          onClick={onSubmit}
          disabled={ingestStatus === 'loading'}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-sky-600 hover:bg-sky-700 disabled:bg-sky-300 text-white text-sm font-medium rounded-xl transition-colors"
        >
          {ingestStatus === 'loading' ? (
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
        <div className="flex items-center gap-2 px-1 text-xs text-emerald-600">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>
            {searchSelected.size === 0 || searchSelected.size === indexedFiles.length
              ? 'Buscando em todos os arquivos'
              : `Buscando em ${searchSelected.size} de ${indexedFiles.length} arquivo${indexedFiles.length > 1 ? 's' : ''}`}
          </span>
        </div>
      )}

      {ingestStatus === 'error' && (
        <div className="flex items-center gap-2 px-1 text-xs text-red-500">
          <AlertCircle className="w-3.5 h-3.5" />
          <span>{ingestError ?? 'Falha ao indexar. Tente novamente.'}</span>
        </div>
      )}
    </div>
  );
}
