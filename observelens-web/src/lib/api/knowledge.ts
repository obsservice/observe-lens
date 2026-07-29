import { apiFormRequest, apiRequest } from '@/lib/api/client';

export type KnowledgeBaseStatus = 'ACTIVE' | 'DISABLED';
export type DocumentType = 'GUIDE' | 'SOP' | 'CASE' | 'REFERENCE' | 'OTHER';
export type DocumentSourceType = 'UPLOAD' | 'URL' | 'API';
export type DocumentStatus =
  | 'UPLOADED'
  | 'PENDING'
  | 'PROCESSING'
  | 'READY'
  | 'REINDEXING'
  | 'FAILED'
  | 'ARCHIVED';

export interface KnowledgeBase {
  created_at: string;
  created_by: number;
  description: string | null;
  embedding_model: string;
  id: string;
  name: string;
  status: KnowledgeBaseStatus;
  tenant_id: number;
  updated_at: string;
}

export interface KnowledgeBasePage {
  items: KnowledgeBase[];
  page: number;
  page_size: number;
  total: number;
}

export interface KnowledgeDocument {
  archived_at: string | null;
  created_at: string;
  created_by: number;
  current_version_id: string | null;
  document_type: DocumentType;
  id: string;
  knowledge_base_id: string;
  metadata?: Record<string, unknown>;
  name: string;
  source_type: DocumentSourceType;
  status: DocumentStatus;
  tags: string[];
  tenant_id: number;
  updated_at: string;
}

export interface KnowledgeDocumentPage {
  items: KnowledgeDocument[];
  page: number;
  page_size: number;
  total: number;
}

export interface CreateKnowledgeBaseRequest {
  description?: string;
  embedding_model?: string;
  name: string;
}

export interface UpdateKnowledgeBaseRequest {
  description?: string | null;
  embedding_model?: string | null;
  name?: string;
  status?: KnowledgeBaseStatus;
}

export interface ListKnowledgeBasesParams {
  keyword?: string;
  page?: number;
  page_size?: number;
  status?: KnowledgeBaseStatus;
}

export interface ListDocumentsParams {
  document_type?: DocumentType;
  keyword?: string;
  page?: number;
  page_size?: number;
  status?: DocumentStatus;
  tag?: string;
}

export interface UploadDocumentRequest {
  document_type: DocumentType;
  file: File;
  metadata?: Record<string, unknown>;
  name?: string;
  tags?: string[];
}

export interface RetrievalFilters {
  document_types?: DocumentType[];
  document_ids?: string[];
  tags?: string[];
}

export interface RetrievalSearchRequest {
  filters?: RetrievalFilters;
  include_trace?: boolean;
  knowledge_base_ids?: string[];
  query: string;
  rerank?: boolean;
  top_k?: number;
}

export interface RetrievalCitation {
  document_id: string;
  document_name: string;
  document_version: number;
  page_number: number | null;
  section: string | null;
  snippet: string | null;
  source_url: string;
}

export interface RetrievalResultMetadata {
  chunk_index: number;
  document_type: DocumentType | null;
  knowledge_base_id: string;
  section_path: string[];
  tags: string[];
}

export interface RetrievalResult {
  chunk_id: string;
  citation: RetrievalCitation;
  content: string;
  metadata: RetrievalResultMetadata;
  score: number;
}

export interface RetrievalTrace {
  keyword_candidates: number;
  latency_ms: number;
  reranked_candidates: number;
  retrieval_id: string;
  rewritten_query: string | null;
  vector_candidates: number;
}

export interface RetrievalSearchResponse {
  query: string;
  results: RetrievalResult[];
  trace: RetrievalTrace | null;
}

export const knowledgeQueryKeys = {
  all: ['knowledge'] as const,
  bases: (params: ListKnowledgeBasesParams = {}) =>
    [...knowledgeQueryKeys.all, 'knowledge-bases', params] as const,
  documents: (
    knowledgeBaseId: string | null,
    params: ListDocumentsParams = {},
  ) =>
    [...knowledgeQueryKeys.all, 'documents', knowledgeBaseId, params] as const,
};

export async function listKnowledgeBases(
  params: ListKnowledgeBasesParams = {},
): Promise<KnowledgeBasePage> {
  const searchParams = new URLSearchParams();
  const keyword = params.keyword?.trim();

  searchParams.set('page', String(params.page ?? 1));
  searchParams.set('page_size', String(params.page_size ?? 20));
  if (keyword) searchParams.set('keyword', keyword);
  if (params.status) searchParams.set('status', params.status);

  return await apiRequest<KnowledgeBasePage>(
    `/knowledge/knowledge-bases?${searchParams.toString()}`,
  );
}

export async function createKnowledgeBase(
  request: CreateKnowledgeBaseRequest,
): Promise<KnowledgeBase> {
  return await apiRequest<KnowledgeBase>('/knowledge/knowledge-bases', {
    body: request,
    method: 'POST',
  });
}

export async function updateKnowledgeBase(
  knowledgeBaseId: string,
  request: UpdateKnowledgeBaseRequest,
): Promise<KnowledgeBase> {
  return await apiRequest<KnowledgeBase>(
    `/knowledge/knowledge-bases/${knowledgeBaseId}`,
    {
      body: request,
      method: 'PATCH',
    },
  );
}

export async function deleteKnowledgeBase(
  knowledgeBaseId: string,
): Promise<void> {
  await apiRequest<void>(`/knowledge/knowledge-bases/${knowledgeBaseId}`, {
    method: 'DELETE',
  });
}

export async function listKnowledgeDocuments(
  knowledgeBaseId: string,
  params: ListDocumentsParams = {},
): Promise<KnowledgeDocumentPage> {
  const searchParams = new URLSearchParams();
  const keyword = params.keyword?.trim();
  const tag = params.tag?.trim();

  searchParams.set('page', String(params.page ?? 1));
  searchParams.set('page_size', String(params.page_size ?? 20));
  if (keyword) searchParams.set('keyword', keyword);
  if (params.document_type)
    searchParams.set('document_type', params.document_type);
  if (params.status) searchParams.set('status', params.status);
  if (tag) searchParams.set('tag', tag);

  return await apiRequest<KnowledgeDocumentPage>(
    `/knowledge/knowledge-bases/${knowledgeBaseId}/documents?${searchParams.toString()}`,
  );
}

export async function uploadKnowledgeDocument(
  knowledgeBaseId: string,
  request: UploadDocumentRequest,
): Promise<KnowledgeDocument> {
  const formData = new FormData();
  formData.set('file', request.file);
  formData.set('name', request.name?.trim() || request.file.name);
  formData.set('document_type', request.document_type);
  formData.set('tags', JSON.stringify(request.tags ?? []));
  formData.set('metadata', JSON.stringify(request.metadata ?? {}));

  const response = await apiFormRequest<{ document: KnowledgeDocument }>(
    `/knowledge/knowledge-bases/${knowledgeBaseId}/documents`,
    formData,
    { method: 'POST' },
  );

  return response.document;
}

export async function searchKnowledge(
  request: RetrievalSearchRequest,
): Promise<RetrievalSearchResponse> {
  return await apiRequest<RetrievalSearchResponse>(
    '/knowledge/retrieval/search',
    {
      body: request,
      method: 'POST',
    },
  );
}
