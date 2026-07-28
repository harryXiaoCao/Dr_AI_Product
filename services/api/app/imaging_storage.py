"""Synthetic imaging byte storage with an explicit Tencent COS boundary."""

from pathlib import Path

from app.config import Settings
from app.errors import ApiError


class ImagingStorage:
    provider: str

    def put(self, object_key: str, content: bytes) -> None:
        raise NotImplementedError

    def read(self, object_key: str) -> bytes:
        raise NotImplementedError


class LocalImagingStorage(ImagingStorage):
    provider = "local"

    def __init__(self, root: str) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, object_key: str) -> Path:
        target = (self.root / object_key).resolve()
        if self.root not in target.parents:
            raise ApiError(422, "validation_failed", "The storage key is invalid.")
        return target

    def put(self, object_key: str, content: bytes) -> None:
        target = self._path(object_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(f"{target.suffix}.upload")
        temporary.write_bytes(content)
        temporary.replace(target)

    def read(self, object_key: str) -> bytes:
        target = self._path(object_key)
        try:
            return target.read_bytes()
        except FileNotFoundError as error:
            raise ApiError(
                503,
                "service_unavailable",
                "The imaging bytes are temporarily unavailable.",
            ) from error


class TencentCosStorage(ImagingStorage):
    """Signer/storage boundary; live writes remain disabled in this repository."""

    provider = "tencent_cos"

    def put(self, object_key: str, content: bytes) -> None:
        del object_key, content
        raise ApiError(
            503,
            "service_unavailable",
            "Tencent COS upload signing is not active in this synthetic environment.",
        )

    def read(self, object_key: str) -> bytes:
        del object_key
        raise ApiError(
            503,
            "service_unavailable",
            "Tencent COS download signing is not active in this synthetic environment.",
        )


def imaging_storage(settings: Settings) -> ImagingStorage:
    if settings.imaging_storage_backend == "local":
        return LocalImagingStorage(settings.imaging_local_storage_root)
    return TencentCosStorage()
