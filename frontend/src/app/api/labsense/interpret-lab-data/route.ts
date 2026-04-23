import { NextResponse } from "next/server";

import { getMessages, isLocale } from "@/lib/i18n";
import { interpretLabDataRequestSchema } from "@/lib/labsense-contract";

import { buildUpstreamUrl, fetchUpstream, jsonError, parseUpstreamJson } from "../route-helpers";

export async function POST(request: Request) {
  let body: unknown;

  try {
    body = await request.json();
  } catch {
    const t = getMessages("en");
    return jsonError(400, "invalid_json", t.api.invalidJson);
  }

  const locale =
    typeof body === "object" && body !== null && "language" in body && typeof body.language === "string" && isLocale(body.language)
      ? body.language
      : "en";
  const t = getMessages(locale);

  const parsedBody = interpretLabDataRequestSchema.safeParse(body);
  if (!parsedBody.success) {
    return jsonError(400, "invalid_payload", t.api.invalidPayload, parsedBody.error.flatten());
  }

  try {
    const response = await fetchUpstream(buildUpstreamUrl("/interpret-lab-data"), {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(parsedBody.data)
    });

    const payload = await parseUpstreamJson(response);
    if (payload === null) {
      return jsonError(502, "invalid_upstream_response", t.api.invalidInterpretationResponse);
    }

    return NextResponse.json(payload, { status: response.status });
  } catch (error) {
    const timedOut = error instanceof Error && (error.name === "TimeoutError" || error.name === "AbortError");
    const message = timedOut ? t.api.interpretationTimedOut : t.api.interpretationUnavailable;

    return jsonError(timedOut ? 504 : 502, "upstream_unavailable", message);
  }
}
