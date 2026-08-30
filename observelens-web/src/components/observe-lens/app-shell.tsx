'use client';

import {
  ActionButton,
  DropdownControl,
} from '@/components/observe-lens/interactive-controls';
import { cn } from '@/lib/utils';
import {
  Bell,
  BellOff,
  Box,
  Building2,
  CheckCheck,
  ClipboardCheck,
  CircleAlert,
  FileText,
  HelpCircle,
  Info,
  LogOut,
  MessageSquare,
  Search,
  Settings,
  Siren,
  UserRound,
  X,
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

type HeaderNotificationKind = 'incident' | 'inspection' | 'system';

interface HeaderNotification {
  id: string;
  description: string;
  href: string;
  kind: HeaderNotificationKind;
  read: boolean;
  timeLabel: string;
  title: string;
}

const notificationStorageKey = 'observelens.header-notifications.v1';

const defaultHeaderNotifications: HeaderNotification[] = [
  {
    id: 'incident-payment-latency',
    title: 'Payment API latency is elevated',
    description: 'P95 latency exceeded the 800 ms threshold in production.',
    kind: 'incident',
    timeLabel: '12m ago',
    href: '/incidents',
    read: false,
  },
  {
    id: 'inspection-completed',
    title: 'Inspection completed',
    description: 'The checkout dependency inspection is ready to review.',
    kind: 'inspection',
    timeLabel: '1h ago',
    href: '/tasks/inspections',
    read: false,
  },
  {
    id: 'knowledge-base-updated',
    title: 'Knowledge base indexing completed',
    description: '42 documents are available for investigation context.',
    kind: 'system',
    timeLabel: 'Yesterday',
    href: '/knowledge/files',
    read: true,
  },
];

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
  knowledge: [
    { href: '/knowledge/files', label: 'Knowledge Bases' },
    { href: '/knowledge/test', label: 'Test' },
  ],
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
      src="/images/observelens-icon.svg?v=4"
      width={32}
    />
  );
}

function NotificationKindIcon({
  kind,
}: {
  kind: HeaderNotificationKind;
}): ReactNode {
  const iconClassName = 'size-4';

  if (kind === 'incident') {
    return <CircleAlert aria-hidden="true" className={iconClassName} />;
  }
  if (kind === 'inspection') {
    return <ClipboardCheck aria-hidden="true" className={iconClassName} />;
  }
  return <Info aria-hidden="true" className={iconClassName} />;
}

function NotificationCenter(): ReactNode {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<HeaderNotification[]>(
    defaultHeaderNotifications,
  );
  const panelRef = useRef<HTMLDivElement>(null);
  const unreadCount = notifications.filter(
    (notification) => !notification.read,
  ).length;

  useEffect(() => {
    const storedNotifications = window.localStorage.getItem(
      notificationStorageKey,
    );
    if (!storedNotifications) {
      return;
    }
    try {
      setNotifications(JSON.parse(storedNotifications) as HeaderNotification[]);
    } catch {
      window.localStorage.removeItem(notificationStorageKey);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(
      notificationStorageKey,
      JSON.stringify(notifications),
    );
  }, [notifications]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const closeOnOutsidePointer = (event: MouseEvent) => {
      if (
        event.target instanceof Node &&
        !panelRef.current?.contains(event.target)
      ) {
        setIsOpen(false);
      }
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', closeOnOutsidePointer);
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      document.removeEventListener('mousedown', closeOnOutsidePointer);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [isOpen]);

  const markAsRead = (notificationID: string) => {
    setNotifications((currentNotifications) =>
      currentNotifications.map((notification) =>
        notification.id === notificationID
          ? { ...notification, read: true }
          : notification,
      ),
    );
  };

  const markAllAsRead = () => {
    setNotifications((currentNotifications) =>
      currentNotifications.map((notification) => ({
        ...notification,
        read: true,
      })),
    );
  };

  const dismiss = (notificationID: string) => {
    setNotifications((currentNotifications) =>
      currentNotifications.filter(
        (notification) => notification.id !== notificationID,
      ),
    );
  };

  return (
    <div className="relative" ref={panelRef}>
      <button
        aria-expanded={isOpen}
        aria-haspopup="dialog"
        aria-label={`Notifications${unreadCount ? `, ${unreadCount} unread` : ''}`}
        className="relative grid size-9 place-items-center rounded-full text-slate-700 transition hover:bg-slate-50 hover:text-blue-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-100"
        onClick={() => setIsOpen((currentValue) => !currentValue)}
        type="button"
      >
        <Bell aria-hidden="true" size={20} />
        {unreadCount ? (
          <span className="absolute -right-1.5 -top-1.5 grid min-w-4 place-items-center rounded-full bg-red-500 px-1 text-[10px] font-semibold leading-4 text-white">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        ) : null}
      </button>
      {isOpen ? (
        <section
          aria-label="Notifications"
          className="absolute right-0 top-11 z-50 w-[380px] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-xl shadow-slate-200/70"
          role="dialog"
        >
          <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-900">
                Notifications
              </h2>
              <p className="mt-0.5 text-xs text-slate-500">
                {unreadCount ? `${unreadCount} unread` : 'All caught up'}
              </p>
            </div>
            {unreadCount ? (
              <button
                className="inline-flex items-center gap-1.5 rounded px-2 py-1 text-xs font-medium text-blue-700 transition hover:bg-blue-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-100"
                onClick={markAllAsRead}
                type="button"
              >
                <CheckCheck aria-hidden="true" size={15} />
                Mark all read
              </button>
            ) : null}
          </div>
          {notifications.length ? (
            <div className="max-h-[360px] overflow-y-auto">
              {notifications.map((notification) => (
                <div
                  className="group relative border-b border-slate-100 last:border-b-0"
                  key={notification.id}
                >
                  <Link
                    className="flex gap-3 px-4 py-3 pr-10 transition hover:bg-slate-50"
                    href={notification.href}
                    onClick={() => {
                      markAsRead(notification.id);
                      setIsOpen(false);
                    }}
                  >
                    <span
                      className={cn(
                        'mt-0.5 grid size-7 shrink-0 place-items-center rounded-full',
                        notification.kind === 'incident' &&
                          'bg-rose-50 text-rose-600',
                        notification.kind === 'inspection' &&
                          'bg-blue-50 text-blue-600',
                        notification.kind === 'system' &&
                          'bg-slate-100 text-slate-600',
                      )}
                    >
                      <NotificationKindIcon kind={notification.kind} />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex items-start justify-between gap-3">
                        <span className="text-sm font-medium text-slate-900">
                          {notification.title}
                        </span>
                        {!notification.read ? (
                          <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-blue-600" />
                        ) : null}
                      </span>
                      <span className="mt-1 block text-xs leading-5 text-slate-500">
                        {notification.description}
                      </span>
                      <span className="mt-1 block text-xs text-slate-400">
                        {notification.timeLabel}
                      </span>
                    </span>
                  </Link>
                  <button
                    aria-label={`Dismiss ${notification.title}`}
                    className="absolute right-2 top-2 grid size-7 place-items-center rounded text-slate-400 opacity-0 transition hover:bg-slate-100 hover:text-slate-700 focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-100 group-hover:opacity-100"
                    onClick={() => dismiss(notification.id)}
                    type="button"
                  >
                    <X aria-hidden="true" size={15} />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid place-items-center gap-2 px-6 py-10 text-center">
              <span className="grid size-10 place-items-center rounded-full bg-slate-100 text-slate-500">
                <BellOff aria-hidden="true" size={20} />
              </span>
              <p className="text-sm font-medium text-slate-800">
                You are all caught up
              </p>
              <p className="text-xs text-slate-500">
                New activity will appear here.
              </p>
            </div>
          )}
          <div className="border-t border-slate-200 p-2">
            <Link
              className="block rounded px-3 py-2 text-center text-sm font-medium text-blue-700 transition hover:bg-blue-50"
              href="/settings/notifications"
              onClick={() => setIsOpen(false)}
            >
              Notification settings
            </Link>
          </div>
        </section>
      ) : null}
    </div>
  );
}

function UserMenu(): ReactNode {
  return (
    <div className="group relative">
      <ActionButton
        aria-haspopup="true"
        className="grid size-9 place-items-center rounded-full border-0 bg-violet-600 p-0 text-sm font-semibold text-white shadow-none ring-0 hover:bg-violet-700"
        message="User profile opened"
        title="User menu"
        variant="ghost"
      >
        S
      </ActionButton>
      <div className="pointer-events-none invisible absolute right-0 top-full z-40 w-[240px] pt-2 opacity-0 transition duration-150 group-focus-within:pointer-events-auto group-focus-within:visible group-focus-within:opacity-100 group-hover:pointer-events-auto group-hover:visible group-hover:opacity-100">
        <div className="overflow-hidden rounded-sm border border-slate-200 bg-white py-1.5 shadow-lg shadow-slate-200/70">
          <div className="border-b border-slate-200 px-6 py-1.5">
            <p className="text-base font-medium tracking-tight text-slate-900">
              Sophie
            </p>
            <p className="text-xs text-slate-500">sophie@observelens.ai</p>
          </div>
          <ActionButton
            className="flex h-10 w-full items-center justify-start gap-3.5 bg-transparent px-6 text-left text-[17px] font-medium text-slate-800 shadow-none hover:bg-slate-50 hover:text-slate-950"
            message="Profile settings opened"
            variant="ghost"
          >
            <UserRound
              aria-hidden="true"
              className="text-slate-400"
              size={21}
              strokeWidth={1.8}
            />
            My Profile
          </ActionButton>
          <ActionButton
            className="flex h-10 w-full items-center justify-start gap-3.5 bg-transparent px-6 text-left text-[17px] font-medium text-slate-800 shadow-none hover:bg-slate-50 hover:text-slate-950"
            message="Organization settings opened"
            variant="ghost"
          >
            <Building2
              aria-hidden="true"
              className="text-slate-400"
              size={21}
              strokeWidth={1.8}
            />
            Organization
          </ActionButton>
          <div className="my-1.5 border-t border-slate-200" />
          <ActionButton
            className="flex h-10 w-full items-center justify-start gap-3.5 bg-transparent px-6 text-left text-[17px] font-medium text-slate-800 shadow-none hover:bg-slate-50 hover:text-slate-950"
            message="Sign out started"
            variant="ghost"
          >
            <LogOut
              aria-hidden="true"
              className="text-slate-400"
              size={21}
              strokeWidth={1.8}
            />
            Sign out
          </ActionButton>
        </div>
      </div>
    </div>
  );
}

function TopBar(): ReactNode {
  return (
    <header className="flex h-[66px] shrink-0 items-center justify-between border-b border-slate-200 bg-white pl-[15px] pr-5">
      <Link
        aria-label="ObserveLens home"
        className="flex items-center gap-2.5"
        href="/"
      >
        <ObserveLensLogo />
        <span className="text-lg font-semibold tracking-tight text-slate-950">
          ObserveLens
        </span>
      </Link>

      <div className="flex items-center gap-5">
        <NotificationCenter />
        <UserMenu />
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
  onChange,
  placeholder,
  value,
}: {
  onChange?: (value: string) => void;
  placeholder: string;
  value?: string;
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
        onChange={(event) => onChange?.(event.target.value)}
        placeholder={placeholder}
        type="search"
        value={value}
      />
    </label>
  );
}

export function SelectLike({ label }: { label: string }): ReactNode {
  return <DropdownControl label={label} />;
}
