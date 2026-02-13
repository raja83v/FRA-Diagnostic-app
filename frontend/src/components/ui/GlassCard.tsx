/**
 * Glassmorphic card component with hover effects.
 */
import type { ReactNode } from 'react';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  onClick?: () => void;
}

const paddingClasses = {
  none: '',
  sm: 'p-4',
  md: 'p-5',
  lg: 'p-6',
};

export default function GlassCard({ 
  children, 
  className = '', 
  hover = true,
  padding = 'md',
  onClick,
}: GlassCardProps) {
  return (
    <div 
      className={`${hover ? 'glass-card' : 'glass-card-static'} ${paddingClasses[padding]} ${className}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {children}
    </div>
  );
}
