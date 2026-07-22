from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.request


def _post(url: str, payload: dict[str, object]) -> tuple[dict[str, object], float]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.loads(response.read())
    return result, (time.perf_counter() - started) * 1000


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8090")
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    with urllib.request.urlopen(f"{args.base_url}/health", timeout=5) as response:
        health = json.loads(response.read())
    embedding_latencies = []
    reranker_latencies = []
    relevant_ranked_first = []
    documents = [
        {"id": "blood-pressure", "text": "定期测量并记录血压有助于了解血压变化。"},
        {"id": "hiv", "text": "HIV 检测用于发现人类免疫缺陷病毒感染。"},
        {"id": "cholesterol", "text": "血脂检查包括胆固醇和甘油三酯。"},
        {"id": "cancer", "text": "癌症筛查的选择取决于年龄和风险。"},
    ]
    for _ in range(args.runs):
        embedding, latency = _post(
            f"{args.base_url}/v1/embeddings",
            {
                "model": health["embedding_model"],
                "input": ["为什么需要定期测量血压？", documents[0]["text"]],
            },
        )
        embedding_latencies.append(latency)
        if embedding.get("dimensions") != 768:
            raise SystemExit("embedding dimension mismatch")
        reranked, latency = _post(
            f"{args.base_url}/rerank",
            {
                "model": health["reranker_model"],
                "query": "为什么需要定期测量血压？",
                "documents": documents,
            },
        )
        reranker_latencies.append(latency)
        relevant_ranked_first.append(reranked["results"][0]["id"] == "blood-pressure")
    print(
        json.dumps(
            {
                "host_contract": health,
                "runs": args.runs,
                "embedding_median_ms": round(statistics.median(embedding_latencies)),
                "reranker_median_ms": round(statistics.median(reranker_latencies)),
                "relevant_ranked_first_rate": sum(relevant_ranked_first) / args.runs,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
