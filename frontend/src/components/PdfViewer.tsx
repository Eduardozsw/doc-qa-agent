import { useEffect, useMemo, useRef, useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import { ChevronLeft, ChevronRight, Loader2, X, AlertTriangle } from 'lucide-react';
import { DARK } from '../constants/theme';

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

function displayName(namespace: string): string {
  const parts = namespace.split('_');
  return parts.length > 2 ? parts.slice(2).join('_') : namespace;
}

function normalize(s: string): string {
  return s.toLowerCase().normalize('NFKC').replace(/\s+/g, ' ').trim();
}

/** Procura `trecho` (ou suas ~8 primeiras palavras) no texto acumulado dos spans do text layer
 * e marca os spans correspondentes com a classe de destaque. Retorna se algo foi encontrado. */
function highlightTrecho(container: HTMLElement, trecho: string): boolean {
  container.querySelectorAll('.pdf-highlight-span').forEach(el => el.classList.remove('pdf-highlight-span'));

  const spans = Array.from(container.querySelectorAll<HTMLSpanElement>('.textLayer span'));
  if (spans.length === 0 || !trecho.trim()) return false;

  let acc = '';
  const ranges: { start: number; end: number; span: HTMLSpanElement }[] = [];
  for (const span of spans) {
    const text = normalize(span.textContent || '');
    if (!text) continue;
    const start = acc.length;
    acc += text;
    ranges.push({ start, end: acc.length, span });
    acc += ' ';
  }

  const target = normalize(trecho);
  let needle = target;
  let idx = acc.indexOf(needle);
  if (idx === -1) {
    const words = target.split(' ').filter(Boolean).slice(0, 8);
    needle = words.join(' ');
    idx = needle ? acc.indexOf(needle) : -1;
  }
  if (idx === -1) return false;

  const idxEnd = idx + needle.length;
  let matched = false;
  for (const { start, end, span } of ranges) {
    if (end > idx && start < idxEnd) {
      span.classList.add('pdf-highlight-span');
      matched = true;
    }
  }
  return matched;
}

export type PdfViewerRequest = {
  namespace: string;
  documento: string;
  pagina: number | null;
  trecho: string;
};

type AuthFetch = (url: string, options?: RequestInit) => Promise<Response>;

interface PdfViewerProps {
  open: boolean;
  request: PdfViewerRequest | null;
  onClose: () => void;
  authFetch: AuthFetch;
  isMobile: boolean;
}

export function PdfViewer({ open, request, onClose, authFetch, isMobile }: PdfViewerProps) {
  const cacheRef = useRef<Map<string, string>>(new Map());
  const pageContainerRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [pageWidth, setPageWidth] = useState(480);

  const namespace = request?.namespace ?? null;

  // Busca (ou reaproveita do cache) o PDF sempre que o namespace pedido muda.
  useEffect(() => {
    if (!namespace) return;
    let cancelled = false;

    const cached = cacheRef.current.get(namespace);
    if (cached) {
      setBlobUrl(cached);
      setError(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    setBlobUrl(null);
    setNumPages(null);

    authFetch(`/api/files/${namespace}/pdf`)
      .then(res => {
        if (!res.ok) {
          throw new Error(res.status === 404 ? 'Documento não encontrado.' : `Erro ${res.status} ao carregar o PDF.`);
        }
        return res.blob();
      })
      .then(blob => {
        if (cancelled) return;
        const url = URL.createObjectURL(blob);
        cacheRef.current.set(namespace, url);
        setBlobUrl(url);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Erro ao carregar o PDF.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [namespace, authFetch]);

  // Vai para a página pedida sempre que uma nova citação é aberta.
  useEffect(() => {
    if (request) setPageNumber(request.pagina && request.pagina > 0 ? request.pagina : 1);
  }, [request?.namespace, request?.pagina, request?.trecho]); // eslint-disable-line react-hooks/exhaustive-deps

  // Revoga todos os blobs em cache quando o visualizador é desmontado de vez.
  useEffect(() => {
    const cache = cacheRef.current;
    return () => {
      cache.forEach(url => URL.revokeObjectURL(url));
      cache.clear();
    };
  }, []);

  // Largura responsiva da página, seguindo a largura do painel.
  useEffect(() => {
    if (!open) return;
    const el = panelRef.current;
    if (!el) return;
    const update = () => setPageWidth(Math.max(240, el.clientWidth - 32));
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [open]);

  const handleRenderTextLayerSuccess = () => {
    if (!request?.trecho || !pageContainerRef.current) return;
    highlightTrecho(pageContainerRef.current, request.trecho);
  };

  const title = useMemo(() => (request ? displayName(request.documento || request.namespace) : ''), [request]);

  const panelStyle: React.CSSProperties = isMobile
    ? {
        position: 'fixed', inset: 0, zIndex: 60,
        background: '#0d0d1a',
        transform: open ? 'translateX(0)' : 'translateX(100%)',
        transition: 'transform 0.25s ease',
        display: 'flex', flexDirection: 'column',
      }
    : {
        width: open ? '45%' : 0,
        minWidth: open ? 360 : 0,
        flexShrink: 0,
        overflow: 'hidden',
        borderLeft: `1px solid ${DARK.border}`,
        background: '#0d0d1a',
        transition: 'width 0.25s ease, min-width 0.25s ease',
        display: 'flex', flexDirection: 'column',
      };

  return (
    <div ref={panelRef} style={panelStyle}>
      {open && (
        <>
          {/* Header */}
          <div style={{
            flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '12px 16px', borderBottom: `1px solid ${DARK.border}`,
          }}>
            <span className="text-sm font-sans font-medium truncate" style={{ color: DARK.text, maxWidth: '80%' }} title={title}>
              {title}
            </span>
            <button
              onClick={onClose}
              title="Fechar visualizador"
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                width: 28, height: 28, borderRadius: 6,
                background: 'transparent', border: `1px solid ${DARK.border}`,
                color: DARK.textMuted, cursor: 'pointer',
              }}
            >
              <X style={{ width: 14, height: 14 }} />
            </button>
          </div>

          {/* Navegação de página */}
          <div style={{
            flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12,
            padding: '8px 16px', borderBottom: `1px solid ${DARK.border}`,
          }}>
            <button
              onClick={() => setPageNumber(p => Math.max(1, p - 1))}
              disabled={pageNumber <= 1}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                width: 26, height: 26, borderRadius: 6,
                background: 'transparent', border: `1px solid ${DARK.border}`,
                color: pageNumber <= 1 ? DARK.textFaint : DARK.textMuted,
                cursor: pageNumber <= 1 ? 'default' : 'pointer',
              }}
            >
              <ChevronLeft style={{ width: 14, height: 14 }} />
            </button>
            <span className="text-xs font-sans" style={{ color: DARK.textMuted, minWidth: 90, textAlign: 'center' }}>
              {numPages ? `p. ${pageNumber} de ${numPages}` : '—'}
            </span>
            <button
              onClick={() => setPageNumber(p => (numPages ? Math.min(numPages, p + 1) : p + 1))}
              disabled={!!numPages && pageNumber >= numPages}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                width: 26, height: 26, borderRadius: 6,
                background: 'transparent', border: `1px solid ${DARK.border}`,
                color: (!!numPages && pageNumber >= numPages) ? DARK.textFaint : DARK.textMuted,
                cursor: (!!numPages && pageNumber >= numPages) ? 'default' : 'pointer',
              }}
            >
              <ChevronRight style={{ width: 14, height: 14 }} />
            </button>
          </div>

          {/* Conteúdo */}
          <div style={{ flex: 1, overflow: 'auto', padding: 16, display: 'flex', justifyContent: 'center' }} ref={pageContainerRef}>
            {loading && (
              <div className="flex flex-col items-center gap-2 mt-8">
                <Loader2 className="w-5 h-5 animate-spin" style={{ color: DARK.accent }} />
                <span className="text-xs font-sans" style={{ color: DARK.textMuted }}>Carregando documento…</span>
              </div>
            )}
            {!loading && error && (
              <div className="flex flex-col items-center gap-2 mt-8 text-center px-4">
                <AlertTriangle className="w-5 h-5" style={{ color: '#f87171' }} />
                <span className="text-xs font-sans" style={{ color: DARK.textMuted }}>{error}</span>
              </div>
            )}
            {!loading && !error && blobUrl && (
              <Document
                file={blobUrl}
                onLoadSuccess={({ numPages: n }) => setNumPages(n)}
                loading={
                  <div className="flex flex-col items-center gap-2 mt-8">
                    <Loader2 className="w-5 h-5 animate-spin" style={{ color: DARK.accent }} />
                  </div>
                }
                error={
                  <span className="text-xs font-sans" style={{ color: DARK.textMuted }}>Não foi possível exibir o PDF.</span>
                }
              >
                <Page
                  pageNumber={pageNumber}
                  width={pageWidth}
                  onRenderTextLayerSuccess={handleRenderTextLayerSuccess}
                />
              </Document>
            )}
          </div>
        </>
      )}
    </div>
  );
}
