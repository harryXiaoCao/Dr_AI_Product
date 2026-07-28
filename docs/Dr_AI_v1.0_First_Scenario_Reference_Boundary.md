# Dr. AI v1.0 First Scenario and Reference Boundary

```yaml
document_status: "Slice A boundary frozen; reference release blocked"
decision_date: "2026-07-25"
candidate_scenario_id: "cn-sh-outpatient-single-region-ct-plain-v1"
candidate_release_status: "blocked"
production_activation: false
runtime_reference_data_created: false
clinical_review_status: "missing"
pricing_domain_review_status: "missing"
rights_review_status: "unresolved"
```

## 1. Decision

The first implementation candidate is a **clinician-ordered, adult outpatient,
single-body-region CT plain-scan service episode at a Shanghai public medical
institution**.

This is the strongest evidence-supported candidate found in the repository and
official-source audit. It matches the implemented Clinical Event, imaging
Clinical Service, evidence-file, care-cost, immutable payer-request, and human
review boundaries without making Dr. AI decide whether a patient clinically
needs a CT.

The candidate is selected for future implementation sequencing, but its
reference release is **blocked and must not be activated**. Three independent
release gates are open:

1. no named clinical reviewer has approved the applicability, alternatives,
   exceptions, and unsafe under-testing cases;
2. the Shanghai source identifies itself as copyrighted, and no permission for
   commercial storage, transformation, redistribution, or model transmission
   was found; and
3. the official Shanghai amounts are maximum public-institution charges, not
   evidence of the actual posted facility price or a clinically appropriate
   low/high expected-care range.

Until all three gates close, application and runtime assets may keep only
link-level provenance metadata. This internal decision record preserves the
minimum factual observations needed to identify the candidate and explain the
blocker; its codes and amounts must not be copied into runtime reference rows,
seed data, prompts, embeddings, generated fixtures, or
patient/doctor/payer output.

## 2. Evidence audit and candidate comparison

### 2.1 Repository evidence

The current implementation supports this service episode more directly than a
disease-wide pathway:

- `ClinicalService` is generic in persistence, while the current writable API
  contract deliberately admits imaging only.
- Imaging evidence files, consultation records, medications, and care-cost
  items are source-linked rather than represented as free-standing financial
  rows.
- Care-cost submission already fails closed on missing allocation and non-CNY
  currency, snapshots submitted lines immutably, and keeps payer resolution
  human-owned.
- Existing tests use synthetic values for “Low-dose CT chest” and other care
  items. Those values are workflow fixtures only and are not price evidence.
- The local NHC catalog contains discovery metadata for clinical guidelines,
  but explicitly marks the material link-only pending legal review. It does not
  provide an approved utilization release for this scenario.

No authoritative scenario, clinical-utilization, facility-price, claims, or
review-label release exists in the repository.

### 2.2 Official-source evidence

The [Shanghai radiology price notice](https://ybj.sh.gov.cn/qtwj/20250429/f5dd5e766bf54230b98f5c19024f3067.html)
states that its attachment defines the charging scope and maximum price
standards for Shanghai public medical institutions, effective 2025-04-30. Its
attachment lists CT plain scan under code `012301020010000`, unit `部位`
(body region), with maximum prices of CNY 189, 177, and 165 for tertiary,
secondary, and primary institutions respectively. It also defines declining
fractions for additional regions.

The [NHSA national radiology guide](https://www.nhsa.gov.cn/art/2024/11/25/art_201_14760.html)
is a national project-normalization reference, not a national price list: it
instructs provinces to map the projects and establish local benchmarks.
The [NHSA 2026 interpretation](https://www.nhsa.gov.cn/art/2026/2/26/art_202_19735.html)
further states that the interpretation is not itself a fund-audit basis and
that institutions charge under local medical-service price policy.

The [Shanghai 2026 mapping notice](https://ybj.sh.gov.cn/gsgg/20260608/d4a98dc2e93d4e4ca69f983b3319b3f7.html)
provides a current mapping reference between the radiology project guide,
legacy project names, and the 2023 national technical specification. It does
not replace the 2025 Shanghai price notice or turn a price ceiling into an
actual facility charge.

### 2.3 Candidate comparison

| Candidate | Evidence and implementation fit | Material gaps | Decision |
|---|---|---|---|
| Adult outpatient single-region CT plain-scan episode, Shanghai public institution | Current official local code, unit, effective date, tiered maximums, and mapping; directly matches the implemented imaging service and care-cost workflow | Rights unresolved; no named clinical or pricing review; ceiling is not actual price or expected range | **Selected, activation blocked** |
| Adult outpatient ultrasound episode, Shanghai public institution | National and local price-project material exists; the current imaging contract could represent it | Its local code/price boundary was not verified to the same depth; clinical applicability, rights, named review, and fixture labels remain absent | Not first |
| Chronic-disease outpatient follow-up | Medication and consultation records exist; NHC discovery metadata includes relevant guidance | No admitted utilization release, medication-price release, or bounded code/quantity matrix; substantial treatment heterogeneity | Not first |
| Low-dose chest CT screening pathway | Existing synthetic UI/test language and lung-cancer-guideline discovery metadata | Eligibility and interval decisions carry under-/over-screening risk; local catalog is not rights-cleared; no named clinical approval | Rejected as the first safety boundary |
| Hip-fracture care episode | NHC guideline discovery metadata exists | Broad inpatient, procedural, rehabilitation, and facility pathway is not represented by the current vertical slice; pricing and rights unresolved | Not first |

The choice is based on evidence and architecture fit, not on the condition name.
Additional scenarios must be admitted through their own releases without a
condition-specific code fork.

## 3. Frozen candidate scenario definition

This section freezes the candidate contract for later Slice B persistence. It
does not authorize a database row or active release.

### 3.1 Scenario and encounter

| Field | Frozen value |
|---|---|
| Scenario family | Diagnostic imaging service episode |
| Encounter type | Clinician-ordered outpatient service |
| Candidate scenario ID | `cn-sh-outpatient-single-region-ct-plain-v1` |
| Jurisdiction | `CN` |
| Region | Shanghai municipality only |
| Facility ownership | Public medical institution only |
| Facility levels | Primary, secondary, or tertiary; one explicit level required |
| Currency | CNY, stored as integer minor units |
| Clinical-service category | `imaging` |
| Service subtype | CT plain scan |
| Quantity and unit | Exactly `1` body region |
| Reference date | Actual service-delivery date, not order, upload, invoice, or submission date |

### 3.2 Population and inclusion

The initial synthetic/de-identified evaluation population is adults aged 18 or
older. This is a conservative product-test boundary, not a clinical claim that
the price code is adult-only.

A case is eligible only when all of the following are present:

- a clinician-created imaging Clinical Service linked to a Clinical Event;
- a recorded CT plain scan that was actually delivered;
- exactly one body region;
- a Shanghai public medical institution with an explicit primary, secondary,
  or tertiary facility level;
- service date on or after the applicable release effective date;
- currency `CNY`;
- the exact admitted service code and unit; and
- a usable, active reference release plus all required reviews.

### 3.3 Exclusions

The candidate does not cover:

- deciding whether CT, imaging, or any other care is clinically indicated;
- pediatric cases;
- emergency-department or inpatient episodes;
- private, military, employer, cross-border, or non-Shanghai facilities;
- enhanced CT, CT angiography, CT perfusion, CBCT, PET/CT, or MRI;
- multiple body regions;
- thin-slice, energy-imaging, artificial-intelligence-assistance, delayed-image,
  contrast-material, film, cloud-image, or other add-on/extension charging;
- proposed, ordered, scheduled, cancelled, or uploaded-only imaging without a
  delivered service;
- coverage eligibility, benefit design, negotiated or confidential rates,
  patient cost sharing, reimbursement entitlement, or payment determination;
- diagnosis, medical necessity, fraud, waste, abuse, quality, or clinician
  ranking; and
- a general statement of what CT “should cost.”

Excluded cases return an explicit unsupported or unavailable state. They do
not silently fall back to another code, facility level, region, price, or
model-generated estimate.

### 3.4 Known reasonable alternatives and variance

The following may be clinically or operationally reasonable, but they are not
interchangeable with the admitted single-region plain-scan candidate:

- no CT because the clinician chose observation, another modality, or no
  imaging;
- enhanced CT, angiography, perfusion, or another modality selected by the
  clinician;
- more than one body region based on the recorded order and delivered service;
- a lower facility-posted charge than the municipal maximum;
- a different facility level or an out-of-region service;
- delayed, cancelled, repeated, or technically incomplete imaging; and
- separately documented materials or services that are not included in the
  admitted base item.

Dr. AI must preserve these as context or route them to unsupported/manual
review. It must not label them as overuse, underuse, fraud, or an unjustified
variance. In particular, a lower charge than an official maximum is not an
adverse variance, and absence of CT is not under-treatment without a
clinician-approved utilization rule.

## 4. Code, price, provenance, and rights boundary

### 4.1 Candidate pricing reference

| Field | Frozen candidate value |
|---|---|
| Source authority | Shanghai Municipal Healthcare Security Administration and Shanghai Municipal Health Commission |
| Source instrument | 沪医保价采发〔2025〕11号 |
| Source locator | `https://ybj.sh.gov.cn/qtwj/20250429/f5dd5e766bf54230b98f5c19024f3067.html` |
| Project code | `012301020010000` |
| Project name | 计算机体层成像（CT）平扫 |
| Unit | 部位 |
| Tertiary maximum | CNY 189 / `18900` minor units |
| Secondary maximum | CNY 177 / `17700` minor units |
| Primary maximum | CNY 165 / `16500` minor units |
| Effective from | 2025-04-30 |
| Effective to | Not stated; must not be inferred |
| Economic meaning | Public-institution maximum charge, not an actual charge, average, negotiated rate, reimbursement amount, or expected-care range |
| Runtime admission | Prohibited while candidate release is blocked |

The code string must remain a string. Currency arithmetic must use integer minor
units. Any future reference row must separately store source, code system,
project code, unit, facility level, economic meaning, effective interval,
retrieval/checksum evidence, review state, and activation state.

### 4.2 Provenance and freshness

For a future release, the source page, attachment, and mapping page must each
have a retrieval timestamp and content checksum. The candidate release must:

- be built from a human-reviewed immutable snapshot;
- record `effective_from` and a nullable `effective_to` without inventing an
  expiry;
- be checked against the official source immediately before review and
  activation;
- have a configurable next-review date no later than 30 calendar days after the
  last successful official-source check;
- become unavailable when that review date passes, the official instrument is
  superseded or withdrawn, the checksum changes without reconciliation, or the
  applicable facility/region/date cannot be proved; and
- require a new version for any code, amount, unit, applicability, economic
  meaning, or source change.

Thirty days is Dr. AI's conservative release-control interval, not a frequency
stated by the source.

### 4.3 Rights and provider-transmission state

The official pages display a publisher copyright notice. The audit found no
explicit license permitting Dr. AI to store and transform the attachment for a
commercial product, redistribute derived reference rows, embed the content, or
transmit it to DeepSeek.

The frozen state is therefore:

```yaml
rights_status: "unresolved"
storage_mode: "link_metadata_only"
runtime_derivation_allowed: false
redistribution_allowed: false
embedding_allowed: false
provider_transmission_allowed: false
legal_review_required: true
```

Public accessibility is not treated as reuse permission. A named legal/rights
decision, its evidence, scope, effective interval, and provider-transmission
decision are required before runtime admission.

## 5. Review and activation gates

No reviewer is named in repository evidence, so no approval is claimed.
Activation requires all of the following named, attributable decisions:

| Review | Minimum decision |
|---|---|
| Clinical imaging reviewer | Approve population, inclusion/exclusion, reasonable alternatives, unsafe under-testing risks, and fixture labels |
| Shanghai pricing/reimbursement reviewer | Confirm current code, unit, facility-tier meaning, maximum-price meaning, effective interval, included/excluded components, and comparison behavior |
| Legal/rights reviewer | Approve or reject storage, transformation, derived data, redistribution, and DeepSeek transmission separately |
| Product safety owner | Approve non-goals, role-visible language, fallback states, and prohibition on clinical/coverage/adverse labels |
| Data/release owner | Verify immutable snapshot, checksums, provenance, freshness, rollback, and activation controls |

Approval in one row does not satisfy another. Named review means a persisted
reviewer identity, role, decision, timestamp, reviewed version/checksum, and
rationale—not a checklist tick in this document.

Activation must additionally prove an applicable actual-price or defensible
range source. The municipal maximum alone may support a “maximum price
reference” fact after rights clearance, but it must not be presented as the
facility's actual price or as low/high expected cost.

## 6. Frozen synthetic/de-identified fixture contract

The suite is frozen at the specification level only. No fixture amounts from
the official attachment are to be copied into executable data until rights and
review gates close.

| Fixture ID | Synthetic case | Expected deterministic label |
|---|---|---|
| `CTA-SH-001` | Adult, delivered one-region CT plain scan, Shanghai tertiary public institution, valid date/code/CNY; release blocked | `reference_release_unavailable`; no variance label |
| `CTA-SH-002` | Same service with facility level missing | `missing_facility_level`; no fallback tier |
| `CTA-SH-003` | Same service at a private Shanghai facility | `unsupported_facility_ownership` |
| `CTA-SH-004` | Same service before `effective_from` | `no_applicable_reference_version` |
| `CTA-SH-005` | Two body regions | `unsupported_quantity`; retain for later multi-region rule review |
| `CTA-SH-006` | Enhanced CT or CT angiography code | `unsupported_service_code`; no mapping to plain scan |
| `CTA-SH-007` | Ordered or uploaded evidence, but service not delivered | `not_a_delivered_cost_item` |
| `CTA-SH-008` | Delivered service with `pending_cost` | `comparison_not_ready`; payer submission remains blocked |
| `CTA-SH-009` | Valid service mixed with a non-CNY line | `mixed_currency`; whole comparison fails closed |
| `CTA-SH-010` | Existing “Low-dose CT chest” synthetic test/UI amount | `fixture_only_not_reference_evidence`; never promote the amount |
| `CTA-SH-011` | Artificial-intelligence-assistance extension plus main plain-scan line | `unsupported_extension`; no automatic duplicate-charge conclusion |
| `CTA-SH-012` | Lower observed charge than a rights-cleared municipal maximum, with no facility actual-price source | `ceiling_only_not_comparable`; never label adverse variance |

For every case, the patient sees only an unavailable/unsupported/manual-review
state and safe next step. The doctor sees the missing applicability or evidence
fields. The payer reviewer sees only submitted immutable facts and may make a
human review decision. An NGO or showcase observer sees aggregate synthetic
workflow evidence only, never patient-level or confidential data.

No `review_recommended`, `within_range`, `above_range`, or `below_range` label
is admitted yet. Those labels require a reviewed expected-care/utilization
release and an actual-price or defensible range source; a maximum ceiling alone
is insufficient.

## 7. Fail-closed behavior

The server—not DeepSeek or the client—must own these outcomes:

- blocked, inactive, stale, changed, or rights-incompatible release:
  `reference_release_unavailable`;
- missing region, facility ownership/level, service date, code, unit, quantity,
  or currency: explicit applicability error;
- unsupported code, unit, quantity, encounter, population, region, or facility:
  explicit unsupported state;
- no delivered service or unresolved cost allocation: comparison not ready;
- mixed currency, invalid range, arithmetic mismatch, or unreconciled totals:
  reject the whole comparison;
- provider failure or malformed output: preserve manual and `pending_cost`
  workflow without AI substitution; and
- uncertainty about actual versus maximum price: do not compare and do not
  generate a variance label.

There is no general-model fallback for reference codes, amounts, clinical
utilization, price meaning, coverage, or variance labels.

## 8. Non-goals and next authorized slice

This freeze does not:

- activate a clinical, pricing, or utilization release;
- claim legal permission, clinical approval, pricing approval, payer approval,
  production readiness, reimbursement accuracy, or live-use authorization;
- create scenario/reference tables, migrations, routes, prompts, model calls,
  Flutter UI, seeded records, or evaluation outputs;
- change existing Clinical Service or care-cost behavior;
- establish DeepSeek as a clinical, price, coverage, or review authority;
- begin deterministic comparison implementation; or
- admit additional scenarios.

Slices B, C, and D were separately authorized and implemented on 2026-07-25 as
provider-neutral release persistence, a deterministic comparison engine, and
a schema-constrained expected-care candidate purpose.
The blocked CT candidate is represented only by an unavailable test fixture:
no source code, amount, attachment content, runtime reference row, seed, or
active release was created. Unrelated synthetic rehabilitation and laboratory
cases prove that the implementation is configuration-driven rather than a
CT-specific branch. A separately named, wholly synthetic rehabilitation
release bundle is now persisted and active only for local integration and
stub-provider candidate testing; an unrelated persisted synthetic laboratory
bundle proves the same candidate contract is configuration-driven. Neither has
Shanghai source lineage or relaxes this candidate's gates. Slice D made no live
provider call and added no Shanghai runtime release.
The selected candidate remains blocked until the named review, rights, and
usable-price/range gates above are evidenced.
