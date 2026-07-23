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
  process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export async function apiRequest<TResponse>(
  path: string,
  { body, headers, ...options }: RequestOptions = {},
): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    body: body === undefined ? undefined : JSON.stringify(body),
    headers: {
      Accept: 'application/json',
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

  return (await response.json()) as TResponse;
}
