'use client';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function Spinner({ size = 'md', className = '' }: SpinnerProps) {
  const sizeStyles = {
    sm: 'w-4 h-4 border-2',
    md: 'w-6 h-6 border-2',
    lg: 'w-8 h-8 border-3',
  };

  return (
    <span
      className={`
        inline-block rounded-full border-current border-t-transparent animate-spin
        ${sizeStyles[size]} ${className}
      `}
    />
  );
}

export function PageLoading({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="fixed inset-0 bg-base/90 flex flex-col items-center justify-center z-50">
      <Spinner size="lg" className="text-brand" />
      <span className="mt-4 text-secondary">{message}</span>
    </div>
  );
}
