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
names. The translations remain explicitly unofficial and zero passages are
retrieval-eligible. The eight sections below the ordinary Chinese-character
threshold are publisher reference lists whose Chinese heading is `参考文献`;
their bibliographic citations and URLs were intentionally preserved rather
than translated.

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

The local deterministic embedding model exists for development and reproducible
tests. Production must configure the approved self-hosted multilingual medical
embedding service and build a new release with that exact model version. The
real catalog cannot be promoted until rights and clinician-review records are
approved; pending sources never enter either retrieval view.
