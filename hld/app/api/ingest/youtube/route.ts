import { NextResponse } from "next/server";
import { addDocumentsToStore, splitToDocuments } from "@/services/langchain";

export const runtime = "nodejs";

async function fetchTranscriptFromYouTube(url: string): Promise<string> {
	// lightweight transcript fetcher using public transcript API if available
	// For robustness, you'd use a server-side loader from LangChain community.
	const videoIdMatch = url.match(/[?&]v=([^&]+)/) || url.match(/youtu\.be\/([^?]+)/);
	const videoId = videoIdMatch?.[1];
	if (!videoId) throw new Error("Invalid YouTube URL");
	const resp = await fetch(`https://youtubetranscriptdata.sumanjay.workers.dev/?video_id=${videoId}`);
	if (!resp.ok) throw new Error("Transcript not available");
	const data: unknown = await resp.json();
	if (!Array.isArray(data)) throw new Error("Unexpected transcript format");
	return data
		.map((item) => (typeof item === "object" && item !== null && "text" in item ? String((item as { text: unknown }).text ?? "") : ""))
		.join(" ");
}

export async function POST(request: Request) {
	try {
		const { url } = await request.json();
		if (!url) return NextResponse.json({ error: "Missing url" }, { status: 400 });
		const transcript = await fetchTranscriptFromYouTube(url);
		const docs = await splitToDocuments(transcript);
		await addDocumentsToStore(docs);
		return NextResponse.json({ ok: true, added: docs.length });
	} catch (err: unknown) {
		const message = err instanceof Error ? err.message : "Failed to ingest YouTube";
		return NextResponse.json({ error: message }, { status: 500 })
	}
}
