import { apiRequest } from './client';

interface CatalogApiResponse<TData> {
  code: 0;
  data: TData;
  msg: string;
}

interface CatalogEntity {
  __domain__: string;
  __entity_type__: string;
  __entity_uuid__: string;
  __fields__: Record<string, unknown>;
  __last_observed_time__: number;
}

interface CatalogEntityPage {
  items: CatalogEntity[];
  limit: number;
  page: number;
  total: number;
}

interface CatalogEntityTypeModel {
  metadata: {
    displayName?: string;
    name: string;
  };
}

interface CatalogModelPage {
  items: CatalogEntityTypeModel[];
}

export interface Entity {
  id: string;
  labels: Record<string, string>;
  name: string;
  namespace: string;
  status: string;
  type: string;
  updated_at: string | null;
}

export interface EntityOption {
  label: string;
  value: string;
}

export interface EntityPage {
  items: Entity[];
  page: number;
  page_size: number;
  total: number;
}

export interface SearchEntitiesParams {
  page?: number;
  page_size?: number;
  query?: string;
  type?: string;
}

const CATALOG_WORKSPACE_ID =
  process.env.NEXT_PUBLIC_CATALOG_WORKSPACE_ID ?? 'ws000003';

const catalogWorkspacePath = `/catalog/workspaces/${encodeURIComponent(
  CATALOG_WORKSPACE_ID,
)}`;

export const entityQueryKeys = {
  all: ['entities'] as const,
  search: (params: SearchEntitiesParams = {}) =>
    [...entityQueryKeys.all, 'search', params] as const,
  types: () => [...entityQueryKeys.all, 'types'] as const,
};

function toLabelValue(value: unknown): string | null {
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }
  return null;
}

function toEntity(entity: CatalogEntity): Entity {
  const fields = entity.__fields__;
  const displayName = toLabelValue(fields.display_name);
  const identifier = toLabelValue(fields.id);
  const namespace = toLabelValue(fields.namespace);
  const status =
    toLabelValue(fields.status) ?? toLabelValue(fields.phase) ?? 'Unknown';
  const labels = Object.fromEntries(
    Object.entries(fields).flatMap(([key, value]) => {
      const labelValue = toLabelValue(value);
      return labelValue === null ||
        ['display_name', 'namespace', 'status'].includes(key)
        ? []
        : [[key, labelValue]];
    }),
  );

  return {
    id: entity.__entity_uuid__,
    labels,
    name: displayName ?? identifier ?? entity.__entity_uuid__,
    namespace: namespace ?? entity.__domain__ ?? '-',
    status,
    type: entity.__entity_type__,
    updated_at: new Date(entity.__last_observed_time__ * 1000).toISOString(),
  };
}

function toEntityPage(page: CatalogEntityPage): EntityPage {
  return {
    items: page.items.map(toEntity),
    page: page.page + 1,
    page_size: page.limit,
    total: page.total,
  };
}

export async function listEntityTypes(): Promise<EntityOption[]> {
  const response = await apiRequest<CatalogApiResponse<CatalogModelPage>>(
    `${catalogWorkspacePath}/models?kind=EntityType&page=0&limit=200`,
  );

  return response.data.items.map((model) => ({
    label: model.metadata.displayName ?? model.metadata.name,
    value: model.metadata.name,
  }));
}

export async function searchEntities(
  params: SearchEntitiesParams = {},
): Promise<EntityPage> {
  const query = params.query?.trim();
  const type = params.type?.trim();
  const page = Math.max((params.page ?? 1) - 1, 0);
  const limit = params.page_size ?? 20;

  if (query) {
    const response = await apiRequest<CatalogApiResponse<CatalogEntityPage>>(
      `${catalogWorkspacePath}/entities/search`,
      {
        body: {
          entity_types: type || undefined,
          keyword: query,
          limit,
          page,
        },
        method: 'POST',
      },
    );

    return toEntityPage(response.data);
  }

  const searchParams = new URLSearchParams({
    limit: String(limit),
    page: String(page),
  });
  if (type) searchParams.set('entityType', type);

  const response = await apiRequest<CatalogApiResponse<CatalogEntityPage>>(
    `${catalogWorkspacePath}/entities?${searchParams.toString()}`,
  );

  return toEntityPage(response.data);
}
