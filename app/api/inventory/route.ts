// app/api/inventory/route.ts
import { NextRequest, NextResponse } from "next/server";

/**
 * Where to forward requests.
 * Prefer BACKEND_URL for server-only; fall back to NEXT_PUBLIC_API_URL so local dev “just works”.
 */
const BACKEND =
  process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "";

if (!BACKEND) {
  throw new Error(
    "Missing BACKEND_URL (or NEXT_PUBLIC_API_URL). Set it to your FastAPI base URL, e.g. http://localhost:8000"
  );
}

/**
 * Which backend path to hit for “inventory” operations.
 * Change this if your FastAPI uses a different route than /items.
 */
const INVENTORY_PATH = process.env.BACKEND_INVENTORY_PATH || "/items";

/** Utility: try to return JSON, otherwise return raw text */
async function passthroughResponse(r: Response) {
  const text = await r.text();
  try {
    return NextResponse.json(JSON.parse(text), { status: r.status });
  } catch {
    return new NextResponse(text, { status: r.status });
  }
}

/** GET /api/inventory?… → forwards to {BACKEND}{INVENTORY_PATH}?… */
export async function GET(req: NextRequest) {
  const qs = req.nextUrl.search; // includes leading "?" or empty string
  const url = `${BACKEND}${INVENTORY_PATH}${qs}`;

  const r = await fetch(url, {
    // no-store so you always see fresh data during dev
    cache: "no-store",
    // You can forward headers if you need auth:
    // headers: { Authorization: req.headers.get("authorization") ?? "" },
  });

  return passthroughResponse(r);
}

/**
 * POST /api/inventory
 * - If Content-Type is JSON → forward as JSON
 * - If multipart/form-data → forward the form (file uploads supported)
 * - Else (e.g. text/plain) → forward raw body with same content-type
 */
export async function POST(req: NextRequest) {
  const url = `${BACKEND}${INVENTORY_PATH}`;
  const ct = req.headers.get("content-type") || "";

  // JSON
  if (ct.includes("application/json")) {
    const bodyText = await req.text(); // preserve raw JSON
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: bodyText,
    });
    return passthroughResponse(r);
  }

  // multipart/form-data (file uploads)
  if (ct.includes("multipart/form-data")) {
    const form = await req.formData();
    // Important: do NOT set Content-Type manually; let fetch set the boundary
    const r = await fetch(url, { method: "POST", body: form });
    return passthroughResponse(r);
  }

  // Fallback: forward as-is (e.g., text/plain)
  const raw = await req.arrayBuffer();
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": ct },
    body: raw,
  });
  return passthroughResponse(r);
}

/** Optional: make preflight happy if the browser ever calls this route directly */
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
      "Access-Control-Max-Age": "86400",
    },
  });
}
