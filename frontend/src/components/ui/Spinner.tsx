/**
 * Loading spinner component.
 */

type SpinnerSize = 'sm' | 'md' | 'lg';

interface SpinnerProps {
  size?: SpinnerSize;
  className?: string;
}

const sizeClasses: Record<SpinnerSize, string> = {
  sm: 'spinner-sm',
  md: '',
  lg: 'spinner-lg',
};

export default function Spinner({ size = 'md', className = '' }: SpinnerProps) {
  return <div className={`spinner ${sizeClasses[size]} ${className}`} />;
}

export function LoadingOverlay({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-4">
      <Spinner size="lg" />
      <p className="text-sm text-(--text-muted)">{message}</p>
    </div>
  );
}
