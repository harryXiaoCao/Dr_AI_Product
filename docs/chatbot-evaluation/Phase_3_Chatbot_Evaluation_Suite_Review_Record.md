# Phase 3 Chatbot Evaluation Suite Review Record

Status: candidate suite populated; native-Chinese and clinical review blocked<br>
Date: 2026-07-12<br>
Owner: Harry Cao

## Frozen Candidate Composition

The deterministic candidate suite contains exactly 1,500 stable IDs:

| Component | Cases | Source |
|---|---:|---|
| Private rural-China authored candidates | 450 | 100 research-grounded synthetic scenario families; no real patient data |
| Chinese consumer health | 200 | CHBench |
| CMB medical knowledge | 200 | CMB validation split |
| Additional Chinese medical exam | 150 | OpenAI MMMLU `ZH_CN` medical subjects |
| Medical safety/adversarial | 200 | HealthBench safety-keyword/rubric stratum |
| HealthBench open-ended | 150 | HealthBench, excluding the safety stratum |
| Chinese robustness | 150 | Naturally short or underspecified CHBench queries |

The 1,050 public cases comprise 700 Simplified-Chinese and 350 English cases.
No public case was translated, re-authored, or synthetically generated. The 450
private rows now contain authored candidate inputs across 100 rural-China
scenario families: 50 families have five variants and 50 have four. They are
evaluation inputs, not clinical ground truth, and remain sealed from training,
retrieval, and model-vendor reuse.

## Rural-China Background Research And Scenario Construction

The private set was constructed from official national and provincial sources
with a research cutoff of 2026-07-12. The evidence supports these scenario
design assumptions:

- village clinics and township health centers provide basic public-health work,
  common-disease care, follow-up, rehabilitation, and referral; county hospitals
  receive cases beyond primary-care capability;
- routine rural workflows prominently include resident records, health
  education, vaccination, maternal and child health, older-adult care,
  hypertension, type 2 diabetes, serious mental illness, tuberculosis, and
  communicable-disease reporting;
- village-clinic information systems and network access remain an explicit
  infrastructure concern, so low bandwidth and interrupted sessions are real
  product conditions;
- Yunnan evidence supports uneven village-doctor qualification levels and a
  continuing border-province infectious-disease focus;
- Sichuan planning identifies population ageing, rural elder-care gaps,
  constrained primary-care capacity, major infectious diseases, and chronic
  noncommunicable disease as material pressures; and
- Guizhou reports large-scale village-clinic renovation, county medical
  communities spanning township and village facilities, workforce training,
  and a chronic-disease burden led by cardiovascular disease, cancer, diabetes,
  and chronic respiratory disease.

Primary evidence is preserved per case through `research_basis_ids` and exact
official URLs. The scenario families cover chronic disease, older-adult care,
maternal and child health, communicable disease, injuries and environmental
exposure, mental health, medication-boundary pressure, doctor-record
clarification, privacy, access, dialect/low-literacy limitations, and
network/provider failure. Regional context changes the access condition and
workflow; it is not used to claim that a disease is unique to one province.

## Private Scenario-Family Ground-Truth Rubrics

The 100 private scenario families now have source-backed candidate rubrics in
`evaluation/chatbot/private_scenario_rubrics.jsonl`, supported by the evidence
hierarchy and 41-source registry in
`evaluation/chatbot/private_rubric_sources.json`. Each rubric contains atomic
required criteria, prohibited criteria, a required next action, evidence IDs,
reviewer roles, review status, and shared overlays for direct user, caregiver,
low-literacy, limited-access, and unstable-network variants. All 450 private
rows link to exactly one family rubric and one variant overlay.

The rubrics deliberately do not provide one model answer. Multiple answers may
be acceptable when they satisfy the same source-backed facts and safety rules.
Thirty high-risk families currently contain at least one explicit hard-failure
criterion. This is a candidate evidence layer, not a clinical sign-off: medical
criteria remain pending the specified qualified reviewer and, for emergency,
urgent, medication, and medical-education families, a second reviewer.

## Rights And Provenance Review

Admitted source snapshots are pinned to immutable repository revisions:

- CMB: Apache-2.0.
- CHBench: MIT.
- OpenAI MMMLU: MIT.
- OpenAI HealthBench: MIT.

CMExam, MedQA Chinese, cMedQA, MedSafetyBench, and non-commercial CMMLU were
excluded. The manifest records the reason for each exclusion. Repository-level
availability was never treated as permission.

CHBench source responses are retained only as
`source_reference_response_unverified`; they are not encoded as required facts
or medical ground truth. CMB/MMMLU answer keys and HealthBench rubrics retain
their original provenance and still require Dr. AI boundary review.

## Automated Review Result

`evaluation/chatbot/review_report.json` passes with the clinical-review gate:

- exact component counts passed;
- 1,500 unique stable IDs passed;
- 1,050 unique public source rows passed;
- zero exact normalized public-message duplicates passed;
- all 24 required schema fields are present;
- Chinese-first language composition passed; and
- all 450 private entries are populated and exactly match the private segment
  of `suite.jsonl`;
- the private set has exactly 100 scenario families, split into 50 five-variant
  and 50 four-variant families; and
- private messages and all 1,500 suite IDs are unique.
- all 100 rubric IDs and evidence-source references resolve;
- every family contains required and prohibited criteria; and
- all 450 private rows resolve to their family rubric and condition overlay.

Artifact SHA-256 hashes and byte sizes are frozen in
`evaluation/chatbot/manifest.json`.

## Release Gates And Owner Actions

This selection freeze prevents silent row changes; it is not a clinical
approval. Before benchmarking can support a production-model decision:

1. The reviewer role named in each private family rubric must review its
   criteria and sources; emergency, urgent, medication, and medical-education
   families require a second reviewer. Reviewers must resolve disagreements and
   sign/date the rubric before it can be used as approved ground truth.
2. A qualified medical reviewer and native-Chinese reviewer review every public
   case retained for Dr. AI, verify emergency/severity labels and required
   facts, reject out-of-boundary cases, and sign/date the review fields.
3. Reviewers must pay particular attention to emergency pre-routing, urgent but
   non-emergency separation, medication questions, maternal/child cases,
   poisoning, self-harm, and whether colloquial wording is natural for the
   intended users without stereotyping them.
4. Replacement public cases, if any, must come from the same approved component and a
   rights-cleared source, then the builder, duplicate checks, manifest hashes,
   and review must be rerun.
4. An authorized legal/rights reviewer should confirm the recorded licenses
   cover the intended commercial evaluation use before production release.

Until these gates close, the suite must remain marked
`pass_with_clinical_review_gate` and must not be described as clinically
validated or production-ready.
