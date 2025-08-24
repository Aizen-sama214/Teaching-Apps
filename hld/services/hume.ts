"use server";

import "server-only";
import { fetchAccessToken } from "hume";

export async function getHumeAccessToken(): Promise<string> {
	const apiKey = process.env.HUME_API_KEY;
	const secretKey = process.env.HUME_SECRET_KEY;
	if (!apiKey || !secretKey) {
		throw new Error("Missing HUME_API_KEY or HUME_SECRET_KEY environment variables");
	}
	const token = await fetchAccessToken({ apiKey, secretKey });
	return token;
}
