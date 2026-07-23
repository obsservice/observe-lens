import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

const toneClassNames = {
  blue: 'bg-blue-50 text-blue-700 ring-blue-200',
  emerald: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  amber: 'bg-amber-50 text-amber-700 ring-amber-200',
  red: 'bg-red-50 text-red-700 ring-red-200',
  slate: 'bg-slate-50 text-slate-600 ring-slate-200',
  violet: 'bg-violet-50 text-violet-700 ring-violet-200',
} as const;

export type StatusTone = keyof typeof toneClassNames;

interface StatusBadgeProps {
  children: ReactNode;
  tone?: StatusTone;
}

export function StatusBadge({
  children,
  tone = 'slate',
}: StatusBadgeProps): ReactNode {
  return (
    <span
      className={cn(
        'inline-flex h-6 items-center rounded px-2 text-xs font-medium ring-1',
        toneClassNames[tone],
      )}
    >
      {children}
    </span>
  );
}
