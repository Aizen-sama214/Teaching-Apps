"use client";

import { useState } from "react";

type QueryResult = { pageContent: string; metadata?: Record<string, unknown> };

export default function KnowledgeUploader() {
	const [file, setFile] = useState<File | null>(null);
	const [youtubeUrl, setYoutubeUrl] = useState("");
	const [pastedText, setPastedText] = useState("");
	const [query, setQuery] = useState("");
	const [results, setResults] = useState<QueryResult[]>([]);
	const [status, setStatus] = useState<string>("");

	async function uploadFile() {
		if (!file) return;
		setStatus("Uploading...");
		const fd = new FormData();
		fd.append("file", file);
		const resp = await fetch("/api/ingest/upload", { method: "POST", body: fd });
		const json = await resp.json();
		setStatus(resp.ok ? `Added ${json.added} chunks` : json.error || "Upload failed");
	}

	async function addYouTube() {
		if (!youtubeUrl) return;
		setStatus("Fetching transcript...");
		const resp = await fetch("/api/ingest/youtube", { method: "POST", body: JSON.stringify({ url: youtubeUrl }), headers: { "Content-Type": "application/json" } });
		const json = await resp.json();
		setStatus(resp.ok ? `Added ${json.added} chunks` : json.error || "YouTube ingest failed");
	}

	async function addText() {
		if (!pastedText.trim()) return;
		setStatus("Adding text...");
		const resp = await fetch("/api/ingest/text", { method: "POST", body: JSON.stringify({ text: pastedText }), headers: { "Content-Type": "application/json" } });
		const json = await resp.json();
		setStatus(resp.ok ? `Added ${json.added} chunks` : json.error || "Text ingest failed");
		if (resp.ok) setPastedText("");
	}

	async function runQuery() {
		if (!query) return;
		setStatus("Searching...");
		const resp = await fetch("/api/query", { method: "POST", body: JSON.stringify({ query }), headers: { "Content-Type": "application/json" } });
		const json = await resp.json();
		if (resp.ok) {
			setResults(json.results || []);
			setStatus("");
		} else {
			setStatus(json.error || "Query failed");
		}
	}

	return (
		<div className="flex flex-col gap-3 max-w-xl w-full">
			<div className="flex items-center gap-2">
				<input type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
				<button className="rounded border px-3 py-2" onClick={uploadFile}>Upload</button>
			</div>
			<div className="flex items-center gap-2">
				<input className="border rounded px-2 py-1 flex-1" placeholder="YouTube URL" value={youtubeUrl} onChange={(e) => setYoutubeUrl(e.target.value)} />
				<button className="rounded border px-3 py-2" onClick={addYouTube}>Add</button>
			</div>
			<div className="flex flex-col gap-2">
				<textarea className="border rounded px-2 py-1 w-full h-32" placeholder="Paste text to ingest" value={pastedText} onChange={(e) => setPastedText(e.target.value)} />
				<div className="flex justify-end">
					<button className="rounded border px-3 py-2" onClick={addText}>Add Text</button>
				</div>
			</div>
			<div className="flex items-center gap-2">
				<input className="border rounded px-2 py-1 flex-1" placeholder="Ask a question" value={query} onChange={(e) => setQuery(e.target.value)} />
				<button className="rounded border px-3 py-2" onClick={runQuery}>Search</button>
			</div>
			{status && <div className="text-sm opacity-80">{status}</div>}
			{results.length > 0 && (
				<div className="border rounded p-3">
					<div className="font-semibold mb-2">Top results</div>
					<ol className="list-decimal pl-4">
						{results.map((r, i) => (
							<li key={i} className="mb-2 whitespace-pre-wrap">{r.pageContent}</li>
						))}
					</ol>
				</div>
			)}
		</div>
	);
}
