import { NextResponse } from "next/server";
import { addDocumentsToStore, splitToDocuments } from "@/services/langchain";

export const runtime = "nodejs";

export async function POST(request: Request) {
	try {
		const form = await request.formData();
		const file = form.get("file");
		if (!(file instanceof File)) {
			return NextResponse.json({ error: "No file provided" }, { status: 400 });
		}
		const text = await file.text();
		const docs = await splitToDocuments(text);
		await addDocumentsToStore(docs);
		return NextResponse.json({ ok: true, added: docs.length });
	} catch (err: unknown) {
		const message = err instanceof Error ? err.message : "Failed to ingest file";
		return NextResponse.json({ error: message }, { status: 500 });
	}
}
