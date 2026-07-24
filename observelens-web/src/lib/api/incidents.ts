import { apiRequest } from '@/lib/api/client';

export interface IncidentIntegration {
  created_at: string;
  id: number;
  name: string;
  status: string;
  token: string;
  token_hint: string;
  type?: string;
  updated_at: string;
  webhook_url: string;
}

export interface IncidentOption {
  label: string;
  value: string;
}

export interface CreateIncidentIntegrationRequest {
  name: string;
  type: string;
}

export interface UpdateIncidentIntegrationRequest {
  name?: string;
  status?: 'ENABLED' | 'DISABLED';
  type?: string;
}

export interface ListIncidentIntegrationsParams {
  name?: string;
  status?: string;
  type?: string;
}

export const incidentIntegrationQueryKeys = {
  all: ['incident-integrations'] as const,
  statuses: () => [...incidentIntegrationQueryKeys.all, 'statuses'] as const,
  types: () => [...incidentIntegrationQueryKeys.all, 'types'] as const,
  list: (params: ListIncidentIntegrationsParams = {}) =>
    [...incidentIntegrationQueryKeys.all, 'list', params] as const,
};

export async function listIncidentIntegrationTypes(): Promise<
  IncidentOption[]
> {
  return await apiRequest<IncidentOption[]>('/incidents/integrations/types');
}

export async function listIncidentIntegrationStatuses(): Promise<
  IncidentOption[]
> {
  return await apiRequest<IncidentOption[]>('/incidents/integrations/statuses');
}

export async function listIncidentIntegrations(
  params: ListIncidentIntegrationsParams = {},
): Promise<IncidentIntegration[]> {
  const searchParams = new URLSearchParams();
  const type = params.type?.trim();
  const status = params.status?.trim();
  const name = params.name?.trim();

  if (type) {
    searchParams.set('type', type);
  }
  if (status) {
    searchParams.set('status', status);
  }
  if (name) {
    searchParams.set('name', name);
  }

  const queryString = searchParams.toString();

  return await apiRequest<IncidentIntegration[]>(
    `/incidents/integrations${queryString ? `?${queryString}` : ''}`,
  );
}

export async function createIncidentIntegration(
  request: CreateIncidentIntegrationRequest,
): Promise<IncidentIntegration> {
  return await apiRequest<IncidentIntegration>('/incidents/integrations', {
    body: request,
    method: 'POST',
  });
}

export async function updateIncidentIntegration({
  integrationId,
  request,
}: {
  integrationId: number;
  request: UpdateIncidentIntegrationRequest;
}): Promise<IncidentIntegration> {
  return await apiRequest<IncidentIntegration>(
    `/incidents/integrations/${integrationId}`,
    {
      body: request,
      method: 'PATCH',
    },
  );
}

export async function deleteIncidentIntegration(
  integrationId: number,
): Promise<void> {
  await apiRequest<void>(`/incidents/integrations/${integrationId}`, {
    method: 'DELETE',
  });
}
