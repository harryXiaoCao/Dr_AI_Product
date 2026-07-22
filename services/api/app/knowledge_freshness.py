from __future__ import annotations

import hashlib
import re
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import UTC, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.knowledge_ingestion import ImmutableArtifactStore
from app.models import (
    KbPublisher,
    KbRightsRecord,
    KbSourceCandidate,
    KbSourceFamily,
    KbSourceFetchRun,
)

FAMILY_MANIFEST_SCHEMA_VERSION = "1.0"
ONLINE_PARSER_VERSION = "governed-online-html-v1"
ALLOWED_CONTENT_TYPES = {"text/html", "application/xhtml+xml", "text/plain"}
PROMPT_INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"\bsystem\s+prompt\b", re.IGNORECASE),
    re.compile(r"忽略.{0,12}(先前|之前|以上).{0,12}(指令|要求|提示)"),
    re.compile(r"(泄露|显示|输出).{0,12}(系统提示|隐藏指令)"),
)
DATE_PATTERN = re.compile(r"(?:20\d{2})[-年/.](?:0?[1-9]|1[0-2])[-月/.](?:0?[1-9]|[12]\d|3[01])")


class SourceFamilyPublisher(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stable_id: str = Field(pattern=r"^KBP-[A-Z0-9-]+$")
    official_name_zh: str = Field(min_length=2, max_length=240)
    official_name_en: str | None = Field(default=None, max_length=240)
    organization_type: str = Field(min_length=2, max_length=80)
    authority_basis: str = Field(min_length=10)
    authority_evidence_locator: HttpUrl
    jurisdiction: str = Field(min_length=2, max_length=40)
    allowed_content_classes: list[str] = Field(min_length=1)


class SourceFamilyDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stable_id: str = Field(pattern=r"^KBF-[A-Z0-9-]+$")
    publisher: SourceFamilyPublisher
    name: str = Field(min_length=2, max_length=240)
    jurisdiction: str = Field(min_length=2, max_length=40)
    seed_locators: list[HttpUrl] = Field(min_length=1, max_length=10)
    allowed_domains: list[str] = Field(min_length=1, max_length=10)
    allowed_path_prefixes: list[str] = Field(min_length=1, max_length=20)
    content_classes: list[str] = Field(min_length=1, max_length=20)
    fetch_interval_minutes: int = Field(ge=15, le=43_200)
    max_response_bytes: int = Field(ge=1_024, le=10_000_000)
    capture_policy: Literal["metadata_only", "full_text"]
    rights_gate_status: Literal["pending", "approved", "denied"]
    status: Literal["active", "disabled"]
    max_discovered_fetches_per_run: int = Field(default=8, ge=0, le=25)

    @model_validator(mode="after")
    def validate_locators(self) -> SourceFamilyDefinition:
        domains = {domain.casefold() for domain in self.allowed_domains}
        for locator in self.seed_locators:
            if locator.scheme != "https" or (locator.host or "").casefold() not in domains:
                raise ValueError("Every seed locator must be HTTPS and use an allowlisted domain.")
            if not any(locator.path.startswith(prefix) for prefix in self.allowed_path_prefixes):
                raise ValueError("Every seed locator must use an allowlisted path prefix.")
        return self


class SourceFamilyManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    families: list[SourceFamilyDefinition] = Field(min_length=2)


class FetchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    locator: str
    status_code: int
    headers: dict[str, str]
    body: bytes


class SourceFetcher(Protocol):
    def __call__(self, locator: str, max_bytes: int) -> FetchResponse: ...


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        del req, fp, code, msg, headers, newurl
        return None


def fetch_https(locator: str, max_bytes: int) -> FetchResponse:
    request = urllib.request.Request(
        locator,
        headers={
            "Accept": "text/html,application/xhtml+xml,text/plain;q=0.8",
            "User-Agent": "DrAI-Governed-Knowledge-Monitor/1.0",
        },
        method="GET",
    )
    opener = urllib.request.build_opener(_NoRedirectHandler)
    try:
        with opener.open(request, timeout=10) as response:
            body = response.read(max_bytes + 1)
            headers = {key.casefold(): value for key, value in response.headers.items()}
            return FetchResponse(
                locator=response.geturl(),
                status_code=response.status,
                headers=headers,
                body=body,
            )
    except urllib.error.HTTPError as exc:
        if 300 <= exc.code < 400:
            raise ValueError("redirect_rejected") from exc
        raise ValueError("http_error") from exc
    except (OSError, urllib.error.URLError) as exc:
        raise ValueError("network_error") from exc


class _VisibleHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden_depth = 0
        self.text_parts: list[str] = []
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() in {"script", "style", "noscript", "template", "svg"}:
            self.hidden_depth += 1
        if tag.casefold() == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in {"script", "style", "noscript", "template", "svg"}:
            self.hidden_depth = max(self.hidden_depth - 1, 0)

    def handle_data(self, data: str) -> None:
        if self.hidden_depth == 0 and data.strip():
            self.text_parts.append(data.strip())


def load_source_family_manifest(path: Path) -> SourceFamilyManifest:
    return SourceFamilyManifest.model_validate_json(path.read_text(encoding="utf-8"))


def _normalized_domain(value: str) -> str:
    return value.rstrip(".").casefold()


def locator_is_allowed(family: KbSourceFamily, locator: str) -> bool:
    parsed = urllib.parse.urlsplit(locator)
    return (
        parsed.scheme == "https"
        and parsed.username is None
        and parsed.password is None
        and parsed.port in {None, 443}
        and _normalized_domain(parsed.hostname or "")
        in {_normalized_domain(domain) for domain in family.allowed_domains_json}
        and any(parsed.path.startswith(prefix) for prefix in family.allowed_path_prefixes_json)
        and not parsed.fragment
    )


def sync_source_families(
    db: Session,
    manifest: SourceFamilyManifest,
    *,
    now: datetime | None = None,
) -> tuple[int, int]:
    now = now or datetime.now(UTC)
    publishers_created = families_created = 0
    for item in manifest.families:
        publisher = db.scalar(
            select(KbPublisher).where(KbPublisher.stable_id == item.publisher.stable_id)
        )
        if publisher is None:
            publisher = KbPublisher(
                stable_id=item.publisher.stable_id,
                official_name_zh=item.publisher.official_name_zh,
                official_name_en=item.publisher.official_name_en,
                organization_type=item.publisher.organization_type,
                authority_basis=item.publisher.authority_basis,
                authority_evidence_locator=str(item.publisher.authority_evidence_locator),
                verified_domains_json=item.allowed_domains,
                jurisdiction=item.publisher.jurisdiction,
                review_status="authority_verified",
                allowed_content_classes_json=item.publisher.allowed_content_classes,
                reviewed_at=now,
            )
            db.add(publisher)
            db.flush()
            publishers_created += 1
        else:
            publisher.verified_domains_json = list(
                dict.fromkeys([*publisher.verified_domains_json, *item.allowed_domains])
            )
            publisher.allowed_content_classes_json = list(
                dict.fromkeys(
                    [
                        *publisher.allowed_content_classes_json,
                        *item.publisher.allowed_content_classes,
                    ]
                )
            )
        family = db.scalar(select(KbSourceFamily).where(KbSourceFamily.stable_id == item.stable_id))
        if family is None:
            family = KbSourceFamily(
                stable_id=item.stable_id,
                publisher_id=publisher.id,
                name=item.name,
                jurisdiction=item.jurisdiction,
                seed_locators_json=[str(locator) for locator in item.seed_locators],
                allowed_domains_json=item.allowed_domains,
                allowed_path_prefixes_json=item.allowed_path_prefixes,
                content_classes_json=item.content_classes,
                parser_version=ONLINE_PARSER_VERSION,
                fetch_interval_minutes=item.fetch_interval_minutes,
                max_response_bytes=item.max_response_bytes,
                capture_policy=item.capture_policy,
                rights_gate_status=item.rights_gate_status,
                status=item.status,
                next_check_at=now if item.status == "active" else None,
            )
            db.add(family)
            families_created += 1
            continue
        if family.status == "killed":
            continue
        family.name = item.name
        family.publisher_id = publisher.id
        family.jurisdiction = item.jurisdiction
        family.seed_locators_json = [str(locator) for locator in item.seed_locators]
        family.allowed_domains_json = item.allowed_domains
        family.allowed_path_prefixes_json = item.allowed_path_prefixes
        family.content_classes_json = item.content_classes
        family.parser_version = ONLINE_PARSER_VERSION
        family.fetch_interval_minutes = item.fetch_interval_minutes
        family.max_response_bytes = item.max_response_bytes
        family.capture_policy = item.capture_policy
        family.rights_gate_status = item.rights_gate_status
        family.status = item.status
        if family.status == "active" and family.next_check_at is None:
            family.next_check_at = now
    db.flush()
    return publishers_created, families_created


def _review_gates(
    family: KbSourceFamily,
    publisher: KbPublisher,
    security_status: str,
) -> dict[str, str]:
    return {
        "authority": (
            "approved"
            if publisher.review_status == "authority_verified"
            and bool(set(family.content_classes_json) & set(publisher.allowed_content_classes_json))
            else "pending"
        ),
        "rights": family.rights_gate_status,
        "security": security_status,
        "medical": "pending",
        "language": "pending",
        "jurisdiction": "pending",
        "readability": "pending",
        "retrieval_evaluation": "pending",
        "activation": "pending",
    }


def _approved_storage_rights(db: Session, family: KbSourceFamily) -> KbRightsRecord | None:
    return db.scalar(
        select(KbRightsRecord)
        .where(
            KbRightsRecord.publisher_id == family.publisher_id,
            KbRightsRecord.scope == "publisher",
            KbRightsRecord.decision_status == "approved",
            KbRightsRecord.storage_allowed.is_(True),
        )
        .order_by(KbRightsRecord.created_at.desc())
        .limit(1)
    )


def _inspect_body(
    family: KbSourceFamily,
    response: FetchResponse,
) -> tuple[str, list[str], str | None]:
    if response.status_code != 200:
        return "", [], "unexpected_http_status"
    if len(response.body) > family.max_response_bytes:
        return "", [], "response_too_large"
    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().casefold()
    if content_type not in ALLOWED_CONTENT_TYPES:
        return "", [], "unsupported_content_type"
    if b"\x00" in response.body:
        return "", [], "binary_content_rejected"
    charset = "utf-8"
    match = re.search(r"charset=([A-Za-z0-9._-]+)", response.headers.get("content-type", ""))
    if match:
        charset = match.group(1)
    try:
        decoded = response.body.decode(charset)
    except (LookupError, UnicodeDecodeError):
        return "", [], "malformed_text"
    parser = _VisibleHtmlParser()
    if content_type in {"text/html", "application/xhtml+xml"}:
        try:
            parser.feed(decoded)
            parser.close()
        except Exception:  # HTMLParser may surface malformed entity edge cases.
            return "", [], "parser_drift"
        visible_text = "\n".join(parser.text_parts)
        links = parser.links
    else:
        visible_text = decoded
        links = []
    visible_text = "\n".join(line.strip() for line in visible_text.splitlines() if line.strip())
    if len(visible_text) < 40:
        return visible_text, links, "unexpected_structure"
    if not DATE_PATTERN.search(visible_text):
        return visible_text, links, "missing_publisher_date"
    if any(pattern.search(visible_text) for pattern in PROMPT_INJECTION_PATTERNS):
        return visible_text, links, "prompt_injection_detected"
    return visible_text, links, None


def _allowed_links(family: KbSourceFamily, base: str, links: list[str]) -> list[str]:
    allowed: list[str] = []
    for link in links:
        locator = urllib.parse.urljoin(base, link)
        parsed = urllib.parse.urlsplit(locator)
        normalized = urllib.parse.urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, parsed.query, "")
        )
        if locator_is_allowed(family, normalized):
            allowed.append(normalized)
    return list(dict.fromkeys(allowed))


def _capture_response(
    db: Session,
    store: ImmutableArtifactStore,
    family: KbSourceFamily,
    publisher: KbPublisher,
    run: KbSourceFetchRun,
    locator: str,
    response: FetchResponse,
    *,
    captured_at: datetime,
) -> tuple[KbSourceCandidate | None, list[str], bool]:
    if response.locator != locator or not locator_is_allowed(family, response.locator):
        raise ValueError("redirect_rejected")
    checksum = hashlib.sha256(response.body).hexdigest()
    visible_text, links, quarantine_reason = _inspect_body(family, response)
    previous = db.scalar(
        select(KbSourceCandidate)
        .where(
            KbSourceCandidate.source_family_id == family.id,
            KbSourceCandidate.canonical_locator == locator,
        )
        .order_by(KbSourceCandidate.captured_at.desc())
        .limit(1)
    )
    if previous is not None and previous.body_checksum == checksum:
        return None, _allowed_links(family, locator, links), True
    raw_locator = normalized_locator = None
    storage_rights = _approved_storage_rights(db, family)
    if (
        quarantine_reason is None
        and family.capture_policy == "full_text"
        and family.rights_gate_status == "approved"
        and storage_rights is not None
    ):
        _, raw_locator = store.put("online-raw", response.body, "bin")
        _, normalized_locator = store.put("online-normalized", visible_text.encode(), "txt")
    security_status = "approved" if quarantine_reason is None else "rejected"
    gates = _review_gates(family, publisher, security_status)
    quarantine_status = (
        "rejected"
        if quarantine_reason
        else "awaiting_review"
        if all(gates[name] == "approved" for name in ("authority", "rights", "security"))
        else "rights_pending"
        if gates["rights"] == "pending"
        else "quarantined"
    )
    stable_suffix = hashlib.sha256(f"{family.stable_id}:{locator}:{checksum}".encode()).hexdigest()
    candidate = KbSourceCandidate(
        stable_id=f"KBC-{stable_suffix[:28].upper()}",
        source_family_id=family.id,
        fetch_run_id=run.id,
        canonical_locator=locator,
        content_class=family.content_classes_json[0],
        discovered_at=captured_at,
        captured_at=captured_at,
        http_status=response.status_code,
        content_type=response.headers.get("content-type", "unknown")[:160],
        etag=response.headers.get("etag"),
        last_modified=response.headers.get("last-modified"),
        body_checksum=checksum,
        body_bytes=len(response.body),
        raw_artifact_locator=raw_locator,
        normalized_artifact_locator=normalized_locator,
        parser_version=family.parser_version,
        change_state="new" if previous is None else "changed",
        quarantine_status=quarantine_status,
        quarantine_reason_code=quarantine_reason,
        review_gates_json=gates,
    )
    db.add(candidate)
    db.flush()
    return candidate, _allowed_links(family, locator, links), False


def run_source_family_fetch(
    db: Session,
    store: ImmutableArtifactStore,
    family: KbSourceFamily,
    *,
    fetcher: SourceFetcher = fetch_https,
    now: datetime | None = None,
    max_discovered_fetches: int = 8,
) -> KbSourceFetchRun:
    now = now or datetime.now(UTC)
    if family.status != "active":
        raise ValueError("source_family_not_active")
    publisher = db.get(KbPublisher, family.publisher_id)
    if publisher is None or publisher.revoked_at is not None:
        raise ValueError("publisher_not_authorized")
    run = KbSourceFetchRun(
        stable_id=f"KBFR-{uuid.uuid4().hex.upper()}",
        source_family_id=family.id,
        started_at=now,
        status="running",
        metadata_json={"parser_version": family.parser_version},
    )
    db.add(run)
    db.flush()
    queue = list(family.seed_locators_json)
    seen: set[str] = set()
    seed_set = set(queue)
    successful_fetches = 0
    errors: list[str] = []
    discovered: list[str] = []
    while queue:
        locator = queue.pop(0)
        if locator in seen:
            continue
        seen.add(locator)
        if not locator_is_allowed(family, locator):
            errors.append("locator_not_allowlisted")
            continue
        run.attempted_count += 1
        try:
            response = fetcher(locator, family.max_response_bytes)
            candidate, links, unchanged = _capture_response(
                db,
                store,
                family,
                publisher,
                run,
                locator,
                response,
                captured_at=now,
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        successful_fetches += 1
        if unchanged:
            run.unchanged_count += 1
        elif candidate is not None:
            run.changed_count += 1
            if candidate.quarantine_status != "awaiting_review":
                run.quarantined_count += 1
        if locator in seed_set:
            discovered.extend(link for link in links if link not in seed_set)
            remaining = max(0, max_discovered_fetches - len(queue))
            queue.extend([link for link in links if link not in seen][:remaining])
    run.discovered_locator_count = len(set(discovered))
    run.completed_at = now
    family.last_checked_at = now
    if successful_fetches:
        family.next_check_at = now + timedelta(minutes=family.fetch_interval_minutes)
        run.status = "succeeded" if not errors else "partial_failure"
        run.error_code = errors[0] if errors else None
        run.metadata_json = {
            "parser_version": family.parser_version,
            "error_count": len(errors),
        }
        family.last_success_at = now
        family.consecutive_failures = 0
    else:
        family.next_check_at = now + timedelta(
            minutes=min(15, family.fetch_interval_minutes)
        )
        run.status = "failed"
        run.error_code = errors[0] if errors else "no_fetches_completed"
        run.metadata_json = {
            "parser_version": family.parser_version,
            "error_count": len(errors),
        }
        family.consecutive_failures += 1
    db.flush()
    return run


def run_due_source_families(
    db: Session,
    store: ImmutableArtifactStore,
    *,
    fetcher: SourceFetcher = fetch_https,
    now: datetime | None = None,
    max_discovered_fetches: int = 8,
    force: bool = False,
) -> list[KbSourceFetchRun]:
    now = now or datetime.now(UTC)
    query = select(KbSourceFamily).where(KbSourceFamily.status == "active")
    if not force:
        query = query.where(
            or_(
                KbSourceFamily.next_check_at.is_(None),
                KbSourceFamily.next_check_at <= now,
            )
        )
    families = list(db.scalars(query.order_by(KbSourceFamily.stable_id)))
    return [
        run_source_family_fetch(
            db,
            store,
            family,
            fetcher=fetcher,
            now=now,
            max_discovered_fetches=max_discovered_fetches,
        )
        for family in families
    ]


def set_source_family_kill_switch(
    db: Session,
    *,
    stable_id: str,
    killed: bool,
    actor_id: str,
    reason_code: str,
    now: datetime | None = None,
) -> KbSourceFamily:
    now = now or datetime.now(UTC)
    family = db.scalar(select(KbSourceFamily).where(KbSourceFamily.stable_id == stable_id))
    if family is None:
        raise ValueError("source_family_not_found")
    if killed:
        family.status = "killed"
        family.killed_at = now
        family.killed_by = actor_id
        family.kill_reason_code = reason_code
        family.next_check_at = None
    else:
        family.status = "active"
        family.killed_at = None
        family.killed_by = None
        family.kill_reason_code = None
        family.next_check_at = now
    db.flush()
    return family


def freshness_snapshot(
    db: Session,
    *,
    now: datetime | None = None,
) -> list[dict[str, object]]:
    now = now or datetime.now(UTC)
    result: list[dict[str, object]] = []
    for family in db.scalars(select(KbSourceFamily).order_by(KbSourceFamily.stable_id)):
        stale_after = timedelta(minutes=family.fetch_interval_minutes * 2)
        is_stale = family.status == "active" and (
            family.last_success_at is None or now - family.last_success_at > stale_after
        )
        pending_count = len(
            list(
                db.scalars(
                    select(KbSourceCandidate.id).where(
                        KbSourceCandidate.source_family_id == family.id,
                        KbSourceCandidate.quarantine_status.in_(
                            ["rights_pending", "quarantined", "awaiting_review"]
                        ),
                    )
                )
            )
        )
        result.append(
            {
                "source_family_id": family.stable_id,
                "status": family.status,
                "rights_gate_status": family.rights_gate_status,
                "last_checked_at": family.last_checked_at,
                "last_success_at": family.last_success_at,
                "next_check_at": family.next_check_at,
                "consecutive_failures": family.consecutive_failures,
                "is_stale": is_stale,
                "pending_candidate_count": pending_count,
                "kill_reason_code": family.kill_reason_code,
            }
        )
    return result
