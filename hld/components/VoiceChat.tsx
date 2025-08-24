"use client";

import { useState } from "react";
import { VoiceProvider, useVoice, VoiceReadyState } from "@humeai/voice-react";

function StartStop() {
	const { connect, disconnect, readyState } = useVoice();
	const [loading, setLoading] = useState(false);

	const start = async () => {
		setLoading(true);
		try {
			const resp = await fetch("/api/hume/token");
			const json = await resp.json();
			if (!resp.ok) throw new Error(json.error || "Failed to get token");
			await connect({ auth: { type: "accessToken", value: json.token } });
		} catch (e) {
			console.error(e);
		} finally {
			setLoading(false);
		}
	};

	if (readyState === VoiceReadyState.OPEN) {
		return (
			<button className="rounded border px-3 py-2" onClick={disconnect}>End Session</button>
		);
	}
	return (
		<button className="rounded border px-3 py-2" onClick={start} disabled={loading}>
			{loading ? "Starting..." : "Start Voice Session"}
		</button>
	);
}

export default function VoiceChat() {
	return (
		<div className="flex flex-col gap-3">
			<VoiceProvider>
				<StartStop />
			</VoiceProvider>
		</div>
	);
}
