import { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';
import { PDFUpload } from './components/PDFUpload';
import { QuestionInput } from './components/QuestionInput';
import { AnswerSection } from './components/AnswerSection';

type IngestStatus = 'idle' | 'loading' | 'ready' | 'error';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [question, setQuestion] = useState('');
  const [submittedQuestion, setSubmittedQuestion] = useState<string | null>(null);
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [ingestStatus, setIngestStatus] = useState<IngestStatus>('idle');
  const [ingestError, setIngestError] = useState<string | null>(null);

  useEffect(() => {
    if (!file) {
      setIngestStatus('idle');
      setIngestError(null);
      return;
    }

    const controller = new AbortController();

    setIngestStatus('loading');
    setIngestError(null);
    setAnswer(null);
    setSubmittedQuestion(null);

    const formData = new FormData();
    formData.append('file', file);

    fetch('/api/ingest', { method: 'POST', body: formData, signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`Erro ${res.status}`);
        setIngestStatus('ready');
      })
      .catch((err: unknown) => {
        if (err instanceof Error && err.name === 'AbortError') return;
        const message = err instanceof Error ? err.message : 'Falha ao indexar o PDF. Tente novamente.';
        setIngestStatus('error');
        setIngestError(message);
      });

    return () => controller.abort();
  }, [file]);

  const handleSubmit = async () => {
    if (ingestStatus !== 'ready' || !question.trim()) return;

    const currentQuestion = question.trim();
    setSubmittedQuestion(currentQuestion);
    setQuestion('');
    setAnswer(null);
    setLoading(true);

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: currentQuestion }),
      });

      if (!res.ok) throw new Error(`Erro ${res.status}`);

      const data = await res.json();
      setAnswer(data.resposta);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Erro ao consultar. Tente novamente.';
      setAnswer(`Erro: ${message}`);
    } finally {
      setLoading(false);
    }
  };

  const canSubmit = ingestStatus === 'ready' && question.trim().length > 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-sky-50/30">
      <div className="max-w-5xl mx-auto px-4 py-10 sm:px-6 lg:px-8">

        <header className="mb-10 text-center">
          <div className="inline-flex items-center gap-2 bg-white border border-slate-200 rounded-full px-4 py-1.5 mb-5 shadow-sm">
            <Sparkles className="w-4 h-4 text-sky-500" />
            <span className="text-xs font-medium text-slate-500 tracking-wide uppercase">RAG Assistant</span>
          </div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">
            Pergunte ao seu documento
          </h1>
          <p className="text-slate-500 mt-2 text-sm max-w-md mx-auto">
            Carregue um PDF e faça perguntas. A IA vai ler o conteúdo e responder com base nele.
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">

          <div className="space-y-5">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 space-y-6">
              <PDFUpload
                file={file}
                onFileChange={setFile}
                ingestStatus={ingestStatus}
                ingestError={ingestError}
              />
              <div className="border-t border-slate-100" />
              <QuestionInput
                question={question}
                onQuestionChange={setQuestion}
                onSubmit={handleSubmit}
                disabled={!canSubmit}
                loading={loading}
              />
            </div>

            {!file && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-xs text-amber-700">
                Selecione um arquivo PDF para habilitar o envio de perguntas.
              </div>
            )}
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 min-h-[320px] flex flex-col">
            <div className="flex items-center gap-2 mb-5 pb-4 border-b border-slate-100">
              <div className="w-2 h-2 rounded-full bg-emerald-400" />
              <h2 className="text-sm font-semibold text-slate-700">Resposta</h2>
            </div>
            <div className="flex-1">
              <AnswerSection
                answer={answer}
                loading={loading}
                question={submittedQuestion}
              />
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

export default App;
