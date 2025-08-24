# HLD App

## Voice + RAG Setup

1. Create `.env.local` in project root with:

```
HUME_API_KEY=your_key
HUME_SECRET_KEY=your_secret
OPENAI_API_KEY=your_openai_key
```

2. Install deps:

```
npm install @humeai/voice-react hume @langchain/community @langchain/core @langchain/openai langchain hnswlib-node
```

3. Run the dev server:

```
npm run dev
```

## Features
- Voice chat via Hume EVI: see `components/VoiceChat.tsx` and `app/api/hume/token/route.ts`.
- Knowledge ingestion: upload files at `POST /api/ingest/upload` and YouTube links at `POST /api/ingest/youtube`.
- Query vector store: `POST /api/query`.

## Notes
- Routes use `runtime = "nodejs"` to support native deps.
- This demo keeps an in-memory HNSW vector store; restart clears data.
