'use client';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { CheckCircle2, ChevronDown } from 'lucide-react';
import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { useState } from 'react';

interface ActionButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  className?: string;
  message: string;
  size?: 'default' | 'sm';
  variant?: 'default' | 'outline' | 'ghost';
}

export function ActionButton({
  children,
  className,
  message,
  onClick,
  size,
  variant,
  ...props
}: ActionButtonProps): ReactNode {
  const [feedback, setFeedback] = useState<string | null>(null);

  return (
    <>
      <Button
        className={className}
        onClick={(event) => {
          onClick?.(event);
          setFeedback(message);
          window.setTimeout(() => setFeedback(null), 1800);
        }}
        size={size}
        variant={variant}
        {...props}
      >
        {children}
      </Button>
      {feedback ? (
        <div className="fixed bottom-5 right-5 z-50 flex items-center gap-2 rounded-md border border-emerald-200 bg-white px-4 py-3 text-sm font-medium text-slate-800 shadow-lg shadow-slate-200">
          <CheckCircle2
            aria-hidden="true"
            className="text-emerald-600"
            size={17}
          />
          {feedback}
        </div>
      ) : null}
    </>
  );
}

interface DropdownControlProps {
  label: string;
  options?: string[];
}

export function DropdownControl({
  label,
  options = ['All', 'Critical', 'Warning', 'Healthy'],
}: DropdownControlProps): ReactNode {
  const [isOpen, setIsOpen] = useState(false);
  const [selected, setSelected] = useState(label);

  return (
    <div className="relative">
      <button
        aria-expanded={isOpen}
        className="inline-flex h-10 min-w-[132px] items-center justify-between gap-3 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-700 hover:bg-slate-50"
        onClick={() => setIsOpen((value) => !value)}
        type="button"
      >
        {selected}
        <ChevronDown
          aria-hidden="true"
          className={cn('transition', isOpen && 'rotate-180')}
          size={16}
        />
      </button>
      {isOpen ? (
        <div className="absolute left-0 top-11 z-30 w-44 overflow-hidden rounded-md border border-slate-200 bg-white py-1 shadow-lg">
          {options.map((option) => (
            <button
              className={cn(
                'block h-9 w-full px-3 text-left text-sm text-slate-700 hover:bg-blue-50 hover:text-blue-700',
                selected === option && 'bg-blue-50 text-blue-700',
              )}
              key={option}
              onClick={() => {
                setSelected(option);
                setIsOpen(false);
              }}
              type="button"
            >
              {option}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
