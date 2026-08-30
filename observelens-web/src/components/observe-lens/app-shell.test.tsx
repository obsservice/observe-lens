import { fireEvent, render, screen } from '@testing-library/react';
import type { ComponentProps, ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('next/image', () => ({
  default: (props: ComponentProps<'img'>) => <img {...props} />,
}));

vi.mock('next/link', () => ({
  default: ({
    children,
    href,
    ...props
  }: ComponentProps<'a'> & { children: ReactNode }) => (
    <a href={typeof href === 'string' ? href : ''} {...props}>
      {children}
    </a>
  ),
}));

import { AppShell } from './app-shell';

function renderAppShell(): void {
  render(
    <AppShell activeSection="chat">
      <div>Page content</div>
    </AppShell>,
  );
}

describe('AppShell notifications', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('marks all notifications as read and persists the change', () => {
    renderAppShell();

    fireEvent.click(
      screen.getByRole('button', { name: /notifications, 2 unread/i }),
    );

    expect(screen.getByRole('dialog', { name: 'Notifications' })).toBeVisible();
    fireEvent.click(screen.getByRole('button', { name: /mark all read/i }));

    expect(screen.getByText('All caught up')).toBeVisible();
    expect(
      window.localStorage.getItem('observelens.header-notifications.v1'),
    ).toContain('"read":true');
  });

  it('dismisses an item and closes on Escape', () => {
    renderAppShell();

    fireEvent.click(
      screen.getByRole('button', { name: /notifications, 2 unread/i }),
    );
    fireEvent.click(
      screen.getByRole('button', {
        name: /dismiss payment api latency is elevated/i,
      }),
    );

    expect(
      screen.queryByText('Payment API latency is elevated'),
    ).not.toBeInTheDocument();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(
      screen.queryByRole('dialog', { name: 'Notifications' }),
    ).not.toBeInTheDocument();
  });
});
