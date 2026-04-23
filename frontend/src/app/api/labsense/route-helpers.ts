import { NextResponse } from "next/server";

const API_BASE = process.env.LABSENSE_API_BASE_URL || "http://127.0.0.1:8000";
const UPSTREAM_TIMEOUT_MS = 60_000;

export function buildUpstreamUrl(pathname: string): string {
  return `${API_BASE}${pathname}`;
}

export function jsonError(status: number, error: string, message: string, detail?: unknown) {
  return NextResponse.json(
    {
      error,
      message,
      detail
    },
    { status }
  );
}

export async function parseUpstreamJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

export async function fetchUpstream(input: string, init: RequestInit): Promise<Response> {
  return fetch(input, {
    ...init,
    cache: "no-store",
    signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS)
  });
}
