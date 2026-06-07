import type {
  ChunkRecord,
  AdminSettingsResponse,
  AdminUserRecord,
  AuditLogRecord,
  DocumentDetail,
  DocumentRecord,
  DataLayerRecommendationResponse,
  FunnelResponse,
  GraphResponse,
  MeResponse,
  Project,
  ExperimentRecord,
  ExperimentRunResponse,
  ProjectRecommendation,
  QueryAnalyzeResponse,
  QueryOptimizeResponse,
  ExportConfigResponse,
  RBACMatrixResponse,
  RBACSimulationResponse,
  ScatterResponse,
  StrategyCreatePayload,
  StrategyIndexResponse,
  StrategyRecord,
  Workspace,
  WorkspaceRole
} from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("rvo_access_token") : null;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers
    }
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: "Request failed" }));
    if (response.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("rvo_access_token");
      localStorage.removeItem("rvo_refresh_token");
    }
    const message =
      response.status === 401
        ? "Your session expired. Sign in again to continue."
        : typeof detail.detail === "string"
          ? detail.detail
          : "Request failed";
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

async function multipartRequest<T>(path: string, body: FormData): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("rvo_access_token") : null;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(detail.detail ?? "Request failed");
  }
  return response.json() as Promise<T>;
}

export const api = {
  me: () => request<MeResponse>("/auth/me"),
  workspaces: () => request<Workspace[]>("/workspaces"),
  createWorkspace: (payload: { name: string; slug?: string | null }) =>
    request<Workspace>("/workspaces", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  projects: (workspaceId?: string) =>
    request<Project[]>(workspaceId ? `/projects?workspace_id=${workspaceId}` : "/projects"),
  createProject: (payload: {
    workspace_id: string;
    name: string;
    description: string | null;
    use_case: string;
  }) =>
    request<Project>("/projects", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  documents: (projectId: string) => request<DocumentRecord[]>(`/projects/${projectId}/documents`),
  document: (documentId: string) => request<DocumentDetail>(`/documents/${documentId}`),
  strategies: (projectId: string) => request<StrategyRecord[]>(`/projects/${projectId}/strategies`),
  strategy: (strategyId: string) => request<StrategyRecord>(`/strategies/${strategyId}`),
  createStrategy: (projectId: string, payload: StrategyCreatePayload) =>
    request<StrategyRecord>(`/projects/${projectId}/strategies`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  indexStrategy: (strategyId: string) =>
    request<StrategyIndexResponse>(`/strategies/${strategyId}/index`, { method: "POST" }),
  strategyChunks: (strategyId: string, limit = 100) =>
    request<ChunkRecord[]>(`/strategies/${strategyId}/chunks?limit=${limit}`),
  analyzeQuery: (projectId: string, payload: {
    query: string;
    strategy_id: string;
    top_k: number;
    dense_weight: number;
    sparse_weight: number;
    role_simulation: WorkspaceRole | null;
    rerank: boolean;
  }) =>
    request<QueryAnalyzeResponse>(`/projects/${projectId}/query/analyze`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  optimizeQuery: (projectId: string, query: string, useCase?: string) =>
    request<QueryOptimizeResponse>(`/projects/${projectId}/query/optimize`, {
      method: "POST",
      body: JSON.stringify({ query, use_case: useCase ?? null })
    }),
  queryRunScatter: (queryRunId: string) =>
    request<ScatterResponse>(`/query-runs/${queryRunId}/scatter`),
  queryRunGraph: (queryRunId: string) => request<GraphResponse>(`/query-runs/${queryRunId}/graph`),
  queryRunFunnel: (queryRunId: string) =>
    request<FunnelResponse>(`/query-runs/${queryRunId}/funnel`),
  experiments: (projectId: string) =>
    request<ExperimentRecord[]>(`/projects/${projectId}/experiments`),
  createExperiment: (projectId: string, payload: {
    name: string;
    description: string | null;
    strategy_ids: string[];
    query_set: Array<{ query: string; expected_chunk_ids: string[] }>;
    role_simulation: WorkspaceRole | null;
  }) =>
    request<ExperimentRecord>(`/projects/${projectId}/experiments`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  runExperiment: (experimentId: string) =>
    request<ExperimentRunResponse>(`/experiments/${experimentId}/run`, { method: "POST" }),
  projectRecommendation: (projectId: string) =>
    request<ProjectRecommendation>(`/projects/${projectId}/recommendation`),
  dataLayerRecommendation: (projectId: string) =>
    request<DataLayerRecommendationResponse>(`/projects/${projectId}/data-layer/recommendation`),
  simulateRbac: (projectId: string, payload: {
    strategy_id: string;
    query: string;
    role_simulation: WorkspaceRole;
    top_k: number;
  }) =>
    request<RBACSimulationResponse>(`/projects/${projectId}/rbac/simulate`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  rbacMatrix: (projectId: string) => request<RBACMatrixResponse>(`/projects/${projectId}/rbac/matrix`),
  exportConfig: (projectId: string, format: string) =>
    request<ExportConfigResponse>(`/projects/${projectId}/export-config`, {
      method: "POST",
      body: JSON.stringify({ format })
    }),
  adminUsers: (workspaceId: string) =>
    request<AdminUserRecord[]>(`/admin/users?workspace_id=${workspaceId}`),
  adminAuditLogs: (workspaceId: string) =>
    request<AuditLogRecord[]>(`/admin/audit-logs?workspace_id=${workspaceId}&limit=100`),
  adminSettings: (workspaceId: string) =>
    request<AdminSettingsResponse>(`/admin/settings?workspace_id=${workspaceId}`),
  processDocument: (documentId: string) =>
    request<{ id: string; status: string; extracted_characters: number; page_count: number | null; warnings: string[] }>(
      `/documents/${documentId}/process`,
      { method: "POST" }
    ),
  uploadDocument: (projectId: string, payload: {
    title: string;
    file: File;
    allowedRoles: WorkspaceRole[];
    tags: string[];
    metadata: Record<string, string>;
  }) => {
    const body = new FormData();
    body.set("title", payload.title);
    body.set("allowed_roles", JSON.stringify(payload.allowedRoles));
    body.set("allowed_user_ids", JSON.stringify([]));
    body.set("tags", JSON.stringify(payload.tags));
    body.set("metadata", JSON.stringify(payload.metadata));
    body.set("file", payload.file);
    return multipartRequest<DocumentRecord>(`/projects/${projectId}/documents/upload`, body);
  },
  login: (email: string, password: string) =>
    request<{ access_token: string; refresh_token: string; token_type: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    }),
  register: (payload: {
    email: string;
    password: string;
    full_name: string;
    workspace_name: string;
  }) =>
    request<{ access_token: string; refresh_token: string; token_type: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload)
    })
};
