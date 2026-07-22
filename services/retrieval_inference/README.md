# Dr. AI retrieval inference service

This private service exposes the exact HTTP contracts consumed by the Dr. AI
API while testing the 4-vCPU/8-GB candidate pair:

- `Alibaba-NLP/gte-multilingual-base` at immutable revision
  `9bbca17d9273fd0d03d5725c7a4b0f6b45142062`;
- `Alibaba-NLP/gte-multilingual-reranker-base` at immutable revision
  `8215cf04918ba6f7b6a62bb44238ce2953d8831c`;
- the optional CPU INT8 export from
  `onnx-community/gte-multilingual-reranker-base` at immutable revision
  `ee64367e35a2db0da46bb6497e13a18f8bd585cb`, with the expected model-file
  SHA-256 verified before loading;
- Alibaba's shared remote model code at immutable revision
  `40ced75c3017eb27626c9d4ea981bde21a2662f4`.

The service intentionally caps embeddings and reranking at 30 inputs and 512
tokens per input. It runs one worker and serializes inference to keep peak CPU
and memory bounded. It does not make this model pair production-approved: the
immutable knowledge index must be rebuilt with the embedding version, then the
frozen Slice 9A and Slice 9B gates must pass before activation.

## Local run

```bash
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 8090 --workers 1
```

In another terminal:

```bash
uv run python scripts/benchmark.py --runs 3
DR_AI_RETRIEVAL_LOCAL_FILES_ONLY=true uv run python -m scripts.measure_runtime
```

Model files are downloaded into the Hugging Face cache. Set
`DR_AI_RETRIEVAL_MODEL_CACHE_DIR` to an attached model volume on the CVM, and
set `DR_AI_RETRIEVAL_LOCAL_FILES_ONLY=true` after the model revisions have been
prefetched. Set `DR_AI_RETRIEVAL_RERANKER_RUNTIME=onnx_int8` for the bounded
CPU-optimized reranker, or retain the default `pytorch` runtime for comparison.
The `/health` response identifies the exact runtime artifact. Do not expose
port 8090 publicly; allow only the API host/private network security group.

Configure the main API with the exact versions returned by `/health`:

```dotenv
DR_AI_KNOWLEDGE_EMBEDDING_BACKEND=http_service
DR_AI_KNOWLEDGE_EMBEDDING_SERVICE_URL=http://127.0.0.1:8090/v1/embeddings
DR_AI_KNOWLEDGE_EMBEDDING_MODEL=Alibaba-NLP/gte-multilingual-base@9bbca17d9273
DR_AI_KNOWLEDGE_RERANKER_BACKEND=http_service
DR_AI_KNOWLEDGE_RERANKER_SERVICE_URL=http://127.0.0.1:8090/rerank
DR_AI_KNOWLEDGE_RERANKER_MODEL=Alibaba-NLP/gte-multilingual-reranker-base@8215cf04918b
```
