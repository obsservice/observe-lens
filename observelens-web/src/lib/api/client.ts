export class ApiError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly requestId: string | null;

  public constructor({
    status,
    code,
    message,
    requestId,
  }: {
    status: number;
    code: string;
    message: string;
    requestId: string | null;
  }) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

interface ApiErrorResponse {
  code?: string;
  message?: string;
  request_id?: string;
}

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
  signal?: AbortSignal;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:3081/api/v1';

const API_TENANT_ID = process.env.NEXT_PUBLIC_API_TENANT_ID ?? '1';
const API_USER_ID = process.env.NEXT_PUBLIC_API_USER_ID ?? '1';

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

export async function apiRequest<TResponse>(
  path: string,
  { body, headers, ...options }: RequestOptions = {},
): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    body: body === undefined ? undefined : JSON.stringify(body),
    headers: {
      Accept: 'application/json',
      'X-Tenant-Id': API_TENANT_ID,
      'X-User-Id': API_USER_ID,
      ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
      ...headers,
    },
  });

  if (!response.ok) {
    const errorResponse = (await response
      .json()
      .catch(() => ({}))) as ApiErrorResponse;
    throw new ApiError({
      status: response.status,
      code: errorResponse.code ?? 'REQUEST_FAILED',
      message: errorResponse.message ?? 'The request could not be completed.',
      requestId:
        errorResponse.request_id ?? response.headers.get('x-request-id'),
    });
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  return (await response.json()) as TResponse;
}
