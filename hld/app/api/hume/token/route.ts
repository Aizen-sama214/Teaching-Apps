import { NextResponse } from "next/server";
import { getHumeAccessToken } from "@/services/hume";

export const runtime = "nodejs";

export async function GET() {
	try {
		const token = await getHumeAccessToken();
		return NextResponse.json({ token });
	} catch (err: unknown) {
		const message = err instanceof Error ? err.message : "Failed to get token";
		return NextResponse.json({ error: message }, { status: 500 });
	}
}
