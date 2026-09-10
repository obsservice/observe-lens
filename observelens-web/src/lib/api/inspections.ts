import { apiRequest } from '@/lib/api/client';

export type InspectionStatus =
  'DISABLED' | 'ENABLED' | 'FAILED' | 'RUNNING' | 'SUCCESS';

export interface Inspection {
  created_at: string;
  description: string | null;
  id: number;
  last_run_at: string | null;
  name: string;
  schedule: string;
  scope: string;
  status: InspectionStatus;
  updated_at: string;
}

export interface InspectionPage {
  items: Inspection[];
  page: number;
  page_size: number;
  total: number;
}

export interface InspectionOption {
  label: string;
  value: string;
}

export interface InspectionWriteRequest {
  description?: string | null;
  enabled?: boolean;
  input_template?: string;
  name: string;
  schedule: string;
  scope: string;
}

export interface InspectionExecutionResponse {
  run_id: number;
  status: 'FAILED' | 'RUNNING' | 'SUCCESS';
}

export interface ListInspectionsParams {
  page?: number;
  page_size?: number;
}

export const inspectionQueryKeys = {
  all: ['inspections'] as const,
  list: (params: ListInspectionsParams = {}) =>
    [...inspectionQueryKeys.all, 'list', params] as const,
  schedules: () => [...inspectionQueryKeys.all, 'schedules'] as const,
  statuses: () => [...inspectionQueryKeys.all, 'statuses'] as const,
};

export async function listInspections(
  params: ListInspectionsParams = {},
): Promise<InspectionPage> {
  const searchParams = new URLSearchParams({
    page: String(params.page ?? 1),
    page_size: String(params.page_size ?? 20),
  });

  return await apiRequest<InspectionPage>(
    `/inspections?${searchParams.toString()}`,
  );
}

export async function createInspection(
  request: InspectionWriteRequest,
): Promise<Inspection> {
  return await apiRequest<Inspection>('/inspections', {
    body: request,
    method: 'POST',
  });
}

export async function updateInspection(
  id: number,
  request: Partial<InspectionWriteRequest>,
): Promise<Inspection> {
  return await apiRequest<Inspection>(`/inspections/${id}`, {
    body: request,
    method: 'PATCH',
  });
}

export async function deleteInspection(id: number): Promise<void> {
  await apiRequest<void>(`/inspections/${id}`, { method: 'DELETE' });
}

export async function executeInspection(
  id: number,
): Promise<InspectionExecutionResponse> {
  return await apiRequest<InspectionExecutionResponse>(
    `/inspections/${id}/execute`,
    { method: 'POST' },
  );
}

export async function enableInspection(id: number): Promise<Inspection> {
  return await apiRequest<Inspection>(`/inspections/${id}/enable`, {
    method: 'POST',
  });
}

export async function disableInspection(id: number): Promise<Inspection> {
  return await apiRequest<Inspection>(`/inspections/${id}/disable`, {
    method: 'POST',
  });
}

export async function listInspectionStatuses(): Promise<InspectionOption[]> {
  return await apiRequest<InspectionOption[]>('/inspections/statuses');
}

export async function listInspectionSchedules(): Promise<InspectionOption[]> {
  return await apiRequest<InspectionOption[]>('/inspections/schedules');
}
