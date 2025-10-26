// app/api/items/route.ts
import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL;
if (!BACKEND) throw new Error("Set BACKEND_URL or NEXT_PUBLIC_API_URL");

export async function GET(_req: NextRequest) {
  const r = await fetch(`${BACKEND}/items`, { cache: "no-store" });
  const text = await r.text();
  try { return NextResponse.json(JSON.parse(text), { status: r.status }); }
  catch { return new NextResponse(text, { status: r.status }); }
}