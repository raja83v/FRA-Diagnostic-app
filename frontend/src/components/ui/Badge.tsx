/**
 * Status badge component with semantic colors.
 */
import type { ReactNode } from 'react';

type BadgeVariant = 'critical' | 'warning' | 'success' | 'info' | 'neutral';

interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
  icon?: ReactNode;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  critical: 'badge-critical',
  warning: 'badge-warning',
  success: 'badge-success',
  info: 'badge-info',
  neutral: 'badge-neutral',
};

export default function Badge({ 
  children, 
  variant = 'neutral',
  icon,
  className = '',
}: BadgeProps) {
  return (
    <span className={`badge ${variantClasses[variant]} ${className}`}>
      {icon}
      {children}
    </span>
  );
}

// Convenience component for criticality badges
export function CriticalityBadge({ level }: { level: string }) {
  const variantMap: Record<string, BadgeVariant> = {
    critical: 'critical',
    important: 'warning',
    standard: 'success',
  };
  
  return (
    <Badge variant={variantMap[level] || 'neutral'}>
      {level.charAt(0).toUpperCase() + level.slice(1)}
    </Badge>
  );
}
