'use client';

import { useRef, useEffect, useState } from 'react';
import { FiZap, FiX, FiExternalLink, FiCopy, FiCheck, FiMessageCircle } from 'react-icons/fi';

const QUICK_PROMPTS = [
  { label: 'Size my system', prompt: 'I need solar sizing help for a 3-bedroom home with 2 fridges, 3 TVs, lights, and phone charging. Share a safe starter bundle.' },
  { label: 'Backup for business', prompt: 'Recommend a backup solar kit for a small shop with POS, lights, laptops, and a display fridge. Budget-conscious.' },
  { label: 'Off-grid package', prompt: 'I want a fully off-grid package for a rural site. Include panels, batteries, inverter, and installation estimate.' },
  { label: 'Best value bundle', prompt: 'Show me the best-value solar bundle with good warranty and components you recommend.' },
  { label: 'Furniture quote', prompt: 'I need a quote for custom living room furniture: sofa set, coffee table, TV unit. Modern style, quality wood.' },
];

interface AIAssistantFABProps {
  whatsappNumber: string;
  open: boolean;
  onToggle: () => void;
}

export default function AIAssistantFAB({ whatsappNumber, open, onToggle }: AIAssistantFABProps) {
  const [prompt, setPrompt] = useState(QUICK_PROMPTS[0].prompt);
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied'>('idle');
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (open && panelRef.current && !panelRef.current.contains(e.target as Node)) {
        onToggle();
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open, onToggle]);

  const waLink = whatsappNumber
    ? `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(prompt)}`
    : null;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(prompt);
      setCopyStatus('copied');
      setTimeout(() => setCopyStatus('idle'), 2000);
    } catch {
      setCopyStatus('idle');
    }
  };

  const launch = (p: string) => {
    setPrompt(p);
    if (waLink) {
      window.open(`https://wa.me/${whatsappNumber}?text=${encodeURIComponent(p)}`, '_blank', 'noopener,noreferrer');
    } else {
      navigator.clipboard.writeText(p).catch(() => {});
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3" ref={panelRef}>
      {/* Panel */}
      {open && (
        <div className="w-80 sm:w-96 bg-white rounded-2xl shadow-2xl border border-purple-100 overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-sky-500 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FiZap className="w-4 h-4 text-white" />
              <span className="text-white font-bold text-sm">AI Shopping Assistant</span>
            </div>
            <button onClick={onToggle} className="text-white/70 hover:text-white transition">
              <FiX className="w-4 h-4" />
            </button>
          </div>

          <div className="p-4 space-y-3">
            <p className="text-xs text-gray-500">Pick a quick prompt or write your own, then open WhatsApp to chat with our AI.</p>

            {/* Quick prompts */}
            <div className="flex flex-wrap gap-1.5">
              {QUICK_PROMPTS.map((p) => (
                <button
                  key={p.label}
                  onClick={() => launch(p.prompt)}
                  className="text-xs px-3 py-1.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200 hover:bg-sky-100 font-semibold transition"
                >
                  {p.label}
                </button>
              ))}
            </div>

            {/* Textarea */}
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={3}
              className="w-full text-sm px-3 py-2 border border-gray-200 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-purple-400 text-gray-800 resize-none"
              placeholder="Describe what you need…"
            />

            {/* Actions */}
            <div className="flex gap-2">
              {waLink ? (
                <a
                  href={`https://wa.me/${whatsappNumber}?text=${encodeURIComponent(prompt)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-orange-500 hover:bg-orange-600 text-white rounded-xl font-bold text-xs transition"
                >
                  <FiExternalLink className="w-3.5 h-3.5" />
                  Open in WhatsApp
                </a>
              ) : (
                <button
                  onClick={copy}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-orange-500 hover:bg-orange-600 text-white rounded-xl font-bold text-xs transition"
                >
                  <FiMessageCircle className="w-3.5 h-3.5" />
                  Copy Prompt
                </button>
              )}
              <button
                onClick={copy}
                className="px-3 py-2.5 border border-gray-200 rounded-xl text-gray-600 hover:bg-gray-50 transition text-xs flex items-center gap-1"
              >
                {copyStatus === 'copied' ? <FiCheck className="w-3.5 h-3.5 text-green-500" /> : <FiCopy className="w-3.5 h-3.5" />}
                {copyStatus === 'copied' ? 'Copied' : 'Copy'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* FAB */}
      <button
        onClick={onToggle}
        className={`w-14 h-14 rounded-full shadow-xl flex items-center justify-center transition-all duration-300 ${
          open
            ? 'bg-gray-700 hover:bg-gray-800'
            : 'bg-orange-500 hover:bg-orange-600 animate-pulse-slow'
        }`}
        aria-label="AI Shopping Assistant"
        title="AI Shopping Assistant"
      >
        {open ? <FiX className="w-6 h-6 text-white" /> : <FiZap className="w-6 h-6 text-white" />}
      </button>
    </div>
  );
}
