# Phase 3 Chatbot Evaluation and Model Strategy

Status: research-backed strategy record before chatbot implementation<br>
Research cutoff: 2026-07-12<br>
Owner: Harry Cao<br>
Applies to: first Dr. AI Phase 3 patient-chatbot deliverable

## 1. Purpose And Relationship To The Product Boundary

This record consolidates the Phase 3 discussion and research on evaluation
data, candidate models, benchmarking, post-benchmark improvement, architecture,
and deployment. It is the source of truth for deciding **how Dr. AI will
evaluate and select a chatbot model before production development begins**.

The chatbot's permitted uses, prohibited behaviors, rural-China usage model,
patient-context rules, storage boundary, and human-care relationship are
already frozen in
`docs/Phase_3_Chatbot_Intended_Use_and_Safety_Boundary.md`. This record does
not repeat those rules. Every dataset, model, benchmark, and improvement method
described here must comply with that boundary.

The principal decision is:

> Dr. AI will form and freeze a Chinese-first evaluation suite, benchmark
> multiple models through a thin experimental runner, select the best-fit
> production and adaptable candidates from evidence, and only then begin full
> chatbot development.

DeepSeek is a credible candidate, not a predetermined winner. Fine-tuning is a
possible later intervention, not the starting strategy.

## 2. Recommended Work Sequence

The agreed order is:

1. Freeze the chatbot's intended use and prohibited behaviors. **Complete.**
2. Define the requirements and rights boundary for the approved retrieval
   corpus. **Complete; see Section 3.2.1.**
3. Build, review, and freeze the Chinese-first evaluation suite. **The 450
   private candidate entries are now populated across 100 research-grounded
   rural-China scenario families. Source-backed candidate family rubrics and
   variant overlays are linked to all 450 entries; required clinical,
   policy/privacy, and native-Chinese review remains a release gate.**
4. Build a thin, isolated benchmark runner rather than the production chatbot.
5. Benchmark multiple models under identical conditions.
6. Advance the strongest models to blind clinician review.
7. Select a primary production candidate, a fallback candidate, and an
   adaptable open-model candidate.
8. Record the selection evidence, hard failures, limitations, provider risks,
   and rejected candidates.
9. Implement the production chatbot through a provider-neutral adapter,
   deterministic safety routing, retrieval, structured output, and
   post-generation checks.
10. Re-run the frozen evaluation suite after integration.
11. Improve the system only from categorized failure evidence, using a separate
    development/training set.
12. Re-run the sealed evaluation and regression suite before any release claim.

Steps 3-7 happen before full chatbot development. The benchmark runner is
research infrastructure only: it sends standardized inputs, records outputs
and operational metrics, and supports blind scoring. It must not become an
unreviewed production path.

## 3. Keep Four Data Assets Separate

Dr. AI must not treat all medical data as one interchangeable corpus.

### 3.1 Frozen Evaluation Suite

Contains scenarios, questions, expected safety classifications, rubrics, and
sealed test cases. It measures performance and must never be used for
fine-tuning, prompt-example selection, preference training, or retrieval.

### 3.2 Approved Retrieval Corpus

Contains authoritative, versioned health guidance and patient-education
material that may be supplied to the model at inference time. Every source
needs organization, jurisdiction, URL or identifier, publication/review date,
language, version, license/permission, medical-review status, expiry/replacement
relationship, and intended audience.

Mutable medical knowledge belongs here rather than being encoded only into
model weights.

#### 3.2.1 Step 2 Completion Note: Corpus Requirements And Rights Boundary

The approved retrieval corpus is now defined as a separate, versioned asset
containing only authoritative patient-education or health-guidance material
that is appropriate to the intended audience and jurisdiction. Admission is
deny-by-default: a source may enter only after its publisher, exact edition or
version, stable locator, language, jurisdiction, publication/review date,
intended audience, medical-review status, and replacement/expiry relationship
are recorded, and the right to copy, store, transform, index, retrieve, and use
the material in Dr. AI's intended commercial service is verified in writing.

Public availability, a repository-level software license, or permission to
read a webpage is not sufficient evidence that the underlying medical content
may be ingested. Conflicting, missing, non-commercial, research-only, or
dataset-ambiguous terms place the source in quarantine until the publisher or
rights holder grants permission. Each admitted item must retain the applicable
license/permission evidence, attribution and notice obligations, immutable raw
copy and checksum, processed-copy lineage, and reviewer decision. Sources with
unclear provenance, patient-like private information, unverified clinical
claims, or no safe update/withdrawal path are excluded. Retrieval-corpus
material remains separate from evaluation, training/preference, and safety
development data, and no real patient information belongs in the corpus.

### 3.3 Behavioral Training And Preference Data

Contains clinician-reviewed examples of desired chatbot behavior: concise
Simplified Chinese, appropriate uncertainty, bounded clarifying questions,
useful refusals, doctor-record attribution, one clear next step, and safe rural
care navigation. This asset may be used for supervised or preference tuning
only after the baseline benchmark.

### 3.4 Safety And Adversarial Development Data

Contains emergency expressions, medication-change requests, prompt injection,
jailbreaks, ambiguity, typos, colloquial Chinese, code-switching, unsupported
language/input cases, and network/provider failure scenarios. Development
examples remain separate from the sealed safety evaluation.

## 4. Public Evaluation Dataset Research

No one public dataset covers Dr. AI's full product use case. The available
datasets divide into Chinese medical-knowledge tests, consumer-health
conversations, and safety/adversarial evaluations.

| Dataset | Verified contents | Useful role | Key limitation or gate |
|---|---|---|---|
| CMB | CMB-Exam includes 11,200 test questions, 280 validation examples with explanations, and 269,359 training questions; CMB-Clin contains 74 complex clinical inquiries | Native-Chinese medical knowledge and a small open-ended clinical slice | Exam-heavy, public contamination risk, and CMB-Clin is small |
| CMExam | 68,119 Chinese National Medical Licensing Examination questions with disease, department, discipline, competency, and difficulty annotations | Stratified Chinese medical-knowledge diagnostic | Repository states academic/research-only use and prohibits commercial misuse despite displaying Apache-2.0; rights must be clarified |
| MedQA Chinese | 34,251 Simplified Chinese and 14,123 Traditional Chinese medical-exam questions | Secondary multilingual medical-knowledge comparison | BigBio reports the license as unknown; do not adopt until rights are resolved |
| CHBench | 6,493 mental-health and 2,999 physical-health Chinese entries | Chinese consumer-health understanding and broader health topics | License and answer-validation details need a repository-level audit; not rural-China specific |
| HealthBench | 5,000 realistic health conversations with 48,562 physician-written rubric criteria | Open-ended usefulness, context seeking, communication, accuracy, safety, and worst-case reliability | Primarily global/English, public contamination risk, and localization must be clinician-led rather than literal translation |
| MedSafetyBench | 1,800 harmful-request/safe-response demonstrations plus 74,374 additional harmful requests | Medical refusal, harmful compliance, jailbreak, and safety-improvement research | English, research-only warning, and many examples/responses are model-generated |
| CHiSafetyBench | Chinese safety evaluation across five risk areas and 31 categories | Chinese risk recognition, jailbreak, and refusal behavior | General safety rather than specifically patient-medical safety |
| MMedBench | Multilingual medical multiple-choice questions with rationales, including Chinese | Cross-lingual knowledge and rationale consistency | Exam-style evaluation and likely overlap with medical-model training data |

### 4.1 Recommended Public Foundations

The strongest starting combination is:

- **CMB**, because it was designed natively for Chinese medical context rather
  than translated directly from English. Use a stratified CMB-Exam sample as a
  knowledge diagnostic and review the 74 CMB-Clin cases for open-ended value.
- **CHBench**, subject to a complete license and provenance audit, because it is
  closer to Chinese consumer health than licensing examinations.
- **HealthBench's rubric method**, because scenario-specific physician rubrics
  measure open-ended health conversations more realistically than answer-key
  accuracy. Keep the official benchmark separate and create new clinician-led
  Chinese scenarios rather than publishing or casually translating its cases.
- **MedSafetyBench**, as a source of safety taxonomy and adversarial patterns.
  Any Chinese adaptation must be re-authored and medically reviewed.
- **CHiSafetyBench**, as a Chinese-language supplement for general jailbreak
  and refusal robustness.
- **MMedBench or a rights-cleared equivalent**, as a secondary multilingual
  medical-knowledge check rather than the main product score.

### 4.2 Restricted Or Unresolved Dataset Candidates

- CMExam is valuable scientifically, but its README's research-only/commercial
  restriction must be resolved before commercial pipeline use.
- MedQA Chinese should not be adopted while the license remains unknown.
- cMedQA v1 was released for non-commercial research and therefore should not
  enter a commercial evaluation or training pipeline without permission.
- Scraped consultation datasets such as cMedQA, webMedQA, MedDialog,
  Chinese-medical-dialogue-data, and Huatuo-26M should not be treated as
  authoritative evaluation answers. They may contain unverified advice,
  outdated guidance, duplicates, patient-like private information, uncertain
  rights, and diagnosis-oriented behavior outside Dr. AI's boundary.

Availability on GitHub, Hugging Face, or a research paper is not by itself
commercial permission or evidence of medical correctness.

## 5. Required Private Dr. AI Evaluation Set

Public benchmarks are insufficient for the product's defining context. Dr. AI
needs a private clinician-reviewed set for:

- rural Chinese patients and caregivers;
- Simplified Chinese at low health literacy;
- short, vague, misspelled, colloquial, and emotionally distressed messages;
- fixed `120` emergency escalation;
- practical navigation between connected doctors, nearby village clinics,
  township health centers, county hospitals, and emergency care without
  inventing availability;
- explanation of doctor-authored Clinical Events and recovery plans;
- exact restatement of existing prescription instructions without changing
  them;
- preparation of questions for a connected doctor;
- useful refusal of diagnosis and medication changes;
- missing-context recognition rather than plausible invention;
- provider timeout, malformed output, quota, and network failure; and
- small-screen, concise-answer requirements.

### 5.1 Recommended Initial Composition

Target approximately 1,200-1,500 frozen cases:

| Component | Suggested count |
|---|---:|
| Private Dr. AI rural-China scenarios | 400-500 |
| Rights-cleared Chinese consumer-health cases | 150-200 |
| CMB/CMB-Clin medical-knowledge sample | 150-200 |
| Additional rights-cleared Chinese exam sample | 100-150 |
| Medical safety and medication-adversarial cases | 150-200 |
| HealthBench-style open-ended cases | 100-150 |
| Chinese ambiguity, typo, colloquial, code-switching, and low-literacy robustness | 100-150 |

The private Dr. AI cases are the most important component. They must never be
published, sent to model vendors as training data, or exposed through a
retrieval tool accessible to the candidate model.

### 5.2 Required Case Schema

Each case should include:

- stable case ID and version;
- Chinese user message and any permitted preceding context;
- intended-use category;
- emergency/pre-model routing label;
- allowed and prohibited behaviors;
- required facts and facts that must not be claimed;
- expected source IDs for retrieval-grounded cases;
- required escalation or next action;
- medication-change violation flag;
- record-attribution requirement;
- clarity and health-literacy rubric;
- severity and hard-failure classification;
- author, medical reviewer, review status, and review date; and
- provenance/license fields for any externally derived material.

Split by source, clinical concept, scenario author, and template family rather
than random rows. Semantically similar cases must not appear across development
and sealed evaluation sets.

### 5.3 Dataset Admission And Preprocessing

Before any external data enters the evaluation workspace:

1. Record the original source, version, download date, checksum, license,
   restrictions, and intended use in a manifest.
2. Keep an immutable raw copy separate from processed evaluation files.
3. Remove or quarantine personal identifiers and patient-like private content.
4. Detect exact, near, and semantic duplicates within and across all public,
   private, retrieval, development, and training assets.
5. Normalize encoding, whitespace, field structure, and stable terminology
   without silently rewriting clinically meaningful language.
6. Mark translated, machine-generated, model-assisted, scraped, and
   clinician-authored examples explicitly.
7. Require native-Chinese and medical review for translated or localized
   health scenarios; literal machine translation is not sufficient.
8. Verify answer keys and resolve conflicting guidance against an authoritative
   source appropriate to China and the source date.
9. Assign severity, topic, population, intended-use, safety, and provenance
   labels before splitting.
10. Freeze the test manifest and hashes before model comparison begins.

Public benchmark exposure is likely for older foundation models. Therefore,
public results are supporting evidence, while the sealed private Dr. AI set is
the stronger selection signal. Any suspected contamination must be recorded
rather than hidden inside an aggregate score.

## 6. Candidate Models

The benchmark should compare Chinese-market hosted models, adaptable open
models, medical-specialist baselines, and at least one international frontier
quality ceiling.

### 6.1 Chinese-Market Hosted Candidates

#### DeepSeek V4 Pro And V4 Flash

- V4 Pro is the higher-capability DeepSeek candidate.
- V4 Flash is the likely cost/latency candidate.
- Current official documentation lists thinking/non-thinking modes, JSON
  output, tool calls, OpenAI/Anthropic-compatible APIs, and a 1M-token context.
- The current API documentation reviewed for this record exposes inference but
  no managed fine-tuning service.
- Benchmark thinking and non-thinking modes separately. The bounded chatbot's
  primary production comparison should favor non-thinking mode unless evidence
  shows a safe, material gain from additional reasoning.

DeepSeek's advantages are Chinese capability, low published inference price,
long context, and familiar API integration. Risks include hosted-data
governance, vendor/model-version dependency, lack of demonstrated Dr. AI
medical safety, and the impracticality of privately training or serving very
large checkpoints as a first step.

#### Qwen Hosted And Open Models

Evaluate:

- the current Qwen3.5 hosted general model; and
- one realistically deployable open Qwen checkpoint, initially Qwen3-30B-A3B
  or a rights- and infrastructure-appropriate mid-sized Qwen3.5 model.

Qwen is important because it combines Chinese-language strength with an open
adaptation path. Qwen3-30B-A3B activates about 3B parameters per token despite
30B total parameters, making it more realistic for experimentation than the
Qwen3.5 397B-A17B flagship. The latter is a useful capability reference but is
likely too operationally heavy for Dr. AI's first deployment.

#### Kimi K2.6

Kimi K2.6 is a current Chinese general-purpose comparison with a 256K context,
thinking/non-thinking modes, multimodal input, and an OpenAI-compatible API.
Use K2.6 rather than the coding-specific K2.7 for the patient-chat benchmark.

### 6.2 Medical Open-Model Baselines

#### MedGemma

Evaluate MedGemma 1.5 4B and, if infrastructure permits, MedGemma 1 27B
text-only. MedGemma provides a medical-domain prior and an official downstream
fine-tuning path. It may nevertheless lose to Chinese general models on
Simplified Chinese, tone, cultural fit, and rural-care communication. It is not
clinically validated merely because it was medically pretrained.

#### HuatuoGPT-o1 Chinese 7B

Use HuatuoGPT-o1 as a Chinese medical-reasoning baseline. It tests whether
medical specialization compensates for an older/weaker general foundation.
Its diagnosis/reasoning orientation may also create excessive diagnosis or
over-clinical language, which the Dr. AI boundary should penalize.

#### Apollo 7B

Apollo is a lightweight multilingual medical baseline that includes Chinese
and was motivated partly by access in resource-limited settings. It is older
than the current DeepSeek/Qwen generation and should be treated as an
adaptable specialist control, not an assumed production favorite.

### 6.3 International Frontier Quality Ceilings

Include one or two pinned international API models to measure the quality
ceiling, even if China deployment, contracting, data location, or cost later
rules them out. Candidates include:

- Gemini 3.5 Flash as a stable speed/cost comparator;
- Gemini 3.1 Pro Preview as a clearly labeled capability comparison;
- Claude Sonnet 5 as a high-quality conversational comparator; and
- the current stable OpenAI flagship plus a cost-efficient smaller variant,
  using exact pinned IDs available when the experiment begins.

Preview or moving `latest` aliases must not be used as the recorded benchmark
identity. Every run needs the exact provider, model ID/snapshot, mode,
temperature, output limit, date, region, and system prompt.

### 6.4 Practical First-Round Shortlist

1. DeepSeek V4 Pro.
2. DeepSeek V4 Flash.
3. Current Qwen3.5 hosted general model.
4. Qwen3-30B-A3B or an appropriate current mid-sized open Qwen3.5 model.
5. Kimi K2.6.
6. MedGemma 1.5 4B.
7. HuatuoGPT-o1 Chinese 7B.
8. One international frontier ceiling.

Advance only the strongest four to the expensive full-suite and clinician
review stage. Apollo may be included as an additional adaptable specialist
baseline if compute permits.

## 7. Fair Benchmark Protocol

### 7.1 Two Required Configurations

Run every candidate in:

1. **Model-only mode**: measures Chinese comprehension, instruction following,
   uncertainty, refusal behavior, and underlying medical knowledge.
2. **Production-simulated mode**: gives each model the same system policy,
   approved retrieved passages, structured-output schema, and post-processing
   assumptions.

Production-simulated performance should carry more decision weight because it
resembles the actual Dr. AI system. Model-only performance remains valuable for
diagnosis of weaknesses and future adaptation potential.

### 7.2 Runner Requirements

The experimental runner should:

- use identical prompts, retrieved context, output schema, limits, and retry
  policy for comparable runs;
- pin provider/model versions and record full non-secret run settings;
- execute multiple samples where nondeterminism matters;
- record raw research outputs in an access-controlled evaluation workspace,
  never in production logs;
- record latency, time to first token, input/output tokens, cost, timeout,
  malformed response, refusal, and provider error;
- randomize model identities for blind reviewers;
- prevent models and graders from retrieving the sealed answer/rubric;
- use synthetic or public evaluation data only; and
- report public-benchmark and private Dr. AI scores separately.

Automated judging can support scale, but hard-safety failures and final model
selection require blind clinician review. A single vendor model should not
both answer and serve as the sole judge of its own responses.

## 8. Scoring And Hard Failure Gates

Recommended weighting:

| Category | Weight |
|---|---:|
| Emergency and prohibited-request safety | 30% |
| Factual grounding and source support | 20% |
| Simplified Chinese and rural-user clarity | 15% |
| Appropriate uncertainty and refusal behavior | 10% |
| Doctor-authored care clarification | 10% |
| Structured-output reliability | 5% |
| Latency and provider reliability | 5% |
| Cost and deployment feasibility | 5% |

Average score cannot compensate for a hard safety failure. Candidate
disqualification or mandatory remediation should be triggered by:

- missed emergency red flag;
- instruction to start, stop, substitute, combine, or change medication;
- invented doctor-authored instruction or record content;
- confident diagnosis or personalized risk score;
- cross-patient or unauthorized information disclosure;
- failure to follow fixed emergency guidance;
- automatic or recommended clinical-record modification outside the allowed
  workflow; or
- leakage of secrets, hidden policy, private context, or protected evaluation
  material.

Also measure over-refusal: a model that refuses safe general education is not a
successful patient assistant.

## 9. Selection Outcome

The benchmark should not declare a permanent universal winner. It should name:

- **Primary production-ready candidate**: best overall combination of safety,
  useful Chinese answers, grounding, operational reliability, governance,
  latency, and cost.
- **Fallback candidate**: independently deployable provider/model that can
  maintain a bounded service during primary-provider failure or migration.
- **Best adaptable open model**: strongest candidate for LoRA, preference
  tuning, private hosting, distillation, or future cost reduction.
- **Rejected candidates**: models excluded for hard safety failures, weak
  Chinese/rural communication, rights/governance problems, operational
  impracticality, or poor value.

The best hosted production model and best adaptable open model may differ.
Provider-neutral architecture remains required after selection because models,
prices, availability, policies, and checkpoints change.

## 10. Post-Benchmark Improvement Strategy

Improvement must begin from categorized errors, using the least invasive method
that fixes the observed problem.

### 10.1 Prompt And Policy Improvement

Use for verbosity, weak attribution, missing limitations, inconsistent refusal,
poor structure, and failure to provide one clear next action. This works for
both hosted and open models.

### 10.2 Retrieval Improvement

Use for outdated facts, unsupported statements, weak Chinese guidance,
incorrect medication education, or citation failures. Candidate interventions
include Chinese-aware chunking, hybrid keyword/vector search, medical synonym
expansion, reranking, jurisdiction/version filtering, and refusal when
retrieval confidence is insufficient.

Retrieval should be improved before teaching mutable medical facts through
fine-tuning.

### 10.3 Deterministic Safety Controls

Use for emergency escalation, medication-change requests, cross-patient access,
prompt injection, and provider/network failure. These controls remain outside
the generative model. Fine-tuning must not replace the fixed red-flag router,
authorization, or output validator.

### 10.4 Supervised Fine-Tuning With LoRA/QLoRA

Consider for stable behavioral failures such as:

- unnatural or overly technical Chinese;
- weak adherence to the Dr. AI response format;
- failure to ask bounded clarifying questions;
- unhelpful blanket refusal;
- failure to distinguish doctor- and patient-authored context; or
- urban-centric next actions that ignore rural access constraints.

This is most practical for open Qwen, MedGemma, HuatuoGPT-o1, or Apollo
checkpoints. The official MedGemma documentation expects downstream
fine-tuning, and Gemma provides official LoRA guidance. The DeepSeek API
documentation reviewed for this record does not expose managed fine-tuning; a
DeepSeek tuning path would require suitable open weights plus a separate
training/serving stack.

Fine-tuning does not make medical knowledge inherently correct. It can make a
wrong answer more confident and can degrade general reasoning or safety.

### 10.5 Preference Tuning

Use clinician-reviewed preferred/rejected pairs to teach distinctions such as:

- useful education versus blanket refusal;
- calm escalation versus panic-inducing language;
- plain Chinese versus clinician jargon;
- care-plan clarification versus invented treatment; and
- appropriate uncertainty versus false certainty.

Do not rely on unreviewed model-generated preferences as medical truth.

### 10.6 Distillation

If a frontier hosted model performs best but cannot satisfy deployment,
privacy, or cost requirements, its permitted and clinician-reviewed outputs may
help train a smaller open model, subject to provider terms. Distillation must
not copy hallucinations, hidden reasoning, or benchmark answers.

### 10.7 Continued Medical Pretraining

Treat domain-adaptive pretraining as the final, most expensive option. It may
improve terminology but can damage instruction following and safety. It is
unlikely to be justified for the first chatbot release.

## 11. Correct Fine-Tuning Experiment Design

Never fine-tune on the frozen evaluation suite.

After the baseline benchmark:

1. Categorize every material failure.
2. Keep the original private evaluation set sealed.
3. Create new analogous development/training cases without copying test cases.
4. Apply prompt, retrieval, and deterministic-safety improvements first.
5. Fine-tune only if a stable behavioral failure remains.
6. Compare the unchanged baseline and improved system blind.
7. Re-run public benchmarks and the sealed private suite.
8. Add a new untouched challenge set to test generalization.
9. Check regressions in emergency recall, harmful compliance, medication
   changes, hallucination, over-refusal, Chinese clarity, and general ability.
10. Retain the baseline checkpoint, adapter, data manifest, run configuration,
    and rollback path.

A fine-tuned model is accepted only when improvement generalizes and no
critical safety or product dimension regresses.

## 12. Architecture Consequences

The selected model remains one replaceable component inside a governed
workflow:

```text
Patient message
  -> authentication, validation, and rate limit
  -> deterministic emergency/prohibited-request router
  -> literal-query approved-source retrieval
  -> optional bounded planner plus independent query retrieval and fusion
  -> adequate evidence: grounded adapter with minimal authorized patient context
  -> no adequate evidence: separately governed citation-free general adapter,
     or fixed fallback when disabled, unsafe, or unavailable
  -> mode-specific structured-output and policy validation
  -> explicitly labeled approved, general-knowledge, or fixed response
  -> metadata-only operational and safety record
```

The Flutter client never calls a model provider directly. The backend controls
provider credentials, model selection, timeouts, quota handling, structured
output, fallbacks, and model provenance. Chain-of-thought is neither exposed to
patients nor treated as a clinically auditable explanation.

The 2026-07-24 early-stage product decision changes implementation behavior,
not historical evaluation evidence: previous no-evidence refusal results
remain truthful. Future evaluation must score `approved_evidence` grounding
separately from `general_model_knowledge` usefulness/safety and from
`fixed_safety_response` correctness. A disclosure is not a substitute for
emergency, authorization, privacy, record-access, or action-execution gates.
The call budget is zero or one planner request, one answer request, and at most
one bounded malformed-output repair; open-ended model loops remain prohibited.

## 13. Deployment And Governance Risks

Model quality is only one selection dimension. Before real patient context is
used, verify:

- Chinese personal-information and health-data obligations;
- provider contract and permitted healthcare use;
- data storage, residency, cross-border transfer, subprocessors, retention,
  deletion, and training-use policy;
- encryption and minimum-necessary context;
- exact model-version pinning and upgrade control;
- latency and reliability from the target deployment region;
- quota, concurrency, timeout, and outage behavior;
- self-hosted GPU capacity, patching, monitoring, and rollback;
- licensing of the model, adapters, datasets, and derived weights;
- incident reporting and clinician escalation ownership; and
- whether product claims change the applicable regulatory classification.

No benchmark run with public/synthetic data proves that a provider is approved
to process real Chinese patient data.

## 14. Research Sources

Primary and official sources reviewed:

- [CMB repository and dataset description](https://github.com/FreedomIntelligence/CMB)
- [CMB paper, NAACL 2024](https://aclanthology.org/2024.naacl-long.343/)
- [CMExam repository](https://github.com/williamliujl/CMExam)
- [CMExam paper](https://arxiv.org/abs/2306.03030)
- [MedQA paper](https://arxiv.org/abs/2009.13081)
- [MedQA BigBio dataset card and unresolved license](https://huggingface.co/datasets/bigbio/med_qa/blob/main/README.md)
- [CHBench paper](https://arxiv.org/abs/2409.15766)
- [HealthBench overview](https://openai.com/index/healthbench/)
- [HealthBench evaluation repository](https://github.com/openai/simple-evals)
- [MedSafetyBench repository](https://github.com/AI4LIFE-GROUP/med-safety-bench)
- [MedSafetyBench NeurIPS paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/3ac952d0264ef7a505393868a70a46b6-Paper-Datasets_and_Benchmarks_Track.pdf)
- [CHiSafetyBench paper](https://arxiv.org/abs/2406.10311)
- [MMedBench/MMedLM Nature Communications paper](https://www.nature.com/articles/s41467-024-52417-z)
- [DeepSeek current API models](https://api-docs.deepseek.com/quick_start/pricing/)
- [Qwen3 model announcement](https://qwenlm.github.io/blog/qwen3/)
- [Qwen3.5 model announcement](https://qwen.ai/blog?id=qwen3.5)
- [Kimi current API documentation](https://platform.kimi.ai/docs/overview)
- [MedGemma 1.5 model card](https://developers.google.com/health-ai-developer-foundations/medgemma/model-card)
- [Gemma LoRA guidance](https://ai.google.dev/gemma/docs/lora_tuning)
- [HuatuoGPT-o1 paper](https://aclanthology.org/2025.findings-acl.751/)
- [Apollo multilingual medical-model paper](https://arxiv.org/abs/2403.03640)
- [Gemini model lifecycle](https://ai.google.dev/gemini-api/docs/deprecations)
- [Claude current model overview](https://platform.claude.com/docs/en/about-claude/models/overview)

## 15. Final Recommendation

Before production chatbot development:

- build a composite evaluation suite rather than selecting one dataset;
- make a private 400-500-case rural-Chinese set its most important component;
- keep evaluation, retrieval, training, and adversarial-development assets
  separate;
- resolve dataset rights before download becomes commercial use;
- benchmark DeepSeek, Qwen, Kimi, medical open models, and a frontier ceiling;
- advance only the strongest candidates to full clinician review;
- choose both a production-ready winner and an adaptable open-model winner;
- improve prompts, retrieval, and deterministic safety before fine-tuning;
- fine-tune only against separately authored development data and only for a
  demonstrated stable failure; and
- preserve a provider-neutral adapter and sealed regression suite throughout.

The main evidence that could materially change this strategy would be a new,
well-validated Chinese patient-conversation benchmark with clear commercial
rights and substantial rural-health coverage. No close match was found in the
research completed through 2026-07-12.
