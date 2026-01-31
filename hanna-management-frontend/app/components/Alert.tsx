'use client';

import React from 'react';
import { FiAlertCircle, FiCheckCircle, FiInfo, FiX } from 'react-icons/fi';

export type AlertVariant = 'success' | 'error' | 'warning' | 'info';

interface AlertProps {
  variant: AlertVariant;
  message: string;
  onClose?: () => void;
  className?: string;
}

const variantStyles = {
  success: {
    container: 'bg-green-50 border-green-200 text-green-800',
    icon: <FiCheckCircle className="w-5 h-5 text-green-500" />,
  },
  error: {
    container: 'bg-red-50 border-red-200 text-red-800',
    icon: <FiAlertCircle className="w-5 h-5 text-red-500" />,
  },
  warning: {
    container: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    icon: <FiAlertCircle className="w-5 h-5 text-yellow-500" />,
  },
  info: {
    container: 'bg-blue-50 border-blue-200 text-blue-800',
    icon: <FiInfo className="w-5 h-5 text-blue-500" />,
  },
};

export function Alert({ variant, message, onClose, className = '' }: AlertProps) {
  const styles = variantStyles[variant];

  return (
    <div
      className={`flex items-start gap-3 p-4 border rounded-lg ${styles.container} ${className}`}
      role="alert"
    >
      <div className="flex-shrink-0">{styles.icon}</div>
      <div className="flex-1 text-sm font-medium">{message}</div>
      {onClose && (
        <button
          onClick={onClose}
          className="flex-shrink-0 text-current opacity-50 hover:opacity-100 transition-opacity"
          aria-label="Close alert"
        >
          <FiX className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
