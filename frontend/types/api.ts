export type WorkspaceRole = "owner" | "admin" | "developer" | "analyst" | "viewer";

export type MembershipSummary = {
  workspace_id: string;
  workspace_name: string;
  workspace_slug: string;
  role: WorkspaceRole;
};

export type MeResponse = {
  user: {
    id: string;
    email: string;
    full_name: string;
    is_active: boolean;
  };
  memberships: MembershipSummary[];
};

export type Workspace = {
  id: string;
  name: string;
  slug: string;
  owner_user_id: string;
  created_at: string;
  current_user_role: WorkspaceRole;
};

export type Project = {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  use_case: string;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type DocumentRecord = {
  id: string;
  workspace_id: string;
  project_id: string;
  title: string;
  filename: string;
  content_type: string;
  status: "uploaded" | "processing" | "processed" | "failed" | string;
  metadata_json: Record<string, unknown>;
  allowed_roles_json: WorkspaceRole[];
  allowed_users_json: string[];
  tags_json: string[];
  page_count: number | null;
  created_at: string;
  updated_at: string;
};

export type DocumentDetail = DocumentRecord & {
  extracted_text: string | null;
  preview: {
    text: string;
    truncated: boolean;
    character_count: number;
    structure: Record<string, unknown>;
    warnings: string[];
  };
};

export type SplitterType = "fixed" | "recursive" | "heading" | "semantic" | "table_aware";

export type StrategyRecord = {
  id: string;
  project_id: string;
  name: string;
  splitter_type: SplitterType;
  chunk_size: number;
  overlap: number;
  preserve_headings: boolean;
  preserve_tables: boolean;
  semantic_threshold: number | null;
  created_at: string;
};

export type StrategyCreatePayload = {
  name: string;
  splitter_type: SplitterType;
  chunk_size: number;
  overlap: number;
  preserve_headings: boolean;
  preserve_tables: boolean;
  semantic_threshold: number | null;
  config_json: Record<string, unknown>;
};

export type StrategyIndexResponse = {
  strategy_id: string;
  documents_indexed: number;
  chunks_created: number;
  chunks_deleted: number;
  warnings: string[];
};

export type ChunkRecord = {
  id: string;
  document_id: string;
  strategy_id: string;
  chunk_index: number;
  text: string;
  token_count: number;
  page_number: number | null;
  section_heading: string | null;
  start_offset: number;
  end_offset: number;
  allowed_roles_json: WorkspaceRole[];
  allowed_users_json: string[];
  tags_json: string[];
  metadata_json: {
    warnings?: string[];
    source_document_title?: string;
    splitter?: string;
    preserved_table?: boolean;
    [key: string]: unknown;
  };
  created_at: string;
};

export type ScoreBreakdown = {
  dense_score: number;
  sparse_score: number;
  hybrid_score: number;
  rerank_score: number | null;
};

export type RetrievedChunk = {
  id: string;
  document_id: string;
  strategy_id: string;
  chunk_index: number;
  text: string;
  token_count: number;
  page_number: number | null;
  section_heading: string | null;
  allowed_roles: WorkspaceRole[];
  tags: string[];
  metadata: Record<string, unknown>;
  scores: ScoreBreakdown;
};

export type QueryMetrics = {
  context_precision: number;
  context_recall: number;
  average_similarity: number;
  irrelevant_chunk_rate: number;
  citation_coverage: number;
  rbac_leakage_count: number;
  latency_ms: number;
  estimated_cost: number;
  overall_score: number;
  warnings: string[];
};

export type FunnelStage = {
  name: string;
  count: number;
  latency_ms: number;
};

export type QueryAnalyzeResponse = {
  query_run_id: string;
  project_id: string;
  strategy_id: string;
  query: string;
  role_context: Record<string, unknown>;
  retrieved_chunks: RetrievedChunk[];
  metrics: QueryMetrics;
  funnel: FunnelStage[];
  latency_ms: number;
  created_at: string;
};

export type QueryOptimizeResponse = {
  original_query: string;
  optimized_queries: Array<{
    query: string;
    method: string;
    reason: string;
  }>;
};

export type ScatterPoint = {
  id: string;
  type: "query" | "chunk" | "document" | string;
  label: string;
  x: number;
  y: number;
  score: number;
  cluster: string;
  metadata: Record<string, unknown>;
};

export type ScatterResponse = {
  points: ScatterPoint[];
};

export type GraphNode = {
  id: string;
  type: "query" | "chunk" | "document" | string;
  label: string;
  metadata: Record<string, unknown>;
};

export type GraphEdge = {
  source: string;
  target: string;
  weight: number;
  label: string;
};

export type GraphResponse = {
  nodes: GraphNode[];
  edges: GraphEdge[];
};

export type FunnelResponse = {
  stages: FunnelStage[];
};

export type ExperimentRecord = {
  id: string;
  workspace_id: string;
  project_id: string;
  name: string;
  description: string | null;
  status: string;
  strategy_ids_json: string[];
  query_set_json: Array<Record<string, unknown>>;
  created_at: string;
  completed_at: string | null;
};

export type StrategyLeaderboardRow = {
  strategy_id: string;
  strategy_name: string;
  query_runs: number;
  context_precision: number;
  context_recall: number;
  average_similarity: number;
  irrelevant_chunk_rate: number;
  citation_coverage: number;
  latency_ms: number;
  estimated_cost: number;
  rbac_leakage_count: number;
  overall_score: number;
  recommendation: string;
};

export type ExperimentRunResponse = {
  experiment: ExperimentRecord;
  leaderboard: StrategyLeaderboardRow[];
  best_strategy_id: string | null;
  query_run_ids: string[];
};

export type ProjectRecommendation = {
  project_id: string;
  recommended_strategy_id: string | null;
  recommended_strategy_name: string | null;
  leaderboard: StrategyLeaderboardRow[];
  recommended_config: Record<string, unknown> | null;
};

export type RBACChunkAccess = {
  chunk_id: string;
  document_id: string;
  chunk_index: number;
  section_heading: string | null;
  token_count: number;
  allowed_roles: WorkspaceRole[];
  tags: string[];
  access: "allowed" | "blocked" | string;
  text_preview: string | null;
  warnings: string[];
};

export type RBACSimulationResponse = {
  project_id: string;
  strategy_id: string;
  role_simulation: WorkspaceRole;
  allowed_chunks: RBACChunkAccess[];
  blocked_chunks: RBACChunkAccess[];
  retrieved_chunk_ids: string[];
  leakage_count: number;
  mixed_permission_warnings: string[];
  metrics: QueryMetrics;
};

export type RBACMatrixResponse = {
  project_id: string;
  rows: Array<{
    entity_id: string;
    entity_type: string;
    label: string;
    allowed_roles: WorkspaceRole[];
    tags: string[];
    role_access: Record<WorkspaceRole, boolean>;
    warnings: string[];
  }>;
};

export type ExportConfigResponse = {
  format: string;
  content: string;
  content_type: string;
  recommended_config: Record<string, unknown>;
};

export type DataLayerProjectFacts = {
  document_count: number;
  processed_document_count: number;
  chunk_count: number;
  strategy_count: number;
  query_run_count: number;
  content_types: Record<string, number>;
  average_chunk_tokens: number;
  chunks_with_embeddings: number;
  chunks_with_section_headings: number;
  chunks_with_tags: number;
  distinct_access_profiles: number;
  mixed_access_chunk_count: number;
};

export type DataLayerStoreRecommendation = {
  store: "relational" | "vector" | "graph" | string;
  role: string;
  fit_score: number;
  primary_entities: string[];
  indexing_strategy: string[];
  rationale: string[];
  risks: string[];
};

export type DataLayerRoutingRule = {
  data_domain: string;
  primary_store: string;
  secondary_stores: string[];
  reason: string;
  sync_pattern: string;
};

export type DataLayerRecommendationResponse = {
  project_id: string;
  facts: DataLayerProjectFacts;
  recommended_architecture: string;
  stores: DataLayerStoreRecommendation[];
  routing_rules: DataLayerRoutingRule[];
  efficiency_recommendations: string[];
  governance_rules: string[];
  warnings: string[];
};

export type AdminUserRecord = {
  user_id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  workspace_id: string;
  role: WorkspaceRole;
  joined_at: string;
};

export type AuditLogRecord = {
  id: string;
  workspace_id: string | null;
  user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type AdminSettingsResponse = {
  embedding_providers: string[];
  storage_provider: string;
  api_keys_placeholder: string;
  rate_limiting: string;
};
