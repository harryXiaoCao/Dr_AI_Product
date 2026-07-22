from __future__ import annotations

import hashlib
import os
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from threading import Lock
from typing import Annotated, Literal

import numpy
import onnxruntime
import torch
import torch.nn.functional as functional
from fastapi import FastAPI, HTTPException
from huggingface_hub import hf_hub_download
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer

EMBEDDING_REPOSITORY = "Alibaba-NLP/gte-multilingual-base"
EMBEDDING_REVISION = "9bbca17d9273fd0d03d5725c7a4b0f6b45142062"
RERANKER_REPOSITORY = "Alibaba-NLP/gte-multilingual-reranker-base"
RERANKER_REVISION = "8215cf04918ba6f7b6a62bb44238ce2953d8831c"
RERANKER_ONNX_REPOSITORY = "onnx-community/gte-multilingual-reranker-base"
RERANKER_ONNX_REVISION = "ee64367e35a2db0da46bb6497e13a18f8bd585cb"
RERANKER_ONNX_FILENAME = "onnx/model_int8.onnx"
RERANKER_ONNX_SHA256 = "ccf51dba7f8aa9205753761cfaa68c55f741792501463a3bf25d7e5bcdac7c35"
REMOTE_CODE_REVISION = "40ced75c3017eb27626c9d4ea981bde21a2662f4"
EMBEDDING_DIMENSIONS = 768


class ServiceSettings(BaseSettings):
    embedding_api_model: str = f"{EMBEDDING_REPOSITORY}@{EMBEDDING_REVISION[:12]}"
    reranker_api_model: str = f"{RERANKER_REPOSITORY}@{RERANKER_REVISION[:12]}"
    reranker_runtime: Literal["pytorch", "onnx_int8"] = "pytorch"
    max_batch_size: int = Field(default=30, ge=1, le=30)
    max_input_tokens: int = Field(default=512, ge=64, le=8192)
    torch_threads: int = Field(default=min(4, os.cpu_count() or 1), ge=1, le=32)
    local_files_only: bool = False
    model_cache_dir: str | None = None

    model_config = SettingsConfigDict(env_prefix="DR_AI_RETRIEVAL_", extra="ignore")


class EmbeddingRequest(BaseModel):
    model: str
    input: Annotated[list[str], Field(min_length=1, max_length=30)]

    @model_validator(mode="after")
    def reject_blank_input(self) -> "EmbeddingRequest":
        if any(not value.strip() for value in self.input):
            raise ValueError("embedding input must not contain blank strings")
        return self


class RerankDocument(BaseModel):
    id: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=20_000)


class RerankRequest(BaseModel):
    model: str
    query: str = Field(min_length=1, max_length=2_000)
    documents: Annotated[list[RerankDocument], Field(min_length=1, max_length=30)]

    @model_validator(mode="after")
    def reject_duplicate_ids(self) -> "RerankRequest":
        ids = [item.id for item in self.documents]
        if len(ids) != len(set(ids)):
            raise ValueError("reranker document IDs must be unique")
        return self


@dataclass
class RuntimeModels:
    embedding_tokenizer: object
    embedding_model: object
    reranker_tokenizer: object
    reranker_model: object
    loaded_at: float


settings = ServiceSettings()
runtime: RuntimeModels | None = None
inference_lock = Lock()


def _from_pretrained_options(revision: str) -> dict[str, object]:
    return {
        "revision": revision,
        "cache_dir": settings.model_cache_dir,
        "local_files_only": settings.local_files_only,
        "trust_remote_code": True,
        "code_revision": REMOTE_CODE_REVISION,
    }


def load_models() -> RuntimeModels:
    torch.set_num_threads(settings.torch_threads)
    embedding_options = _from_pretrained_options(EMBEDDING_REVISION)
    reranker_options = _from_pretrained_options(RERANKER_REVISION)
    embedding_tokenizer = AutoTokenizer.from_pretrained(
        EMBEDDING_REPOSITORY, fix_mistral_regex=False, **embedding_options
    )
    embedding_model = AutoModel.from_pretrained(
        EMBEDDING_REPOSITORY, dtype="auto", **embedding_options
    )
    embedding_model.eval()
    reranker_tokenizer = AutoTokenizer.from_pretrained(
        RERANKER_REPOSITORY, fix_mistral_regex=False, **reranker_options
    )
    if settings.reranker_runtime == "onnx_int8":
        reranker_path = hf_hub_download(
            repo_id=RERANKER_ONNX_REPOSITORY,
            filename=RERANKER_ONNX_FILENAME,
            revision=RERANKER_ONNX_REVISION,
            cache_dir=settings.model_cache_dir,
            local_files_only=settings.local_files_only,
        )
        with open(reranker_path, "rb") as model_file:
            model_checksum = hashlib.file_digest(model_file, "sha256").hexdigest()
        if model_checksum != RERANKER_ONNX_SHA256:
            raise RuntimeError("The pinned reranker ONNX artifact checksum does not match.")
        session_options = onnxruntime.SessionOptions()
        session_options.intra_op_num_threads = settings.torch_threads
        session_options.inter_op_num_threads = 1
        session_options.graph_optimization_level = (
            onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
        )
        reranker_model = onnxruntime.InferenceSession(
            reranker_path,
            sess_options=session_options,
            providers=["CPUExecutionProvider"],
        )
    else:
        reranker_model = AutoModelForSequenceClassification.from_pretrained(
            RERANKER_REPOSITORY, dtype="auto", **reranker_options
        )
        reranker_model.eval()
    return RuntimeModels(
        embedding_tokenizer=embedding_tokenizer,
        embedding_model=embedding_model,
        reranker_tokenizer=reranker_tokenizer,
        reranker_model=reranker_model,
        loaded_at=time.time(),
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    global runtime
    runtime = load_models()
    yield
    runtime = None


app = FastAPI(title="Dr. AI Retrieval Inference", version="0.1.0", lifespan=lifespan)


def _runtime() -> RuntimeModels:
    if runtime is None:
        raise HTTPException(status_code=503, detail="models are not ready")
    return runtime


@app.get("/health")
def health() -> dict[str, object]:
    models = _runtime()
    return {
        "status": "ok",
        "embedding_model": settings.embedding_api_model,
        "reranker_model": settings.reranker_api_model,
        "reranker_runtime": settings.reranker_runtime,
        "reranker_runtime_artifact": (
            f"{RERANKER_ONNX_REPOSITORY}@{RERANKER_ONNX_REVISION[:12]}:"
            f"{RERANKER_ONNX_FILENAME}#{RERANKER_ONNX_SHA256[:12]}"
            if settings.reranker_runtime == "onnx_int8"
            else f"{RERANKER_REPOSITORY}@{RERANKER_REVISION[:12]}:pytorch"
        ),
        "embedding_dimensions": EMBEDDING_DIMENSIONS,
        "max_batch_size": settings.max_batch_size,
        "max_input_tokens": settings.max_input_tokens,
        "loaded_at": models.loaded_at,
    }


@app.post("/v1/embeddings")
def embeddings(payload: EmbeddingRequest) -> dict[str, object]:
    if payload.model != settings.embedding_api_model:
        raise HTTPException(status_code=409, detail="embedding model version mismatch")
    if len(payload.input) > settings.max_batch_size:
        raise HTTPException(status_code=413, detail="embedding batch exceeds service limit")
    models = _runtime()
    started = time.perf_counter()
    with inference_lock, torch.inference_mode():
        encoded = models.embedding_tokenizer(
            payload.input,
            max_length=settings.max_input_tokens,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        output = models.embedding_model(**encoded)
        vectors = functional.normalize(output.last_hidden_state[:, 0], p=2, dim=1)
    rows = vectors.float().cpu().tolist()
    return {
        "model": settings.embedding_api_model,
        "embeddings": rows,
        "dimensions": EMBEDDING_DIMENSIONS,
        "latency_ms": round((time.perf_counter() - started) * 1000),
    }


@app.post("/rerank")
def rerank(payload: RerankRequest) -> dict[str, object]:
    if payload.model != settings.reranker_api_model:
        raise HTTPException(status_code=409, detail="reranker model version mismatch")
    if len(payload.documents) > settings.max_batch_size:
        raise HTTPException(status_code=413, detail="reranker batch exceeds service limit")
    models = _runtime()
    pairs = [[payload.query, item.text] for item in payload.documents]
    started = time.perf_counter()
    with inference_lock:
        encoded = models.reranker_tokenizer(
            pairs,
            max_length=settings.max_input_tokens,
            padding=True,
            truncation=True,
            return_tensors="np" if settings.reranker_runtime == "onnx_int8" else "pt",
        )
        if settings.reranker_runtime == "onnx_int8":
            input_names = {item.name for item in models.reranker_model.get_inputs()}
            if "token_type_ids" in input_names and "token_type_ids" not in encoded:
                encoded["token_type_ids"] = numpy.zeros_like(encoded["input_ids"])
            outputs = models.reranker_model.run(
                None,
                {name: value for name, value in encoded.items() if name in input_names},
            )
            scores = [float(value) for value in outputs[0].reshape(-1)]
        else:
            with torch.inference_mode():
                output = models.reranker_model(**encoded, return_dict=True)
                scores = output.logits.view(-1).float().cpu().tolist()
    results = [
        {"id": item.id, "score": float(score)}
        for item, score in zip(payload.documents, scores, strict=True)
    ]
    results.sort(key=lambda item: (-item["score"], item["id"]))
    return {
        "model": settings.reranker_api_model,
        "results": results,
        "latency_ms": round((time.perf_counter() - started) * 1000),
    }
