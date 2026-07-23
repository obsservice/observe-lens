'use client';

import {
  ActionButton,
  DropdownControl,
} from '@/components/observe-lens/interactive-controls';
import { cn } from '@/lib/utils';
import {
  Bell,
  Box,
  ChevronDown,
  ClipboardCheck,
  FileText,
  HelpCircle,
  MessageSquare,
  Search,
  Settings,
  Siren,
} from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';
import { useEffect, useRef, useState } from 'react';

type PrimarySection =
  'chat' | 'incidents' | 'tasks' | 'entity' | 'knowledge' | 'settings';

interface PrimaryNavItem {
  href: string;
  icon: LucideIcon;
  label: string;
  section: PrimarySection;
}

interface SecondaryNavItem {
  href: string;
  label: string;
}

interface AppShellProps {
  activeItem?: string;
  activeSection: PrimarySection;
  children: ReactNode;
}

const primaryNavItems: PrimaryNavItem[] = [
  { href: '/', icon: MessageSquare, label: 'Chat', section: 'chat' },
  { href: '/incidents', icon: Siren, label: 'Incidents', section: 'incidents' },
  {
    href: '/tasks/inspections',
    icon: ClipboardCheck,
    label: 'Tasks',
    section: 'tasks',
  },
  { href: '/entity/search', icon: Box, label: 'Entity', section: 'entity' },
  {
    href: '/knowledge/files',
    icon: FileText,
    label: 'Knowledge',
    section: 'knowledge',
  },
  {
    href: '/settings/models',
    icon: Settings,
    label: 'Settings',
    section: 'settings',
  },
];

export const secondaryNavigation: Record<PrimarySection, SecondaryNavItem[]> = {
  chat: [
    { href: '/', label: 'Sessions' },
    { href: '/chat/observations', label: 'Observations' },
  ],
  incidents: [
    { href: '/incidents', label: 'Incidents' },
    { href: '/incidents/integrations', label: 'Integrations' },
  ],
  tasks: [{ href: '/tasks/inspections', label: 'Inspections' }],
  entity: [
    { href: '/entity/search', label: 'Search' },
    { href: '/entity/topology', label: 'Topology' },
  ],
  knowledge: [{ href: '/knowledge/files', label: 'Files' }],
  settings: [
    { href: '/settings/models', label: 'Models' },
    { href: '/settings/notifications', label: 'Notifications' },
  ],
};

function ObserveLensLogo(): ReactNode {
  return (
    <Image
      alt=""
      className="size-8 rounded-md object-cover"
      height={32}
      src="/images/observelens-icon.png"
      width={32}
    />
  );
}

function TopBar(): ReactNode {
  return (
    <header className="flex h-[66px] shrink-0 items-center justify-between border-b border-slate-200 bg-white px-5">
      <div className="flex items-center gap-4">
        <Link className="flex items-center gap-3" href="/">
          <ObserveLensLogo />
          <span className="text-lg font-semibold text-slate-950">
            ObserveLens
          </span>
        </Link>
      </div>

      <div className="flex items-center gap-5">
        <ActionButton
          className="relative size-9 rounded-full border-0 bg-transparent p-0 text-slate-700 shadow-none ring-0 hover:bg-transparent hover:text-blue-600"
          message="Notifications panel opened"
          title="Notifications"
          variant="ghost"
        >
          <Bell aria-hidden="true" size={20} />
          <span className="absolute -right-1.5 -top-1.5 grid size-4 place-items-center rounded-full bg-red-500 text-[10px] font-semibold text-white">
            3
          </span>
        </ActionButton>
        <ActionButton
          className="grid size-9 place-items-center rounded-full border-0 bg-violet-600 p-0 text-sm font-semibold text-white shadow-none ring-0 hover:bg-violet-600"
          message="User profile opened"
          title="Current user"
          variant="ghost"
        >
          S
        </ActionButton>
        <ActionButton
          className="size-8 rounded-full border-0 bg-transparent p-0 text-slate-700 shadow-none ring-0 hover:bg-transparent hover:text-blue-600"
          message="Account menu opened"
          title="Account menu"
          variant="ghost"
        >
          <ChevronDown aria-hidden="true" size={18} />
        </ActionButton>
      </div>
    </header>
  );
}

function FloatingSubmenu({
  activeItem,
  item,
  onClose,
}: {
  activeItem?: string;
  item: PrimaryNavItem;
  onClose: () => void;
}): ReactNode {
  const secondaryItems = secondaryNavigation[item.section];

  if (item.section === 'chat' || secondaryItems.length <= 1) {
    return null;
  }

  return (
    <div className="absolute left-[58px] top-0 z-40 min-w-[180px] overflow-hidden rounded-r-md border border-slate-200 bg-white py-2 shadow-lg shadow-slate-200">
      <div className="px-4 pb-2 pt-1 text-xs text-slate-400">{item.label}</div>
      <div>
        {secondaryItems.map((secondaryItem) => (
          <Link
            className={cn(
              'flex h-9 items-center whitespace-nowrap px-4 text-sm font-medium text-slate-800 hover:bg-slate-50 hover:text-blue-700',
              activeItem === secondaryItem.label && 'bg-blue-50 text-blue-700',
            )}
            href={secondaryItem.href}
            key={secondaryItem.href}
            onClick={onClose}
          >
            {secondaryItem.label}
          </Link>
        ))}
      </div>
    </div>
  );
}

function FloatingTooltip({ label }: { label: string }): ReactNode {
  return (
    <div className="absolute left-[66px] top-1/2 z-40 -translate-y-1/2 whitespace-nowrap rounded-md border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-slate-800 shadow-lg shadow-slate-200">
      <span className="absolute -left-1.5 top-1/2 size-3 -translate-y-1/2 rotate-45 border-b border-l border-slate-200 bg-white" />
      {label}
    </div>
  );
}

function IconRail({
  activeItem,
  activeSection,
}: {
  activeItem?: string;
  activeSection: PrimarySection;
}): ReactNode {
  const [openSection, setOpenSection] = useState<PrimarySection | null>(null);
  const closeTimerRef = useRef<number | null>(null);

  const clearCloseTimer = () => {
    if (closeTimerRef.current) {
      window.clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
  };

  const openNavigation = (section: PrimarySection) => {
    clearCloseTimer();
    setOpenSection(section);
  };

  const scheduleCloseNavigation = () => {
    clearCloseTimer();
    closeTimerRef.current = window.setTimeout(() => {
      setOpenSection(null);
      closeTimerRef.current = null;
    }, 220);
  };

  useEffect(() => () => clearCloseTimer(), []);

  return (
    <aside className="relative flex w-[70px] shrink-0 flex-col items-center border-r border-slate-200 bg-white pb-6 pt-5">
      <nav
        aria-label="Primary navigation"
        className="flex flex-1 flex-col items-center gap-3"
      >
        {primaryNavItems.map((item) => {
          const Icon = item.icon;
          const hasFloatingMenu =
            item.section !== 'chat' &&
            secondaryNavigation[item.section].length > 1;
          const isActive = item.section === activeSection;
          const isOpen = item.section === openSection;

          return (
            <div
              className="relative"
              key={item.section}
              onBlur={(event) => {
                if (!event.currentTarget.contains(event.relatedTarget)) {
                  scheduleCloseNavigation();
                }
              }}
              onFocus={() => openNavigation(item.section)}
              onMouseEnter={() => openNavigation(item.section)}
              onMouseLeave={scheduleCloseNavigation}
            >
              {hasFloatingMenu ? (
                <button
                  aria-label={item.label}
                  aria-expanded={isOpen}
                  className={cn(
                    'grid size-10 place-items-center rounded-md text-slate-700 transition hover:bg-slate-50 hover:text-blue-600',
                    isActive && 'bg-blue-50 text-blue-600',
                  )}
                  type="button"
                >
                  <Icon aria-hidden="true" size={22} strokeWidth={1.9} />
                </button>
              ) : (
                <Link
                  aria-label={item.label}
                  className={cn(
                    'grid size-10 place-items-center rounded-md text-slate-700 transition hover:bg-slate-50 hover:text-blue-600',
                    isActive && 'bg-blue-50 text-blue-600',
                  )}
                  href={item.href}
                >
                  <Icon aria-hidden="true" size={22} strokeWidth={1.9} />
                </Link>
              )}
              {isOpen && hasFloatingMenu ? (
                <FloatingSubmenu
                  activeItem={activeItem}
                  item={item}
                  onClose={() => setOpenSection(null)}
                />
              ) : null}
              {isOpen && !hasFloatingMenu ? (
                <FloatingTooltip label={item.label} />
              ) : null}
            </div>
          );
        })}
      </nav>
      <div className="group relative">
        <ActionButton
          aria-label="Help"
          className="grid size-10 place-items-center rounded-md border-0 bg-transparent p-0 text-slate-700 shadow-none ring-0 transition hover:bg-slate-50 hover:text-blue-600"
          message="Help center opened"
          title="Help"
          variant="ghost"
        >
          <HelpCircle aria-hidden="true" size={22} strokeWidth={1.9} />
        </ActionButton>
        <div className="pointer-events-none absolute left-[66px] top-1/2 z-40 -translate-y-1/2 whitespace-nowrap rounded-md border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-slate-800 opacity-0 shadow-lg shadow-slate-200 transition group-hover:opacity-100">
          <span className="absolute -left-1.5 top-1/2 size-3 -translate-y-1/2 rotate-45 border-b border-l border-slate-200 bg-white" />
          Help
        </div>
      </div>
    </aside>
  );
}

export function AppShell({
  activeItem,
  activeSection,
  children,
}: AppShellProps): ReactNode {
  return (
    <main className="flex h-screen min-h-[760px] flex-col overflow-hidden bg-slate-50 text-slate-950">
      <TopBar />
      <div className="flex min-h-0 flex-1">
        <IconRail activeItem={activeItem} activeSection={activeSection} />
        <section className="flex min-w-0 flex-1 flex-col">{children}</section>
      </div>
    </main>
  );
}

export function PageHeader({
  actions,
  actionsClassName,
  description,
  parentTitle,
  title,
}: {
  actions?: ReactNode;
  actionsClassName?: string;
  description?: string;
  parentTitle?: string;
  title: string;
}): ReactNode {
  return (
    <div className="flex min-h-14 items-center justify-between bg-slate-50 px-6 py-3">
      <div>
        <h1 className="text-xl font-semibold tracking-normal text-slate-950">
          {parentTitle ? (
            <>
              <span className="text-slate-500">{parentTitle}</span>
              <span className="mx-2 text-slate-300">/</span>
              <span>{title}</span>
            </>
          ) : (
            title
          )}
        </h1>
        {description ? (
          <p className="mt-0.5 text-xs text-slate-500">{description}</p>
        ) : null}
      </div>
      {actions ? (
        <div className={cn('flex items-center gap-3', actionsClassName)}>
          {actions}
        </div>
      ) : null}
    </div>
  );
}

export function FilterInput({
  placeholder,
}: {
  placeholder: string;
}): ReactNode {
  return (
    <label className="relative block w-[300px]">
      <span className="sr-only">{placeholder}</span>
      <Search
        aria-hidden="true"
        className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
        size={17}
      />
      <input
        className="h-10 w-full rounded-md border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
        placeholder={placeholder}
        type="search"
      />
    </label>
  );
}

export function SelectLike({ label }: { label: string }): ReactNode {
  return <DropdownControl label={label} />;
}
