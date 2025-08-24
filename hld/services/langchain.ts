"use server";

import "server-only";
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";
import { Document } from "langchain/document";
import { OpenAIEmbeddings } from "@langchain/openai";
import { HNSWLib } from "@langchain/community/vectorstores/hnswlib";

let vectorStorePromise: Promise<HNSWLib> | null = null;

export async function splitToDocuments(text: string): Promise<Document[]> {
	const splitter = new RecursiveCharacterTextSplitter({
		chunkSize: 1000,
		chunkOverlap: 200,
	});
	return splitter.createDocuments([text]);
}

export async function getVectorStore(): Promise<HNSWLib> {
	if (!vectorStorePromise) {
		vectorStorePromise = HNSWLib.fromDocuments([], new OpenAIEmbeddings());
	}
	return vectorStorePromise;
}

export async function addDocumentsToStore(docs: Document[]): Promise<void> {
	const store = await getVectorStore();
	await store.addDocuments(docs);
}

export async function similaritySearch(query: string, k = 4) {
	const store = await getVectorStore();
	return store.similaritySearch(query, k);
}
