'use client';

import { FiCheck, FiAlertCircle, FiX } from 'react-icons/fi';

export interface ToastData {
  id: number;
  message: string;
  type: 'success' | 'error';
}

interface ToastStackProps {
  toasts: ToastData[];
  onDismiss: (id: number) => void;
}

export default function ToastStack({ toasts, onDismiss }: ToastStackProps) {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-24 left-1/2 -translate-x-1/2 z-[60] flex flex-col items-center gap-2 w-full max-w-sm px-4 pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`shop-toast-enter pointer-events-auto flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-lg border text-sm font-semibold w-full ${
            t.type === 'success'
              ? 'bg-white border-green-200 text-gray-800'
              : 'bg-white border-red-200 text-gray-800'
          }`}
        >
          <span className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${
            t.type === 'success' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
          }`}>
            {t.type === 'success' ? <FiCheck className="w-3.5 h-3.5" /> : <FiAlertCircle className="w-3.5 h-3.5" />}
          </span>
          <span className="flex-1">{t.message}</span>
          <button onClick={() => onDismiss(t.id)} className="text-gray-300 hover:text-gray-500 transition flex-shrink-0">
            <FiX className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
