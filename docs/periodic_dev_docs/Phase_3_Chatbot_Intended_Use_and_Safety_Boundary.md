# Phase 3 Chatbot Intended Use and Safety Boundary

Status: revised product boundary through the symptom-first Slice 9A reset<br>
Date: 2026-07-21<br>
Owner: Harry Cao<br>
Applies to: Dr. AI production/commercial v1.0 patient chatbot

## 1. Decision

The first Phase 3 AI deliverable will be a **Chinese-first patient education
and care-understanding chatbot**. It is one supporting module inside Dr. AI,
not the whole product, not a separate general-purpose AI assistant, and not a
replacement for the doctor-patient care workflow.

The chatbot will help patients understand health information, understand the
care already provided by their doctor, explore evidence-grounded possible
explanations for symptoms, prepare useful questions, and recognize when they
should stop chatting and seek human help. It may provide **diagnostic
orientation**—a clearly uncertain discussion of more than one plausible
explanation and the information that would help distinguish them—but it will
not confirm or rule out a diagnosis, prescribe, independently triage, or make
treatment decisions.

A disclaimer does not make an unsafe answer safe. The broader scope is allowed
only when the response is grounded in approved patient evidence, keeps
possibilities distinct from a patient-specific diagnosis, states material
uncertainty, and gives a practical verification or care-seeking step.

This boundary is provider-neutral. DeepSeek may be evaluated as a model
provider, but the product contract must not depend on DeepSeek, fine-tuning, or
any single model vendor.

## 2. Place Within The Dr. AI System

Dr. AI remains an AI clinical-copilot system built around patients, doctors,
medical history, Clinical Events/Care Episodes, prescriptions, medications,
imaging, recovery plans, consultations, and follow-up. The chatbot supports
that system but does not own those records or workflows.

```text
Patient and account foundation
  -> profile, medical history, language, doctor connection

Doctor-led care workflow
  -> Clinical Event, diagnosis, prescription, imaging review, recovery plan

Patient chatbot
  -> explains approved information
  -> discusses possible symptom explanations without confirming a diagnosis
  -> helps the patient prepare questions
  -> reinforces doctor-authored instructions without changing them
  -> directs the patient to a doctor or emergency help when appropriate

Other Phase 3 AI modules
  -> diagnostic assistance, recovery-plan drafting, and medication-safety
     support remain separate, separately gated workflows
```

The chatbot must not silently perform the work of another module. In
particular, it must not present itself as the AI Diagnosis Assistant,
Medication Safety Agent, Recovery Planning Agent, specialist consultation
service, appointment service, or emergency-response service.

## 3. Primary Users And Rural-China Context

The primary user is a patient or caregiver in China, including people in rural
areas who may have limited access to specialists, lower health literacy,
limited digital confidence, older or lower-cost phones, unstable connectivity,
or long travel times to a county-level or urban hospital.

The initial production experience must therefore:

- use Simplified Chinese as the primary reviewed language;
- use short sentences, familiar words, and explain unavoidable medical terms;
- present one clear next action instead of a long list of possibilities;
- avoid assuming that the user can immediately reach a tertiary hospital or
  specialist;
- distinguish practical options such as contacting the connected doctor,
  visiting a nearby village clinic or township health center, attending a
  county hospital, or seeking emergency care, without pretending to know the
  capability or opening status of a specific facility;
- remain useful on a small screen and low-bandwidth connection;
- provide a safe fixed fallback when the AI provider or network is unavailable;
- avoid stigma, blame, urban-centric assumptions, and condescending language;
- support English as a secondary interface language without making English
  medical knowledge the default for Chinese patients; and
- treat dialect, minority-language, and voice-input support as unvalidated
  until each is explicitly designed and tested. The chatbot must not claim to
  understand them reliably before that work is complete.

The chatbot should increase access to understandable information. Limited local
medical access is a reason to give more practical routes and better preparation,
not a reason to overstate diagnostic certainty or provide autonomous treatment.

## 4. Intended Uses

The chatbot may support the following bounded uses.

### 4.1 General Health Education

- Explain common health concepts at a safe, general level.
- Explain common medical terms and the usual purpose of tests or procedures.
- Provide general prevention, self-care, and healthy-living education when it
  does not become individualized treatment.
- State uncertainty and the limits of general information.

### 4.2 Preparation For Human Care

- Help a patient organize symptoms and questions before contacting a doctor.
- Suggest factual details the patient may want to tell the doctor, such as
  onset, duration, severity, relevant medication use, or changes over time.
- Summarize a patient-authored question for the patient to review and submit.
- Recommend the appropriate human workflow inside Dr. AI, such as contacting a
  connected doctor or opening the relevant Clinical Event.

The chatbot may help prepare information, but it must not convert that
information into a diagnosis or alter a doctor-owned record.

### 4.3 Symptom Orientation And Possible Explanations

For non-emergency symptom or diagnosis-seeking questions, the chatbot may:

- answer the underlying question instead of returning a diagnosis-only refusal;
- describe more than one plausible explanation supported by approved
  patient-facing evidence;
- explain which reported details, measurements, timing, exposures, or changes
  would affect interpretation;
- distinguish supported self-observation steps from reasons to seek local care
  or contact the connected doctor;
- help the patient prepare a concise symptom timeline and questions for a
  clinician; and
- explain that a clinician may need an examination, repeated measurements, or
  tests before a diagnosis can be confirmed.

It must not label a possibility as the patient's condition, provide a
patient-specific probability or risk score, imply that the listed
possibilities are exhaustive, or use a profile value as proof of a diagnosis.
When evidence supports only general symptom education and not named possible
causes, the chatbot must say that plainly rather than filling the gap from
model memory.

### 4.4 Doctor-Authored Care Clarification

When access is permitted and the patient deliberately opens the relevant
context, the chatbot may explain:

- a doctor-authored recovery plan;
- patient-facing text from a Clinical Event;
- an existing prescription or medication schedule;
- the meaning of a patient Today task; and
- the difference between an instruction, reminder, and completed task.

The response must clearly attribute this information to the patient's existing
record, for example, "According to the recovery plan recorded by your doctor."
It must not invent missing instructions, reinterpret a provisional diagnosis
as confirmed, or change the source record.

### 4.5 Medication Education

- Explain the general purpose of a medication already present in the patient's
  prescription or medication schedule.
- Restate the doctor-authored dose, timing, route, and instructions exactly when
  those fields are available and verified.
- Explain that suspected side effects, missed doses, interactions, allergies,
  pregnancy, or uncertainty should be raised with a qualified clinician or
  pharmacist.

Medication education must never become a new dosage recommendation, a decision
to start or stop a medicine, or an instruction that overrides the prescriber.

### 4.6 Safety Escalation

- Detect defined emergency red flags before any generative model call.
- Represent the reported presentation deterministically, including symptoms,
  anatomy, onset, duration, trajectory, severity, associated signs,
  measurements, population, pregnancy, exposures, trauma, danger signals, and
  negation, hypothetical/not-present mentions, and the user's requested action
  before deciding whether ordinary chat may continue.
- Use that controlled presentation assessment as the sole authority for an
  emergency route. A second keyword or regular-expression override must not
  bypass its negation, hypothetical-mention, severity, or context handling.
- After the safety decision, retrieval may use bounded deterministic views of
  that presentation. The literal question remains authoritative; generated
  views must not invent a symptom or diagnosis, and view-only evidence is
  admissible only when reviewed source metadata centrally matches an actually
  reported, non-negated clinical concept.
- Return fixed, reviewed emergency guidance rather than a generated medical
  answer.
- Tell the user to call **120** or seek immediate local emergency care when the
  emergency rule is triggered, and encourage involving a nearby trusted person
  when appropriate.
- Include only brief scene-safety guidance appropriate to the detected pattern,
  such as dispatcher-guided CPR/AED, choking, seizure, bleeding, poisoning,
  fresh-air, electrical, snake-bite, or post-drowning precautions. This copy
  remains a candidate until named clinical/native-Chinese review is recorded;
  local tests must not be represented as that approval.
- Direct non-emergency but concerning questions to the connected doctor or an
  appropriate local clinician.
- For allowed non-emergency messages, assign care timing from a separately
  reviewable deterministic combination rule over the controlled presentation:
  same-day in-person assessment, clinician contact, or routine education. A
  model must not choose, weaken, or upgrade this route.
- In a patient-owned thread, bounded prior user wording may supply missing
  context only for an actual follow-up or a controlled context-dependent
  presentation such as reduced fetal movement after a pregnancy statement.
  Prior assistant text is never medical evidence, and the current user's
  literal query remains the retrieval/reranking authority.
- A post-safety model planner receives only prior user wording admitted by that
  continuity decision. Its rewrite may normalize literal search wording but
  cannot add, remove, or override controlled presentation fields; retry views,
  presentation-central evidence admission, and urgency remain server-owned.
- Colloquial question endings such as `要紧吗` and `怎么办` are not sufficient
  to declare a query ambiguous. If the controlled representation already
  contains a standalone symptom, pregnancy, exposure, trauma, or explicit
  condition topic, planner failure must retain the initial governed result.
  Evidence may be withheld for context-dependent ambiguity only when that
  standalone topic is absent.
- Send the model only the server-assigned non-emergency route and its bounded
  allowed next actions. Reject an output that downgrades a same-day action or
  introduces `call_120`; only the pre-model emergency layer may select that
  action. When evidence or the provider is unavailable, fixed fallback copy may
  retain the candidate care-timing instruction without adding a diagnosis or
  unsupported medical explanation.

The non-emergency rule table and fallback timing copy are local candidates. They
require named clinical, native-Simplified-Chinese, and product review before
patient-facing production; exact agreement with the candidate evaluation labels
is not approval.

Pre-model answer evaluation may run before corpus readiness only in an explicit
synthetic, non-production, rollback-only environment. It must execute the real
patient-chat entry point, fail if retrieval or either model is reached, keep
multi-turn setup to the one contract-authorized prior user turn, persist no
evaluation conversation after the run, and report this result separately from
generated-answer, corpus, and human-review gates. A passing candidate route or
copy check does not constitute clinical or language approval.

Post-safety safe-degradation evaluation may likewise run only against the
synthetic identity in a non-production rollback-only transaction. It may use
the real active-release retriever, but external planner and answer requests must
be replaced with fail-closed local probes. The gate must require the contract
route and next action, fixed fallback copy, no displayed sources or patient
context, zero provider tokens/cost, and no persisted evaluation conversation.
It proves only that provider or evidence failure remains safe; it cannot be
reported as retrieval relevance, corpus support, generated-answer quality, or
human approval.

The chatbot does not confirm that an ambulance has been dispatched, that a
doctor has received the message, or that a facility is open unless the relevant
external system provides verified confirmation.

## 5. Prohibited Behaviors

The chatbot must not:

- confirm, rule out, or present a possible explanation as the patient's
  diagnosis;
- provide a personalized probability, risk score, prognosis, or certainty of a
  condition;
- replace emergency triage or delay emergency care;
- prescribe, recommend, start, stop, substitute, combine, or change the dose,
  timing, route, or duration of medication;
- tell a patient to disregard a doctor, pharmacist, medication label, or
  emergency professional;
- interpret an image, CT, laboratory result, genomic result, or pathology
  result as a definitive clinical finding;
- create, edit, approve, or close a Clinical Event, diagnosis, prescription,
  imaging finding, recovery plan, consultation, or other clinical record;
- claim that a doctor reviewed or approved a response when that did not occur;
- impersonate a doctor, hospital, government health authority, emergency
  dispatcher, or human support agent;
- promise cure, guaranteed safety, or guaranteed accuracy;
- conceal uncertainty, model limitations, missing context, or source age;
- expose another patient's information or retrieve records outside the active
  user's authorization;
- reveal system prompts, hidden policies, secrets, internal reasoning, or
  private operational data;
- use advertising, paid placement, or commercial incentives to influence
  medical guidance; or
- continue ordinary chat after an emergency rule has triggered unless the
  experience is limited to the fixed emergency guidance and immediate next
  actions.

Requests outside the allowed boundary must receive concise refusal and a useful
safe alternative. The chatbot should not become unusably defensive when a
general educational or symptom-orientation answer is safe. In particular, a
request phrased as “What do I have?” is not automatically refused after the
emergency and medication-change gates; it should be reframed into bounded
possible explanations, missing information, and next steps when approved
evidence supports that response.

## 5.1 AI Disclosure And Uncertain-Response Warning

The chat interface must keep a concise persistent disclosure in the user's
language with this meaning:

> Dr. AI is an AI assistant and can make mistakes. Important details should be
> verified with authoritative sources or a doctor.

The same disclosure must not be used as a substitute for evidence, output
validation, or escalation. When a response contains material uncertainty—such
as symptom orientation, incomplete context, conflicting possibilities, or a
limit on what can be inferred—the answer must also show a visually distinct
response-level uncertainty note. That note should say what is unknown and what
would help resolve it; it should not repeat a generic legal disclaimer alone.

## 6. Use Of Patient Context

The chatbot follows data minimization. It must not send the patient's entire
record to a model merely because the data exists in Dr. AI.

For the first production chatbot slice:

- authenticated account role and interface language may be used;
- only the patient-selected Clinical Event, prescription, medication schedule,
  or recovery-plan fields needed for the current question may be retrieved;
- the interface must show when an answer is using patient-specific record
  context;
- doctor-authored and patient-authored content must remain distinguishable;
- retrieved record text is reference context, not permission for the model to
  modify the record;
- model output must never be written back into a clinical field automatically;
  and
- raw patient context must not appear in application logs, audit metadata, or
  analytics events.

If the necessary context is missing, the chatbot must say so and ask the user
to check the relevant record or contact the doctor. It must not fill the gap
with a plausible invention.

## 7. Conversation Storage And Privacy Boundary

The initial Phase 3 implementation will keep conversation content in the
active session only. It may persist metadata required for safety, operations,
rate limiting, and audit, such as message time, safety category, fallback
reason, model identifier, prompt hash, and character count. It must not place
raw prompts, raw responses, clinical content, filenames, object keys, secrets,
or access tokens into logs or metadata-only audit events.

Persistent readable conversation history is deferred until Dr. AI has an
explicit patient-consent experience, retention period, deletion behavior,
encryption design, authorized-access policy, and reviewed legal/privacy basis.
Adding history later must not silently change this boundary.

No real patient information may be sent to an external model provider until
the applicable privacy, security, provider-contract, data-location, consent,
and legal gates are closed.

## 8. Knowledge And Model Boundary

The chatbot should answer factual health questions from a reviewed,
version-controlled retrieval corpus appropriate for Chinese patients. Source
selection should prioritize authoritative Chinese health guidance, approved
patient education, medicine information, and locally applicable care
instructions. Each source needs provenance, jurisdiction, publication or
review date, language, version, license status, and medical-review status.

A retrieval candidate is not evidence of support until named review has
assigned case-specific relevant and forbidden source IDs. Retrieval-only
evaluation must fail closed while labels are pending and must report clinically
labelled recall, symptom-only recall, paired-variant non-degradation,
forbidden-source leakage, pre-safety call behavior, release-matched latency,
provider calls, and cost separately from candidate-coverage diagnostics. Empty
labels must not be scored as successful retrieval.

Complete-answer evaluation must likewise preserve each variant's own route,
call permissions, relevant sources, and forbidden sources. A five-case initial
batch may authorize progression to a full run, but it must not be reported as
the full machine gate. Only an exact, duplicate-free 100-canonical plus
85-variant result matrix may close the machine portion, and independent human
review remains mandatory afterward.

General model memory is not an authoritative medical source. Fine-tuning may
later improve tone, format, terminology, or refusal behavior, but it must not be
used as the only mechanism for keeping clinical knowledge correct or current.

The architecture must use a provider adapter so that DeepSeek and other
candidate models can be evaluated or replaced without changing the patient
contract. Model selection must be based on Dr. AI's Chinese/English safety and
quality evaluation set rather than general benchmark rankings alone.

## 9. Required Safety Flow

Every message follows this order:

1. Authenticate the user and enforce rate limits.
2. Validate length, format, and supported input type.
3. Build the controlled clinical-presentation representation and run
   deterministic emergency combinations, negation-aware danger checks, and
   prohibited-request checks before retrieval or generation. The resulting
   controlled safety assessment is the only component permitted to select the
   emergency route; parallel keyword overrides are prohibited.
4. Return fixed reviewed guidance if an emergency rule triggers.
5. For an allowed non-emergency message, assign the server-owned same-day,
   clinician-contact, or routine-education route before retrieval.
6. Retrieve only approved sources and the minimum authorized patient context
   needed for an allowed question.
7. Call the model through the provider-neutral backend adapter with only the
   allowed next actions for the deterministic route.
8. Validate structured output and screen for prohibited medical instructions,
   unsupported claims, missing attribution, and unsafe escalation.
   Passage-ID membership alone is insufficient: each displayed answer sentence
   must remain semantically anchored to its specifically cited passage or
   authorized context. Model-generated uncertainty text must not introduce an
   unsupported number, disease concept, or clinical-presentation feature.
9. Show a bounded answer, limitations, relevant source attribution, and one
   clear next action.
10. Record metadata-only safety and operational events.
11. Use fixed fallback copy for timeout, quota, malformed response, provider
    outage, or failed safety validation.

The Flutter client must never call an LLM provider directly.

## 10. Relationship With Human Care

The chatbot should strengthen, not bypass, the patient's relationship with
qualified human care.

- The connected doctor remains responsible for confirmed diagnosis, prescriptions,
  treatment decisions, recovery-plan approval, and clinical record changes.
- A chatbot response does not become part of the formal medical record unless
  a separately designed workflow allows a patient or clinician to review and
  deliberately submit specific content.
- A suggestion to contact a doctor is not the same as a successfully delivered
  consultation request or message.
- The chatbot must clearly tell the user when the next step leaves the chatbot
  and enters another Dr. AI module.
- If no connected doctor is available, the chatbot may give general navigation
  toward an appropriate local level of care but must not claim availability or
  book care unless those systems are implemented and verified.

## 11. User-Facing Positioning

The interface should describe the module in language similar to:

> Dr. AI健康助手可以帮助你理解健康知识、梳理症状可能的解释、了解医生已经记录的照护内容，并整理下一步要做什么。Dr. AI 是 AI 助手，可能会出错；重要信息请通过权威来源或医生核实。它不能确认诊断、开药或处理急症。如遇呼吸困难、严重胸痛、意识不清、大量出血等紧急情况，请立即拨打120或尽快前往急诊。

The exact Chinese copy requires product and medical review before release. It
must be visible at first use and available later without overwhelming every
ordinary response with repeated legalistic text.

## 12. Acceptance Criteria For The Frozen Boundary

This intended-use decision is implemented correctly only when:

- all chatbot requirements and tests classify scenarios according to this
  document;
- emergency red flags return fixed guidance before any model call;
- diagnosis-seeking requests receive bounded symptom orientation when evidence
  supports it, while medication-change requests and diagnostic certainty are
  refused safely;
- safe educational questions receive useful answers rather than blanket
  refusals;
- responses are Chinese-first, understandable at low health literacy, usable
  on patient-phone layouts, and tested under slow or failed network conditions;
- the chatbot identifies when it is using doctor-authored patient context;
- no model output automatically changes a clinical record;
- no raw prompt, raw response, or clinical content appears in logs or
  metadata-only audit events;
- provider outages and failed output validation produce bounded fallback copy;
- the provider can be replaced without changing the client-facing contract;
- the product does not claim that the chatbot is clinically validated until
  the separate evidence, legal, privacy, and regulatory gates are closed; and
- any proposed expansion beyond this boundary requires an explicit update to
  this record before implementation.

## 13. Deferred Decisions

The following are not authorized by this boundary and require separate review:

- persistent patient-visible conversation history;
- real patient data sent to any external model provider;
- voice input, dialect support, or minority-language support;
- automated handoff, paging, appointment booking, or emergency dispatch;
- clinician-facing chatbot use;
- confirmed or personalized-probability diagnosis and treatment recommendations;
- model interpretation of imaging, laboratory, pathology, or genomic inputs;
- fine-tuning and the final production model/provider choice; and
- using chatbot content as a formal medical record.

These items are deferred so the first chatbot slice remains narrow, useful,
testable, and consistent with Dr. AI's role as an assistive clinical copilot.
