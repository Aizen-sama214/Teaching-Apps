import { NextResponse } from "next/server";
import { similaritySearch } from "@/services/langchain";

export const runtime = "nodejs";

export async function POST(request: Request) {
	try {
		const { query, k } = await request.json();
		if (!query) return NextResponse.json({ error: "Missing query" }, { status: 400 });
		const results = await similaritySearch(query, k ?? 4);
		return NextResponse.json({ results });
	} catch (err: unknown) {
		const message = err instanceof Error ? err.message : "Failed to query store";
		return NextResponse.json({ error: message }, { status: 500 });
	}
}
