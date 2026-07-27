import { apiRequest } from '@/lib/api/client';

export interface Incident {
  conversation_id: number | null;
  created_at: string;
  description: string | null;
  id: number;
  incident_id: string;
  name: string;
  severity: string;
  source: string | null;
  external_metadata: Record<string, string>;
  started_at: string | null;
  status: string;
  updated_at: string;
}

export interface IncidentPage {
  items: Incident[];
  page: number;
  page_size: number;
  total: number;
}

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

export interface ListIncidentsParams {
  keyword?: string;
  name?: string;
  page?: number;
  page_size?: number;
  severity?: string;
  source?: string;
  status?: string;
}

export interface OpenIncidentConversationResponse {
  conversation_id: number;
}

export const incidentQueryKeys = {
  all: ['incidents'] as const,
  severities: () => [...incidentQueryKeys.all, 'severities'] as const,
  statuses: () => [...incidentQueryKeys.all, 'statuses'] as const,
  list: (params: ListIncidentsParams = {}) =>
    [...incidentQueryKeys.all, 'list', params] as const,
};

export const incidentIntegrationQueryKeys = {
  all: ['incident-integrations'] as const,
  statuses: () => [...incidentIntegrationQueryKeys.all, 'statuses'] as const,
  types: () => [...incidentIntegrationQueryKeys.all, 'types'] as const,
  list: (params: ListIncidentIntegrationsParams = {}) =>
    [...incidentIntegrationQueryKeys.all, 'list', params] as const,
};

export async function listIncidentSeverities(): Promise<IncidentOption[]> {
  return await apiRequest<IncidentOption[]>('/incidents/severities');
}

export async function listIncidentStatuses(): Promise<IncidentOption[]> {
  return await apiRequest<IncidentOption[]>('/incidents/statuses');
}

export async function listIncidents(
  params: ListIncidentsParams = {},
): Promise<IncidentPage> {
  const searchParams = new URLSearchParams();
  const severity = params.severity?.trim();
  const status = params.status?.trim();
  const source = params.source?.trim();
  const keyword = params.keyword?.trim();
  const name = params.name?.trim();

  searchParams.set('page', String(params.page ?? 1));
  searchParams.set('page_size', String(params.page_size ?? 20));
  if (keyword) {
    searchParams.set('keyword', keyword);
  }
  if (name) {
    searchParams.set('name', name);
  }
  if (severity) {
    searchParams.set('severity', severity);
  }
  if (status) {
    searchParams.set('status', status);
  }
  if (source) {
    searchParams.set('source', source);
  }

  return await apiRequest<IncidentPage>(
    `/incidents?${searchParams.toString()}`,
  );
}

export async function openIncidentConversation(
  incidentId: number,
): Promise<OpenIncidentConversationResponse> {
  return await apiRequest<OpenIncidentConversationResponse>(
    `/incidents/${incidentId}/open-conversation`,
    { method: 'POST' },
  );
}

export interface UpdateIncidentRequest {
  severity?: string;
  status?: string;
  title?: string;
}

export async function updateIncident(
  incidentId: number,
  request: UpdateIncidentRequest,
): Promise<Incident> {
  return await apiRequest<Incident>(`/incidents/${incidentId}`, {
    method: 'PATCH',
    body: request,
  });
}

export interface TransitionIncidentRequest {
  status: string;
  assignee?: string;
}

export async function transitionIncident(
  incidentId: number,
  request: TransitionIncidentRequest,
): Promise<Incident> {
  return await apiRequest<Incident>(`/incidents/${incidentId}/transition`, {
    method: 'POST',
    body: request,
  });
}

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
