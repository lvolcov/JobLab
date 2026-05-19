// joblab — tiny typed fetch client
// All requests use `credentials: "include"` so the session cookie travels.

const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, public detail: string) {
    super(detail || `HTTP ${status}`);
  }
}

type Method = "GET" | "POST" | "PATCH" | "PUT" | "DELETE";

const CSRF_COOKIE = "joblab_csrf";
const CSRF_HEADER = "X-CSRF-Token";
const UNSAFE_METHODS = new Set<Method>(["POST", "PATCH", "PUT", "DELETE"]);

function readCsrfCookie(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.split("; ").find((c) => c.startsWith(`${CSRF_COOKIE}=`));
  return match ? decodeURIComponent(match.slice(CSRF_COOKIE.length + 1)) : null;
}

async function request<T>(
  method: Method,
  path: string,
  body?: unknown,
  init?: RequestInit,
): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  let payload: BodyInit | undefined;

  if (body instanceof FormData) {
    payload = body;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  if (UNSAFE_METHODS.has(method)) {
    const csrf = readCsrfCookie();
    if (csrf) headers[CSRF_HEADER] = csrf;
  }

  const res = await fetch(`${BASE}${path}`, {
    method,
    credentials: "include",
    headers: { ...headers, ...(init?.headers as Record<string, string>) },
    body: payload,
    ...init,
  });

  if (res.status === 204) return undefined as T;

  const text = await res.text();
  let json: unknown = null;
  if (text) {
    try {
      json = JSON.parse(text);
    } catch {
      json = text;
    }
  }

  if (!res.ok) {
    const detail =
      (json && typeof json === "object" && "detail" in json
        ? String((json as { detail: unknown }).detail)
        : "") || `HTTP ${res.status}`;
    throw new ApiError(res.status, detail);
  }
  return json as T;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  patch: <T>(path: string, body?: unknown) => request<T>("PATCH", path, body),
  delete: <T = void>(path: string) => request<T>("DELETE", path),
  upload: <T>(path: string, form: FormData) => request<T>("POST", path, form),
};

// -------- shared types --------

export type UUID = string;

export interface Me {
  id: UUID;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  is_premium: boolean;
  default_provider: LLMProvider | null;
}

export interface AppUser extends Me {
  is_verified: boolean;
}

export type LLMProvider = "openai" | "anthropic" | "gemini";

export interface LLMKey {
  id: UUID;
  provider: LLMProvider;
  label: string;
  is_global: boolean;
  is_premium_only: boolean;
  owner_user_id: UUID | null;
  masked_key: string;
}

export interface Application {
  id: UUID;
  role_title: string;
  company: string;
  jd_text: string;
  status:
    | "applied"
    | "screening"
    | "interview"
    | "offer"
    | "rejected"
    | "withdrawn";
  applied_at: string | null;
  feedback: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export type ArtifactType = "cv" | "cover_letter" | "blind_cv" | "behaviour";

export interface Artifact {
  id: UUID;
  application_id: UUID;
  type: ArtifactType;
  provider: LLMProvider;
  word_limit: number;
  attempts: number;
  final_word_count: number;
  warning_flag: boolean;
  content: string;
  extra_instructions: string;
  behaviour_name: string | null;
  created_at: string;
}

export interface DocumentRow {
  id: UUID;
  filename: string;
  mime: string;
  size_bytes: number;
  parsed_text: string;
  created_at: string;
}

// Generic wiki row — concrete shape depends on the entity but for tables we
// only need a few common fields.
export interface WikiBaseRow {
  id: UUID;
  created_at: string;
  updated_at: string;
  possible_duplicate_of_id?: UUID | null;
  [key: string]: unknown;
}

export interface ImportSummary {
  inserted: number;
  skipped_exact: number;
  flagged_duplicate: number;
}

export interface ImportResult {
  cvs: ImportSummary;
  experiences: ImportSummary;
  projects: ImportSummary;
  skills: ImportSummary;
  qualifications: ImportSummary;
  education: ImportSummary;
  provider: LLMProvider;
  attempts: number;
}
