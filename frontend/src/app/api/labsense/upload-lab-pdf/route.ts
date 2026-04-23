import { NextResponse } from "next/server";

import { getMessages, isLocale } from "@/lib/i18n";

import { buildUpstreamUrl, fetchUpstream, jsonError, parseUpstreamJson } from "../route-helpers";

export async function POST(request: Request) {
  const formData = await request.formData();
  const file = formData.get("file");
  const language = formData.get("language");
  const locale = typeof language === "string" && isLocale(language) ? language : "en";
  const t = getMessages(locale);

  if (!(file instanceof File)) {
    return jsonError(400, "missing_file", t.api.missingFile);
  }

  if (!file.name.toLowerCase().endsWith(".pdf")) {
    return jsonError(400, "invalid_file_type", t.api.invalidFileType);
  }

  if (file.size === 0) {
    return jsonError(400, "empty_file", t.api.emptyFile);
  }

  try {
    const response = await fetchUpstream(buildUpstreamUrl("/upload-lab-pdf"), {
      method: "POST",
      body: formData
    });

    const payload = await parseUpstreamJson(response);
    if (payload === null) {
      return jsonError(502, "invalid_upstream_response", t.api.invalidParserResponse);
    }

    return NextResponse.json(payload, { status: response.status });
  } catch (error) {
    const timedOut = error instanceof Error && (error.name === "TimeoutError" || error.name === "AbortError");
    const message = timedOut ? t.api.uploadTimedOut : t.api.uploadUnavailable;

    return jsonError(timedOut ? 504 : 502, "upstream_unavailable", message);
  }
}
