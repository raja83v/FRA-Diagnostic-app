/**
 * Form input components with glass styling.
 */
import type { InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes, ReactNode } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: ReactNode;
}

export function Input({ 
  label, 
  error, 
  icon,
  className = '',
  ...props 
}: InputProps) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label className="block text-sm font-medium text-(--text-secondary)">
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-(--text-dim)">
            {icon}
          </div>
        )}
        <input
          className={`input ${icon ? 'input-with-icon' : ''} ${error ? 'border-(--status-critical)' : ''} ${className}`}
          {...props}
        />
      </div>
      {error && (
        <p className="text-xs text-(--status-critical)">{error}</p>
      )}
    </div>
  );
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: { value: string; label: string }[];
}

export function Select({ 
  label, 
  error, 
  options,
  className = '',
  ...props 
}: SelectProps) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label className="block text-sm font-medium text-(--text-secondary)">
          {label}
        </label>
      )}
      <select
        className={`input select ${error ? 'border-(--status-critical)' : ''} ${className}`}
        {...props}
      >
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && (
        <p className="text-xs text-(--status-critical)">{error}</p>
      )}
    </div>
  );
}

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export function Textarea({ 
  label, 
  error, 
  className = '',
  ...props 
}: TextareaProps) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label className="block text-sm font-medium text-(--text-secondary)">
          {label}
        </label>
      )}
      <textarea
        className={`input min-h-25 resize-y ${error ? 'border-(--status-critical)' : ''} ${className}`}
        {...props}
      />
      {error && (
        <p className="text-xs text-(--status-critical)">{error}</p>
      )}
    </div>
  );
}
