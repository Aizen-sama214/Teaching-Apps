import { NextResponse } from "next/server";
import { addDocumentsToStore, splitToDocuments } from "@/services/langchain";

export const runtime = "nodejs";

export async function POST(request: Request) {
    try {
        const { text } = await request.json();
        if (!text || typeof text !== "string" || text.trim().length === 0) {
            return NextResponse.json({ error: "Missing text" }, { status: 400 });
        }
        const docs = await splitToDocuments(text);
        await addDocumentsToStore(docs);
        return NextResponse.json({ ok: true, added: docs.length });
    } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Failed to ingest text";
        return NextResponse.json({ error: message }, { status: 500 });
    }
}


