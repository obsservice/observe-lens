import { apiRequest } from '@/lib/api/client';

export interface ModelConfig {
  id: number;
  name: string;
  provider: string;
  model_name: string;
  endpoint: string | null;
  credential: string | null;
  status: string;
  is_default: boolean;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface ModelPage {
  items: ModelConfig[];
  total: number;
  page: number;
  page_size: number;
}

export interface ModelWriteRequest {
  name: string;
  provider: string;
  model_name: string;
  endpoint?: string | null;
  credential_ref?: string | null;
  status?: string | null;
}

export interface Option {
  label: string;
  value: string;
}

export interface ListModelsParams {
  page?: number;
  page_size?: number;
}

export const settingsQueryKeys = {
  all: ['settings'] as const,
  models: (params: ListModelsParams = {}) =>
    [...settingsQueryKeys.all, 'models', params] as const,
};

export async function listModels(
  params: ListModelsParams = {},
): Promise<ModelPage> {
  const searchParams = new URLSearchParams();
  searchParams.set('page', String(params.page ?? 1));
  searchParams.set('page_size', String(params.page_size ?? 20));
  return await apiRequest<ModelPage>(`/models?${searchParams.toString()}`);
}

export async function createModel(
  request: ModelWriteRequest,
): Promise<ModelConfig> {
  return await apiRequest<ModelConfig>('/models', {
    body: request,
    method: 'POST',
  });
}

export async function updateModel(
  id: number,
  request: ModelWriteRequest,
): Promise<ModelConfig> {
  return await apiRequest<ModelConfig>(`/models/${id}`, {
    body: request,
    method: 'PUT',
  });
}

export async function deleteModel(id: number): Promise<void> {
  await apiRequest<void>(`/models/${id}`, {
    method: 'DELETE',
  });
}

export async function listModelProviders(): Promise<Option[]> {
  return await apiRequest<Option[]>('/models/providers');
}

export async function listModelStatuses(): Promise<Option[]> {
  return await apiRequest<Option[]>('/models/statuses');
}

export interface NotificationConfig {
  id: number;
  name: string;
  type: string;
  status: string;
  target: string;
  credential: string | null;
  created_at: string;
  updated_at: string;
}

export interface NotificationPage {
  items: NotificationConfig[];
  total: number;
  page: number;
  page_size: number;
}

export interface NotificationWriteRequest {
  name: string;
  channel_type: string;
  target: string;
  credential_ref?: string | null;
  status?: string | null;
}

export interface ListNotificationsParams {
  page?: number;
  page_size?: number;
}

export const notificationQueryKeys = {
  all: ['notifications'] as const,
  list: (params: ListNotificationsParams = {}) =>
    [...notificationQueryKeys.all, 'list', params] as const,
};

export async function listNotifications(
  params: ListNotificationsParams = {},
): Promise<NotificationPage> {
  const searchParams = new URLSearchParams();
  searchParams.set('page', String(params.page ?? 1));
  searchParams.set('page_size', String(params.page_size ?? 20));
  return await apiRequest<NotificationPage>(
    `/notifications?${searchParams.toString()}`,
  );
}

export async function createNotification(
  request: NotificationWriteRequest,
): Promise<NotificationConfig> {
  return await apiRequest<NotificationConfig>('/notifications', {
    body: request,
    method: 'POST',
  });
}

export async function updateNotification(
  id: number,
  request: NotificationWriteRequest,
): Promise<NotificationConfig> {
  return await apiRequest<NotificationConfig>(`/notifications/${id}`, {
    body: request,
    method: 'PUT',
  });
}

export async function deleteNotification(id: number): Promise<void> {
  await apiRequest<void>(`/notifications/${id}`, {
    method: 'DELETE',
  });
}

export async function listNotificationTypes(): Promise<Option[]> {
  return await apiRequest<Option[]>('/notifications/types');
}
