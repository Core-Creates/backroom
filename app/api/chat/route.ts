// app/api/chat/route.ts
import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL;
if (!BACKEND) throw new Error("Set BACKEND_URL or NEXT_PUBLIC_API_URL");

export async function POST(req: NextRequest) {
  const body = await req.text(); // forward raw JSON
  const r = await fetch(`${BACKEND}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });
  const text = await r.text();
  try { return NextResponse.json(JSON.parse(text), { status: r.status }); }
  catch { return new NextResponse(text, { status: r.status }); }
}