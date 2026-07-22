from __future__ import annotations

import json
import platform
import resource
import time

from app import main


def _peak_rss_mib() -> float:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    bytes_used = peak if platform.system() == "Darwin" else peak * 1024
    return round(bytes_used / (1024 * 1024), 1)


def run() -> int:
    started = time.perf_counter()
    main.runtime = main.load_models()
    load_seconds = time.perf_counter() - started
    embedding_started = time.perf_counter()
    embedding = main.embeddings(
        main.EmbeddingRequest(
            model=main.settings.embedding_api_model,
            input=["为什么需要定期测量血压？", "定期记录血压有助于了解血压变化。"],
        )
    )
    embedding_ms = (time.perf_counter() - embedding_started) * 1000
    rerank_started = time.perf_counter()
    reranked = main.rerank(
        main.RerankRequest.model_validate(
            {
                "model": main.settings.reranker_api_model,
                "query": "为什么需要定期测量血压？",
                "documents": [
                    {"id": "blood-pressure", "text": "定期记录血压有助于了解血压变化。"},
                    {"id": "hiv", "text": "HIV 检测用于发现病毒感染。"},
                    {"id": "cholesterol", "text": "血脂检查包括胆固醇。"},
                    {"id": "cancer", "text": "癌症筛查取决于年龄和风险。"},
                ],
            }
        )
    )
    rerank_ms = (time.perf_counter() - rerank_started) * 1000
    print(
        json.dumps(
            {
                "host": platform.platform(),
                "torch_threads": main.settings.torch_threads,
                "model_load_seconds": round(load_seconds, 2),
                "peak_rss_mib": _peak_rss_mib(),
                "embedding_dimensions": embedding["dimensions"],
                "embedding_ms": round(embedding_ms),
                "reranker_ms": round(rerank_ms),
                "top_reranker_id": reranked["results"][0]["id"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
