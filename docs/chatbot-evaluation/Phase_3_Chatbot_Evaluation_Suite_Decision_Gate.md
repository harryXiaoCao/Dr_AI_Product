# Phase 3 Chatbot Evaluation Suite Decision Gate

Status: both adjustments approved; evaluation assembly authorized<br>
Date: 2026-07-12<br>
Owner: Harry Cao<br>
Applies to: Step 3 of `Phase_3_Chatbot_Evaluation_and_Model_Strategy.md`

## Purpose

This note records the decisions governing assembly of the frozen evaluation
suite. It does not authorize use of any unresolved dataset.

## Approval Record

On 2026-07-12, the owner approved both adjustments below: existing,
rights-cleared public cases may replace newly authored/localized cases, and
same-category dataset substitutions may be made when a recommended source does
not pass the rights gate. The approved categories, counts, schema, safety
boundary, and deny-by-default dataset admission rule remain unchanged.

## Proposed Fixed Size

Use a `1,500`-case suite with exactly `450` sealed placeholders for the owner's
private Dr. AI rural-China scenarios and `1,050` cases selected from existing
public datasets. This stays within every approved component range:

| Component | Proposed count |
|---|---:|
| Private Dr. AI rural-China scenarios (placeholders only) | 450 |
| Rights-cleared Chinese consumer-health cases | 200 |
| CMB/CMB-Clin medical-knowledge sample | 200 |
| Additional rights-cleared Chinese exam sample | 150 |
| Medical safety and medication-adversarial cases | 200 |
| HealthBench-style open-ended cases | 150 |
| Chinese ambiguity, typo, colloquial, code-switching, and low-literacy robustness | 150 |
| **Total** | **1,500** |

The 450 private rows would contain IDs and required schema metadata only; no
scenario text would be generated or inferred.

## Adjustments Requiring Approval

### 1. Existing-public-only constraint versus the approved source plan

The strategy recommends clinician-led Chinese HealthBench-style cases and
re-authored Chinese adaptations of medical-safety patterns. Those are newly
authored cases, while the current instruction requires all 1,050 non-private
cases to come from existing public datasets.

**Proposed adjustment:** preserve the category counts and schema, but permit
rights-cleared existing public cases to fill these two components without
translation or re-authoring. Their provenance fields would identify the
original language and dataset, and Chinese-first would be enforced across the
suite as a whole rather than inside every component.

Approved by the owner on 2026-07-12.

### 2. Recommended datasets whose data rights are unresolved or restrictive

The strategy itself marks CHBench and MedQA Chinese as unresolved, CMExam and
cMedQA as restricted, and MedSafetyBench as research-only. These sources
cannot satisfy a rigid commercial-use admission rule without rights-holder
clarification. A repository-level code license does not override a dataset
README restriction or establish rights in underlying content.

**Proposed adjustment:** allow a substitution inside the same component only
when an existing public dataset has (a) an explicit dataset-level license that
permits the intended evaluation use, (b) traceable provenance, and (c) content
compatible with the frozen safety boundary. No category count or case schema
would change. Every substitution would be listed in the freeze manifest.

Approved by the owner on 2026-07-12.

## Remaining Rights Rule

Approval of substitutions does not approve any particular dataset. Legal
counsel or an authorized rights reviewer should confirm that intended
commercial evaluation use is covered before release; this project record is an
evidence trail, not legal advice.
