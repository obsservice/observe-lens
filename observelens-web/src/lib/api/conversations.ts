import { apiRequest } from '@/lib/api/client';

export interface Conversation {
  id: number;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationPage {
  items: Conversation[];
  total: number;
  page: number;
  page_size: number;
}

export interface ConversationCreateRequest {
  title?: string;
}

export interface ConversationUpdateRequest {
  title?: string;
  status?: string;
}

export interface ListConversationsParams {
  page?: number;
  page_size?: number;
}

export const conversationQueryKeys = {
  all: ['conversations'] as const,
  commands: () => [...conversationQueryKeys.all, 'commands'] as const,
  list: (params: ListConversationsParams = {}) =>
    [...conversationQueryKeys.all, 'list', params] as const,
};

export interface ConversationCommand {
  description: string;
  name: string;
  prompt: string;
}

export async function listConversationCommands(): Promise<
  ConversationCommand[]
> {
  return await apiRequest<ConversationCommand[]>('/conversations/cmds');
}

export interface Message {
  id: number;
  conversation_id: number;
  run_id: number | null;
  role: string;
  content: string;
  metadata?: {
    events?: AESPEvent[];
  } | null;
  created_at: string;
}

export interface MessagePage {
  items: Message[];
  total: number;
  page: number;
  page_size: number;
}

export interface ListMessagesParams {
  page?: number;
  page_size?: number;
}

export const messageQueryKeys = {
  all: ['messages'] as const,
  list: (conversationId: number, params: ListMessagesParams = {}) =>
    [...messageQueryKeys.all, 'list', conversationId, params] as const,
};

export async function listMessages(
  conversationId: number,
  params: ListMessagesParams = {},
): Promise<MessagePage> {
  const searchParams = new URLSearchParams();
  searchParams.set('page', String(params.page ?? 1));
  searchParams.set('page_size', String(params.page_size ?? 50));

  return await apiRequest<MessagePage>(
    `/conversations/${conversationId}/messages?${searchParams.toString()}`,
  );
}

export interface AESPEvent {
  id: string;
  type: string;
  timestamp: string;
  conversation_id: string;
  run_id: string;
  sequence: number;
  data: Record<string, unknown>;
}

export interface StreamRunCallbacks {
  onEvent: (event: AESPEvent) => void;
  onError?: (error: Error) => void;
  onComplete?: () => void;
}

export async function streamConversationMessage(
  conversationId: number,
  content: string,
  callbacks: StreamRunCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const baseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:3081/api/v1';
  const tenantId = process.env.NEXT_PUBLIC_API_TENANT_ID ?? '1';
  const userId = process.env.NEXT_PUBLIC_API_USER_ID ?? '1';

  let response: Response;

  try {
    response = await fetch(
      `${baseUrl}/conversations/${conversationId}/messages`,
      {
        body: JSON.stringify({ content }),
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId,
          'X-User-Id': userId,
        },
        method: 'POST',
        signal,
      },
    );
  } catch (err) {
    callbacks.onError?.(err instanceof Error ? err : new Error(String(err)));
    return;
  }

  if (!response.ok || response.body === null) {
    const errorBody = await response.text().catch(() => '');
    callbacks.onError?.(
      new Error(
        `Stream request failed (${response.status}): ${errorBody.slice(0, 200)}`,
      ),
    );
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });

      let boundary = buffer.indexOf('\n\n');

      while (boundary !== -1) {
        const rawEvent = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        boundary = buffer.indexOf('\n\n');

        const event = parseSSE(rawEvent);

        if (event) {
          callbacks.onEvent(event);
        }
      }
    }

    // flush any remaining partial event
    if (buffer.trim()) {
      const event = parseSSE(buffer);

      if (event) {
        callbacks.onEvent(event);
      }
    }

    callbacks.onComplete?.();
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      callbacks.onComplete?.();
      return;
    }

    callbacks.onError?.(err instanceof Error ? err : new Error(String(err)));
  }
}

function parseSSE(raw: string): AESPEvent | null {
  const lines = raw.split('\n');
  let dataLine = '';

  for (const line of lines) {
    if (line.startsWith('data:')) {
      dataLine += line.slice(5).trim();
    }
  }

  if (!dataLine) {
    return null;
  }

  try {
    return JSON.parse(dataLine) as AESPEvent;
  } catch {
    return null;
  }
}

export async function listConversations(
  params: ListConversationsParams = {},
): Promise<ConversationPage> {
  const searchParams = new URLSearchParams();
  searchParams.set('page', String(params.page ?? 1));
  searchParams.set('page_size', String(params.page_size ?? 100));

  return await apiRequest<ConversationPage>(
    `/conversations?${searchParams.toString()}`,
  );
}

export async function createConversation(
  request: ConversationCreateRequest = {},
): Promise<Conversation> {
  return await apiRequest<Conversation>('/conversations', {
    body: request,
    method: 'POST',
  });
}

export async function updateConversation(
  conversationId: number,
  request: ConversationUpdateRequest,
): Promise<Conversation> {
  return await apiRequest<Conversation>(`/conversations/${conversationId}`, {
    body: request,
    method: 'PATCH',
  });
}
