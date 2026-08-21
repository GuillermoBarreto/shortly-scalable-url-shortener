import { FormEvent, useState } from 'react';
import { Check, Copy, ExternalLink, QrCode } from 'lucide-react';
import { Link as LinkType, request } from '../lib/api';

export function ShortenForm() {
  const [url, setUrl] = useState('');
  const [alias, setAlias] = useState('');
  const [result, setResult] = useState<LinkType | null>(null);
  const [error, setError] = useState('');
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied' | 'failed'>('idle');
  const [loading, setLoading] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    setCopyStatus('idle');
    try {
      setResult(await request<LinkType>('/links', {
        method: 'POST',
        body: JSON.stringify({ original_url: url, custom_alias: alias || null }),
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to shorten URL');
    } finally {
      setLoading(false);
    }
  }

  async function copyShortUrl() {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result.short_url);
      setCopyStatus('copied');
    } catch {
      setCopyStatus('failed');
    }
  }

  return (
    <section aria-labelledby="shorten-heading" className="card mx-auto max-w-4xl">
      <h2 id="shorten-heading" className="sr-only">Shorten a link</h2>
      <form onSubmit={submit} className="grid gap-3 md:grid-cols-[1fr_12rem_auto]">
        <label className="sr-only" htmlFor="long-url">Long URL</label>
        <input required id="long-url" type="url" value={url} onChange={(e) => setUrl(e.target.value)} className="input" placeholder="Paste a long URL" />
        <label className="sr-only" htmlFor="alias">Custom alias</label>
        <input id="alias" value={alias} onChange={(e) => setAlias(e.target.value)} className="input" placeholder="Custom alias" />
        <button disabled={loading} className="btn-primary">{loading ? 'Working…' : 'Shorten link'}</button>
      </form>
      {error && <p role="alert" className="mt-4 text-sm font-semibold text-red-700">{error}</p>}
      {result && (
        <div className="mt-5 flex flex-col gap-4 rounded-2xl bg-mint/40 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-widest text-ink/50">Your short link</p>
            <a className="font-bold text-forest underline" href={result.short_url}>{result.short_url}</a>
          </div>
          <div className="flex items-center gap-2">
            <button className="btn-secondary !p-3" aria-label={copyStatus === 'copied' ? 'Copied short URL' : 'Copy short URL'} onClick={copyShortUrl}>
              {copyStatus === 'copied' ? <Check size={18} /> : <Copy size={18} />}
            </button>
            <a className="btn-secondary !p-3" aria-label="Open short URL" href={result.short_url} target="_blank" rel="noreferrer"><ExternalLink size={18} /></a>
            <a className="btn-secondary !p-3" aria-label="QR code requires an account" href="/register"><QrCode size={18} /></a>
            <span className="sr-only" role="status" aria-live="polite">
              {copyStatus === 'copied' ? 'Short URL copied to clipboard' : copyStatus === 'failed' ? 'Unable to copy short URL' : ''}
            </span>
          </div>
        </div>
      )}
    </section>
  );
}
