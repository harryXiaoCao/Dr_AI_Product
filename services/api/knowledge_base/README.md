# Dr. AI Knowledge Ingestion Foundation

This directory contains governed source-catalog inputs, not an unrestricted
web scrape. The checked-in v1 catalog contains 298 official resources verified
on 2026-07-14: all 239 WHO Chinese fact sheets, all 241 WHO English fact
sheets, and 52 国家卫生健康委员会 guidelines or clinical protocols. The 234
exact WHO slug matches are stored as bilingual records; five Chinese and seven
English unmatched pages remain accurately monolingual, producing 246 distinct
WHO catalog records.

## Current admission state

- Publisher authority: verified for the official WHO Chinese/English fact-sheet
  channels and the official 国家卫生健康委员会 guideline channels.
- Stored content: titles, language status, source type, and official locators
  only.
- Article body: not stored, transformed, embedded, excerpted, or sent to a
  model provider.
- Rights state: pending. Commercial reuse permission has not been recorded for
  either publisher.
- Medical/native-Chinese review: pending.
- Retrieval eligibility: denied for both doctor and patient retrieval.
- Doctor Resources visibility: allowed as an official-link catalog, with the
  pending-rights state shown in the interface.

This distinction is intentional: authoritative publication is not itself
evidence of commercial AI reuse rights. Catalog visibility must never be
treated as retrieval admission.

## Rights-cleared original English corpus

`catalog/open_patient_education.v1.json` is a separate, checked-in corpus of 55
publisher-authored English documents captured on 2026-07-15:

- 25 MedlinePlus health-topic summaries;
- 10 MedlinePlus medical-test explanations;
- 10 National Cancer Institute patient-education documents;
- 5 National Institute of Mental Health fact sheets; and
- 5 MyHealthfinder/ODPHP preventive-health pages.

The corpus contains original publisher text and page metadata only. It does not
contain generated article summaries, Chinese translations, images, logos, or
linked third-party works. Each record preserves its canonical source URL,
publisher date wording, capture date, content checksums, rights-policy locator,
rights-evidence checksum, licence basis, and attribution requirements.

The four publishers' selected text classes are recorded as U.S. Government
public-domain content. This is page- and content-class scoped: MedlinePlus
A.D.A.M./ASHP/licensed material and all third-party images or works remain
excluded. The documents are foreign-jurisdiction, authority-tier-B evidence.
国家卫生健康委员会, 国家药监局, 中国疾控中心, and other applicable Chinese
authority guidance governs a China-facing answer when sources conflict.

The original English text is visible through the doctor-only resource-detail
API, but every medical, native-Chinese, and patient-readability review remains
pending. Sources and passages are not doctor- or patient-retrieval eligible;
lexical and vector eligibility are false and no embeddings are stored. A
separate DeepSeek translation pipeline can now produce and import review-pending
Simplified-Chinese derived artifacts without creating additional sources.

## Licensed Chinese-native HPA Health Myths corpus

`catalog/hpa_health_myths.zh-Hans.v1.json` contains the complete 697-row
`保健闢謠` open dataset published by Taiwan's 衛生福利部國民健康署. The raw
publisher CSV is preserved under `knowledge_base/raw/` with its SHA-256
checksum. Thirteen repeated-question groups are retained as later immutable
versions, producing 684 stable sources and 697 source versions rather than
silently dropping revisions.

The dataset explicitly uses `政府資料開放授權條款-第1版
(OGDL-Taiwan-1.0)`. The rights record permits storage, commercial use,
transformation, Simplified-Chinese adaptation, excerpt display,
redistribution, prior-version retention, embedding, and bounded model-provider
transmission with attribution. Logos, trademarks, separately marked
third-party works, images, videos, and external attachments remain excluded.

Every original `zh-Hant` question and answer has a deterministic OpenCC `t2s`
`zh-Hans` adaptation with checksum-linked lineage. The conversion does not
claim to be an official publisher translation. Product-owner confirmation on
2026-07-17 records that all 697 Simplified-Chinese artifacts completed medical,
native-Simplified-Chinese, Mainland-applicability, and patient-readability
review. Reviewer identities were not supplied and are therefore recorded as
unspecified rather than invented. Approved versions are lexical/vector
eligible and may enter the immutable patient release; Taiwan-specific policy,
program, contact, approval, and legal details retain their jurisdiction label.
The doctor Resources catalog exposes all 697 dated records, including the 13
preserved historical revisions, and its reader displays each deterministic
Simplified-Chinese question and answer with HPA/Taiwan provenance and an
explicit human-reviewed notice.

Rebuild from the preserved official CSV and captured rights evidence:

```bash
uv run python -m scripts.build_hpa_health_myths_corpus \
  --source-csv knowledge_base/raw/hpa_health_myths.zh-Hant.dataset-43338.2026-07-02.csv \
  --dataset-html /tmp/hpa_dataset_43338.html \
  --rights-html /tmp/ogdl_taiwan_1_0.html
```

Import idempotently after applying migrations:

```bash
uv run python -m scripts.import_hpa_health_myths
```

Promote the confirmed reviews and activate an immutable combined patient
release idempotently:

```bash
uv run python -m scripts.activate_hpa_health_myths_release \
  --confirm-all-697-human-reviewed
```

## National Health Commission family

The catalog includes 52 Chinese-only, authority-tier-A 国家卫生健康委员会
resources. They cover current primary-care and emergency guidance plus distinct
official PDF attachments from the Commission's tumor/hematology and oral-disease
guideline collections. They use a separate publisher and rights record and are
not represented as WHO translations. Commercial storage/AI-use rights and
medical review remain pending.

- <https://www.nhc.gov.cn/cms-search/downFiles/5683726a96d341dba9aa8090ed2f0734.pdf>
- <https://www.nhc.gov.cn/yzygj/c100068/202404/b12cab9adae7424493cd2d387f018367.shtml>
- <https://www.nhc.gov.cn/cms-search/xxgk/searchList.htm>

## Rebuild and import

Download the official index to a temporary file, then rebuild deterministically:

```bash
uv run python scripts/build_authoritative_catalog.py \
  --index-html /tmp/who_fact_sheets.html \
  --english-index-html /tmp/who_fact_sheets_en.html \
  --rights-html /tmp/who_copyright.html \
  --nhc-manifest knowledge_base/catalog/nhc_resources.v1.json \
  --catalog-output knowledge_base/catalog/authoritative_resources.v1.json \
  --dart-output ../../apps/dr_ai_app/lib/features/doctor/domain/medical_resource_fixture.dart \
  --generated-at 2026-07-14T00:00:00Z
```

After applying migrations, import the validated catalog idempotently:

```bash
uv run python -m scripts.import_knowledge_catalog
```

Build and import the separate open-content corpus:

```bash
uv run python scripts/build_open_patient_education_corpus.py
uv run python -m scripts.import_open_patient_education
```

## Governed Chinese translation workflow

The checked-in translation tooling targets exactly the 55 open-content
documents and their 426 source sections. It validates the rights record before
generation/import, preserves source-version and section checksums, resumes from
an append-only JSONL work file, uses provider-reported token usage, and refuses
to finalize until every source document is present exactly once.

Keep the API key only in the server environment (for example the gitignored
`services/api/.env` as `DR_AI_DEEPSEEK_API_KEY`); never paste it into source,
artifacts, logs, or Flutter. Inspect the no-cost plan first, then run a one-item
smoke test with a cost ceiling before the complete batch:

```bash
uv run python -m scripts.translate_open_patient_education dry-run
uv run python -m scripts.translate_open_patient_education run --limit 1 --max-cost-usd 0.10
uv run python -m scripts.translate_open_patient_education run --max-cost-usd 1.00
uv run python -m scripts.translate_open_patient_education finalize
uv run python -m scripts.import_open_patient_education_translations
```

Import is idempotent and records every artifact as
`generated_pending_review`. It asserts that the `kb_sources` count does not
change. Record the medical and native-Chinese decisions separately for each
artifact ID:

```bash
uv run python -m scripts.review_open_patient_education_translation \
  ARTIFACT_ID --review-type medical --reviewer-id REVIEWER_USER_ID \
  --decision approved
uv run python -m scripts.review_open_patient_education_translation \
  ARTIFACT_ID --review-type native_chinese --reviewer-id REVIEWER_USER_ID \
  --decision approved
```

When the complete 55-document corpus has been reviewed by both roles, use the
guarded, idempotent bulk command instead of issuing 110 opaque updates:

```bash
uv run python -m scripts.approve_open_patient_education_translations \
  --medical-reviewer-id MEDICAL_REVIEWER_ID \
  --native-chinese-reviewer-id NATIVE_CHINESE_REVIEWER_ID \
  --confirm-all-55-reviewed
```

Only after both approvals does the existing entry become English + `zh-Hans`
in Doctor Resources and expose the reviewed, explicitly unofficial Chinese
translation. Translation import alone never enables display, embeddings,
lexical/vector retrieval, an index release, or patient use.

### Current translation state (2026-07-15)

The complete DeepSeek v4 Flash batch has been generated, validated, finalized,
and imported: 55 unique documents, 426 aligned sections, 107,006 input tokens,
and 94,090 output tokens. Provider-reported usage produced an estimated batch
cost of `$0.0413`. The database remains at 353 sources and contains 55
translation artifacts. Product-owner-confirmed medical and native-Chinese
review completion has been recorded as 110 separate approved review rows; the
55 artifacts are now `approved` and the existing entries advertise English and
`zh-Hans` in Doctor Resources. Named reviewer identities were not supplied in
the confirmation, so the audit rows preserve that fact through
provenance-scoped reviewer identifiers and findings rather than inventing
names. The translations remain explicitly unofficial. On 2026-07-16, the
product owner separately confirmed all 55 entries and documents as manually
reviewed and patient-use approved. The guarded promotion command materialized
55 checksum-linked Chinese patient versions, 426 retrieval-eligible passages,
and 165 version-level medical, native-language, and patient-readability review
rows. It then built and activated immutable local patient release
`KBIR-8293AC8D815B9715D1B44F42` without changing the 353-source registry.
The sources remain U.S.-jurisdiction authority-tier-B evidence and must not be
presented as Chinese guidance. The eight sections below the ordinary Chinese-character
threshold are publisher reference lists whose Chinese heading is `参考文献`;
their bibliographic citations and URLs were intentionally preserved rather
than translated.

Re-running promotion and activation is idempotent:

```bash
uv run python -m scripts.activate_open_patient_education_release \
  --reviewer-id product-owner-confirmed-unspecified \
  --confirm-all-55-patient-approved
```

The content-addressed release manifest is stored under
`knowledge_base/release_artifacts/`. Reviewer names were not supplied, so the
audit findings preserve that limitation explicitly rather than fabricating
identities. This is a local deterministic retrieval baseline; it does not
waive the production clinical, safety, retrieval-evaluation, privacy/legal,
provider, monitoring, rollback, and deployment gates.

## Governed bilingual summary workflow

The 55-source open patient-education corpus has a separate DeepSeek summary
workflow. It reads the governed English originals and their aligned reviewed
Simplified-Chinese translations, then produces one concise English summary and
one concise Chinese summary for each stable source. Generation is append-only,
resumable, checksum-bound to both inputs, and records provider-reported token
usage.

From `services/api`, inspect the batch without calling DeepSeek:

```bash
uv run python -m scripts.summarize_open_patient_education dry-run --max-cost-usd 0.25
```

Run the paid batch only after reviewing the dry-run output:

```bash
uv run python -m scripts.summarize_open_patient_education run --max-cost-usd 0.25
```

The completed artifact is written under `knowledge_base/summaries/` with status
`generated_pending_review`. Generation alone does not alter the database,
catalog search, retrieval releases, or patient eligibility.

### Current bilingual summary state (2026-07-15)

All 55 English and Simplified-Chinese summary pairs were generated with
DeepSeek v4 Flash (192,598 input tokens; 10,802 output tokens), manually
reviewed, and imported as 55 approved `kb_summary_artifacts` with 55 review
records. The source registry remains 353 rows. Approved summary text now
participates in Doctor Resources catalog matching in both languages, alongside
titles, official translations, topics, metadata summaries, and bilingual
keywords. The import is idempotent and checksum-bound to the immutable source
version and approved translation artifact. Reviewer names were not supplied,
so the recorded reviewer identifier and findings preserve product-owner
confirmation without inventing individual identities.

Summary approval affects catalog search only. It does not enable passage
retrieval, create an index release, or change doctor/patient eligibility.

The generator prioritizes common primary-care topics, then preserves every WHO
index entry and appends the reviewed NHC manifest. Every source has a stable ID
and metadata checksum. Discovery inputs also have recorded SHA-256 checksums.

## Promotion boundary

To promote any source beyond link-only metadata, record a source- or
publisher-scoped approved rights decision, immutable raw and normalized
artifacts, medical/native-language reviews, and an approved source version.
Only then may a deterministic index release include it. Activation changes the
active release pointer; rollback restores its predecessor without mutating
evidence history.

## Slice 6 governed online-source freshness

`source_families/china_authorities.v1.json` is the initial China-first connector
manifest. It registers only the 国家卫生健康委员会 normative-document channel
and 中国疾控中心 health-education channel. Both are metadata-only and
rights-pending: the worker may hash responses and record quarantined change
candidates, but it may not store full text, build passages, or alter an active
retrieval release.

Apply migration `20260716_0028`, then synchronize the manifest:

```bash
uv run python -m scripts.manage_online_sources sync
uv run python -m scripts.manage_online_sources status
```

The scheduler/worker entry point polls only due, active families. It disables
redirect following, enforces exact HTTPS domain/path allowlists and byte/type
limits, scans visible text for malformed structure and prompt-injection
patterns, detects checksum changes, follows only a bounded number of
same-family links, and writes every changed candidate to the review queue:

```bash
uv run python -m scripts.manage_online_sources poll \
  --max-discovered-fetches 8
```

After a diagnosed transient network/tooling failure, an operator may bypass
the due-time check once with `poll --force`; failed runs otherwise use a
15-minute retry backoff rather than waiting for the full source schedule.

Operational source-family incidents can remove assigned evidence from
answer-time retrieval immediately without mutating the immutable release:

```bash
uv run python -m scripts.manage_online_sources kill KBF-NHC-NORMATIVE \
  --actor-id SAFETY_OPERATOR_ID --reason-code SOURCE_FAMILY_INCIDENT
uv run python -m scripts.manage_online_sources restore KBF-NHC-NORMATIVE \
  --actor-id SAFETY_OPERATOR_ID --reason-code INCIDENT_CLEARED
```

WHO, NMPA, literature discovery, full-text capture, and patient activation are
not configured by this manifest. Each requires a separate source-family,
rights, medical/language/jurisdiction/readability, retrieval-evaluation, and
explicit activation decision.

## Canonical symptom-gap source intake

`evaluation/canonical_rural_symptom_source_candidates.v1.json` is a separate,
evaluation-only intake queue for the candidate 100-question symptom contract. It
contains links and review metadata, not article bodies or retrieval passages.
After presentation centrality was applied to literal as well as generated
views, the active v8 audit reports 33 canonical and 25 variant presentations as
`no_eligible_evidence`. Schema `1.1.0` now maps at least one official Mainland
research lead to all 33 canonical and all 25 variant gaps. These link-only
mappings complete research discovery for the current audit snapshot; they do
not change any audit decision or establish corpus coverage.

Run the checksum-bound, no-network, no-provider structural gate from
`services/api`:

```bash
uv run python -m scripts.validate_canonical_source_candidates
```

The validator requires the queue and coverage artifact to match the canonical
contract checksum; validates declared authority domains, unique source IDs and
locators, canonical/variant mappings, review-pending states, and strict
evaluation/retrieval/training separation; rejects raw text or an invented
approval; and now fails closed while any observed gap lacks a research lead.
The latest corresponding local evidence artifact is
`release_artifacts/evaluation/canonical-source-intake-v5-complete-research-leads-local-20260721.json`;
it passes the structural research-lead gate with 31 link-only candidates,
33/33 canonical mappings, 25/25 variant mappings, zero provider calls, and no
eligible-evidence or clinical-approval claim. Earlier failing artifacts remain
historical evidence for their preceding coverage snapshots.

Every candidate remains `link_only_pending`. Before any source can enter a
retrieval corpus, obtain source- and content-class-specific rights for storage,
transformation, commercial use, embeddings, excerpt display, and bounded model
transmission; capture it through an allowlisted governed source family; perform
named clinical, native-Simplified-Chinese, jurisdiction, and readability review
at section level; then build a new immutable candidate release and rerun
retrieval and complete-answer gates. Public availability or government
publication does not satisfy these requirements.

A live 2026-07-21 audit of the five research leads for the retrieval-eligible
symptom-only gaps confirmed that the official pages remain available. The NHC
pages display an explicit copyright notice, while no reusable-content licence
was recorded for the Beijing or Yantai pages. Therefore orthostatic presyncope,
positional vertigo, pesticide-related dermatitis, palpitation/chest-tightness,
and reduced-fetal-movement content remains link-only; no body text was copied
into the corpus and permission/review is still required.

### Canonical review packet

`evaluation/canonical_rural_symptom_review_packet.v1.json` is the generated,
evaluation-only review overlay for the exact contract, v8 coverage audit, and
source-candidate queue. It contains all 100 canonical cases, all 85 variants,
the active release's retrieval candidate source IDs, and all 31 link-only
research leads. It contains no captured article body or retrieval passage.

Regenerate it only from the bound inputs, then validate the reviewer-edited
copy:

```bash
uv run python -m scripts.build_canonical_review_packet --generated-on 2026-07-21
uv run python -m scripts.validate_canonical_review_packet \
  --output canonical-review-readiness-v1-pending-local-20260721.json
```

The pending validator exit is intentionally non-zero. Its current artifact is
structurally valid but records 949 explicit readiness failures: four unnamed
reviewer roles, 822 per-subject annotation decisions, 34 active-source label
selections, 58 research-lead selections, and 31 source dispositions. A source
cannot be approved by checkbox alone: the gate requires source-specific rights
provenance and capabilities, selected section locators, all clinical/language/
readability/product decisions, and bidirectional source-to-case scope. Any
correction requires contract regeneration and a new checksum. Even a completed
packet does not create eligible evidence or authorize capture, provider
transmission, indexing, or activation.

### Canonical retrieval-only gate

`evaluation/canonical_rural_symptom_retrieval_gate.v1.json` defines the
checksum- and active-release-bound retrieval-only gate separately from safety,
rescue, and complete-answer evaluation. Generate the production-path coverage
trace, then score it from `services/api`:

```bash
uv run python -m scripts.audit_canonical_symptom_coverage \
  --output knowledge_base/release_artifacts/evaluation/canonical-rural-symptom-coverage-KBIR-D3DFA94CC95660019B6EF94E-v9-gate-metrics-local-20260721.json
uv run python -m scripts.evaluate_canonical_retrieval \
  --coverage knowledge_base/release_artifacts/evaluation/canonical-rural-symptom-coverage-KBIR-D3DFA94CC95660019B6EF94E-v9-gate-metrics-local-20260721.json \
  --output knowledge_base/release_artifacts/evaluation/canonical-rural-symptom-retrieval-gate-v1-pending-local-20260721.json
```

Use `--require-pass` only for a release gate. The current report exits normally
for inspection but has `passed=false`: all 92 retrieval-eligible subjects still
lack reviewed source labels, so candidate hits are not converted into recall or
support claims. The policy separately gates symptom-only recall, paired-variant
non-degradation, forbidden-source leakage, pre-safety calls, retrieval errors,
latency, provider calls, and cost. The evaluation files are never retrieval
corpus or training data.

### Canonical complete-answer matrix gate

`scripts.evaluate_canonical_answers` keeps safety, retrieval-only, rescue, and
complete-answer metrics separate. Its v3 scorer accepts only two explicit
scopes: the exact five-route `initial_batch`, or `full_contract` containing all
100 canonical and 85 variant inputs. Every variant uses its own route, call
permissions, relevant sources, and forbidden sources. A passing initial batch
can set `ready_for_full_contract_run=true`, but only the complete matrix can set
`machine_gate_passed=true`; independent human review is still required for the
overall gate.

The zero-cost pre-model production-path lane can be run independently before
source-label readiness:

```bash
uv run python -m scripts.evaluate_canonical_answers premodel \
  --output knowledge_base/release_artifacts/evaluation/<new-premodel-artifact>.json
```

It executes the real patient-chat entry point for the exact 93 emergency and
medication-change canonical/variant subjects. Multi-turn setup is inserted as
evaluation-only prior user context without invoking retrieval or a model; the
final turn fails immediately if retrieval, the query planner, or the answer
model is called. It accepts only the explicit synthetic demo identity in a
non-production `synthetic_only` environment, runs inside an outer rollback-only
transaction, refuses to overwrite evidence, and stores no question or answer
text in the artifact. The v2 local artifact passes all 93 subjects: 82
emergency and 11 medication-change refusals, with zero downstream calls/tokens/
cost, 100% route/action behavior, 100% emergency recall and zero-call behavior,
100% medication-gate behavior, 11 ms p95 and 29 ms maximum latency. Database
verification found zero persisted evaluation threads or events. This closes
only the candidate pre-model machine lane; it is not clinical approval and does
not close generated answers or the exact 185-input gate.

The complementary no-provider production-path lane covers the other 92 inputs:

```bash
uv run python -m scripts.evaluate_canonical_answers safe-fallback \
  --output knowledge_base/release_artifacts/evaluation/<new-safe-fallback-artifact>.json
```

It performs real active-release retrieval for the exact 53 canonical and 39
variant subjects that pass deterministic safety, while replacing planner and
answer adapters with local service-unavailable probes that cannot make an
external request. The v2 artifact passes 92/92 route/action, call-boundary,
fixed-fallback, and zero-usage checks: 92 retrievals produced 34 candidate
`sufficient` and 58 `no_eligible_evidence` decisions, 59 planner-adapter and 34
answer-adapter invocations made zero provider requests, and p95/maximum endpoint
latency was 900/975 ms. All endpoint writes were rolled back and direct checks
found zero retained evaluation threads or events. The artifact stores no query
or answer text and explicitly claims neither retrieval quality nor complete
answers. It proves safe degradation only; candidate retrieval hits remain
unreviewed and unsupported gaps remain unsupported.

Rescue ambiguity is presentation-aware. A short phrase such as `要紧吗` or
`怎么办` does not by itself make a self-contained symptom/exposure query
ambiguous. Only a query without a controlled clinical topic may take the
context-dependent ambiguity path that discards unverified initial evidence
when planning fails. The v4 no-cost Slice 9B preflight preserves the three
frozen context-dependent triggers and all three ordinary controls at 6/6, with
zero model calls or cost.

The current no-cost preflight is
`release_artifacts/evaluation/canonical-complete-answer-preflight-v4-matrix-integrity-local-20260721.json`.
It records zero structural failures and 190 readiness failures because the
contract/reviews are not frozen and all 92 model-eligible canonical/variant
subjects lack approved source labels and coverage. It planned one case from
each route, estimated `$0.013496` under the `$0.10` cap, and made zero provider
calls. Do not run or pay for that batch while `ready_for_initial_paid_batch` is
false.

## Supplementary symptom-presentation intake

`catalog/open_symptom_presentations.v1.json` is a separate six-source
retrieval-corpus candidate built from five publisher-authored MedlinePlus
health-topic summaries and the NHS page `Your baby's movements`. It contains no
evaluation queries or training examples. The catalog records the MedlinePlus
public-domain evidence and independently checksum-binds the NHS terms and
content-exclusion page. NHS OGL v3 permits commercial copying and adaptation,
but translated or non-refreshed text must use the adaptation attribution, must
not be presented as NHS-authored, must not imply endorsement, and cannot inherit
the original page's formal clinical approval. All source-rights decisions still
require named review before candidate admission.

The open-content and translation schemas now accept a checksum-bound dynamic
document count only in schema `1.1`; the frozen 55-source corpus remains schema
`1.0` and retains its exact-count invariant. Import scripts accept an explicit
artifact path, preserve that path in source-version lineage, and leave every
new source, passage, and generated translation retrieval-ineligible.

The six Simplified-Chinese candidates in
`translations/open_symptom_presentations.zh-Hans.deepseek-v4-flash.v1.json`
were generated sequentially with DeepSeek `deepseek-v4-flash`, thinking
disabled, and a `$0.05` run ceiling. Provider-reported usage is 3,202 input,
2,217 output, and 5,419 total tokens; configured-price cumulative cost is
approximately `$0.0011`. The NHS addition used one bounded call after its local
structural preflight. There were no provider failures. Generation is not
approval.

The file-backed gate is
`reviews/open_symptom_presentations.v1.json`. It binds the exact catalog and
translation checksums, keeps retrieval/evaluation/training separation explicit,
and requires named rights, medical, native-Simplified-Chinese,
patient-readability, Mainland-applicability, and product decisions as
applicable. It records six open blockers: the original four plus England-
specific maternity-pathway localization and OGL adaptation/attribution for the
NHS translation.

Run the structural check separately from admission readiness:

```bash
uv run python -m scripts.validate_open_symptom_review --structure-only
uv run python -m scripts.validate_open_symptom_review
```

The first command currently passes. The second intentionally returns nonzero:
60 named human reviews and six blocking findings remain open. The imported
database state is six sources, eleven original passages, and six translations,
all pending, with zero patient/doctor eligibility and zero lexical/vector
eligibility. No immutable
candidate was built or activated, and the active-release coverage, Slice 9A
retrieval gate, complete-answer preflight, and Slice 9B results therefore have
not changed.

## Slice 4 retrieval baseline

Catalog-visible metadata now carries a `catalog_summary` and
`search_keywords` for all 298 entries. These fields improve link-catalog search
but do not claim to summarize article bodies: every generated summary states
that the body is not stored or summarized. Common aliases such as `血压高` /
`high blood pressure` are searchable alongside titles, official translations,
topics, and source metadata.

Passage retrieval is a separate fail-closed path. It reads only passages listed
in the active immutable release for the requested audience and rechecks rights,
review, lifecycle, current-version, language, jurisdiction, and audience gates.
The implementation combines lexical and version-matched dense scores, reviewed
terminology expansion, policy reranking, deduplication, source diversity, and
evidence sufficiency/conflict checks. It records hashes, IDs, scores, decisions,
and latency, never the raw query or passage text.

The local deterministic embedding and policy-reranking models exist for
development, reproducible tests, and explicit degradation fallback only.
Slice 9A retains self-hosted BGE-M3 embeddings and BGE Reranker v2 M3 as the
production profile. The pinned GTE multilingual base pair in
`../../retrieval_inference` is a locally validated 4-vCPU/8-GB staging
candidate, not an activated release. The current Slice 9A suite is
`evaluation/retrieval_cases.slice9a.v2.json`; it preserves every clinician-
reviewed v1 case and label while replacing the pre-measurement 1,200 ms p95
planning target with a measured 2,500 ms end-to-end p95 gate plus an 8,000 ms
hard per-case ceiling. The original v1 suite remains immutable. Hong Kong is
acceptable for current development/staging and avoids introducing a second
operational region while the API and PostgreSQL remain there. A later Mainland
deployment decision must be based on measured network performance and
documented residency/privacy/legal controls. Every stored vector carries its
exact model version, and a release refuses mismatched vectors. Patient release
build and pre-provider transmission independently re-read source-matched,
effective, unexpired transmission rights. The real catalog cannot be promoted
until rights and clinician-review records are approved; pending sources never
enter either retrieval view.

Slice 9B evaluates adaptive retrieval separately from answer generation. Its
frozen candidate hard-query and ordinary-control suite is
`evaluation/retrieval_rescue_cases.slice9b.v2.json`. V2 preserves the reviewed
queries and source labels but reclassifies the v1 colloquial case as a non-
degradation control because the first live run proved its baseline already
retrieved every labelled source. Validate its structure and run the no-cost
trigger/feasibility preflight using:

```bash
uv run python -m scripts.evaluate_slice9b_retrieval_rescue validate
uv run python -m scripts.evaluate_slice9b_retrieval_rescue preflight
uv run python -m scripts.evaluate_slice9b_retrieval_rescue preflight \
  --output knowledge_base/release_artifacts/evaluation/<new-preflight-artifact>.json
```

The suite records product-owner approval by Harry Cao and clinical/native
Simplified Chinese approval by Hou Jin, Doctor at Beijing Hospital, dated
2026-07-18, with no corrections required. The live runner compares original
retrieval with bounded rescue for relevant-source improvement, ordinary-query
non-degradation, exact trigger behavior, at least one real planner attempt,
total rescue latency, and configured-price cost. It records the suite checksum
and release ID, refuses to overwrite evidence, rolls back its retrieval-event
writes, and does not use answer-evaluation cases. Runner v4 also routes every
case through deterministic continuity and safety before baseline retrieval,
sends the planner only an admitted previous user turn, validates rewrites
against the safety-approved controlled presentation, and lets a rewrite replace
only the retry's literal query. Generated views and centrality therefore remain
controlled rather than model-authored. Its ambiguity trigger additionally
requires the absence of a standalone controlled clinical topic, so colloquial
question endings cannot erase sufficient governed evidence. A v4 structural
preflight can be written
as immutable zero-call evidence and records the call/token/cost counts
explicitly. The failed v1 result remains
preserved under `release_artifacts/evaluation/slice9b-rescue.json`.
The failed v2 artifact is also preserved. Do not spend another paid rescue run
against the local hashed/policy fallback. First deploy the semantic model pair,
rebuild a new immutable release with exact 768-dimensional embedding lineage,
and pass Slice 9A; only then rerun the frozen Slice 9B gate.
