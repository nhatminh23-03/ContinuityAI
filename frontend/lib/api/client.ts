/**
 * The single boundary between the UI and the API.
 *
 * Components never fetch directly. Switching NEXT_PUBLIC_USE_MOCKS flips the whole
 * app between the shared fixtures and a live FastAPI without touching a component,
 * which is the Phase 1 integration gate in docs/ARCHITECTURE.md section 100.
 */

import type { ApiErrorResponse, ErrorCode } from '@/types/api';

const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== 'false';
const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

/** Thrown for every non-2xx response. Switch on `code`, never on `message`. */
export class ApiError extends Error {
  readonly code: ErrorCode;
  readonly status: number;
  readonly details: Record<string, unknown>;

  constructor(code: ErrorCode, message: string, status: number, details = {}) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

/** Fixture file backing each endpoint in mock mode. */
export type FixtureName =
  | 'platforms'
  | 'payments-systems'
  | 'identity-systems'
  | 'payment-gateway'
  | 'payment-gateway-graph'
  | 'incident-recovery'
  | 'incident-recovery-evidence'
  | 'alex-simulation'
  | 'backup-candidates'
  | 'mitigation-plan'
  | 'mitigation-plan-approved'
  | 'challenge-attest-jordan';

async function readFixture<T>(name: FixtureName): Promise<T> {
  const response = await fetch(`/fixtures/${name}.json`);
  if (!response.ok) {
    throw new ApiError(
      'NOT_FOUND',
      `Fixture '${name}' is missing. Run: npm run sync:fixtures`,
      response.status,
    );
  }
  return response.json() as Promise<T>;
}

interface RequestOptions {
  method?: 'GET' | 'POST';
  body?: unknown;
  query?: Record<string, string | undefined>;
  /** Fixture used when mock mode is on. */
  fixture: FixtureName;
}

export async function request<T>(path: string, options: RequestOptions): Promise<T> {
  if (USE_MOCKS) return readFixture<T>(options.fixture);

  const url = new URL(`${BASE_URL}/api/v1${path}`);
  for (const [key, value] of Object.entries(options.query ?? {})) {
    if (value !== undefined) url.searchParams.set(key, value);
  }

  const response = await fetch(url, {
    method: options.method ?? 'GET',
    headers: options.body ? { 'Content-Type': 'application/json' } : undefined,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    let payload: ApiErrorResponse | undefined;
    try {
      payload = (await response.json()) as ApiErrorResponse;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(
      payload?.error.code ?? 'INTERNAL_ERROR',
      payload?.error.message ?? `Request failed with status ${response.status}.`,
      response.status,
      payload?.error.details,
    );
  }

  return response.json() as Promise<T>;
}

export const apiMode = USE_MOCKS ? 'mocks' : 'live';
