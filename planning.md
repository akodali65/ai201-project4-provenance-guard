# Provenance Guard Planning

## Project Goal

Provenance Guard is a backend system for creative-sharing platforms. It analyzes submitted text using multiple detection signals, returns an attribution result with a confidence score, displays a transparency label, and allows creators to appeal classifications they believe are incorrect.

---

# Architecture

## System Flow

```text
                    SUBMISSION FLOW

                POST /submit
                     |
                     v
        Validate JSON Input
      (text + creator_id)
                     |
                     v
     Signal 1: Groq LLM Classification
                     |
                     v
    Signal 2: Stylometric Heuristics
                     |
                     v
         Confidence Score Calculation
                     |
                     v
      Transparency Label Generation
                     |
                     v
             Structured Audit Log
                     |
                     v
            JSON Response Returned


                     APPEAL FLOW

                POST /appeal
                     |
                     v
Validate content_id + creator_reasoning
                     |
                     v
      Locate Original Classification
                     |
                     v
     Update Status → under_review
                     |
                     v
       Record Appeal in Audit Log
                     |
                     v
          JSON Confirmation Returned
```

### Architecture Narrative

A submitted piece of content first reaches the **POST /submit** endpoint where the request is validated. The content is analyzed by two independent detection signals: a Groq LLM classifier and a stylometric heuristic analyzer. Their outputs are combined into a confidence score, which is converted into a transparency label. The final decision is saved in the audit log before the API returns a JSON response.

If a creator disagrees with the decision, they submit an appeal through **POST /appeal**. The system records the creator's reasoning, updates the submission status to **under_review**, logs the appeal, and returns confirmation.

---

# Detection Signals

## Signal 1 – Groq LLM Classification

The first detection signal uses Groq's **llama-3.3-70b-versatile** model to estimate whether the submitted text appears AI-generated or human-written.

### Measures

* Overall writing style
* Semantic coherence
* Tone consistency
* Generic vs personal writing style

### Output

A confidence score between **0.0 and 1.0**

* 0.0 = strongly human-written
* 1.0 = strongly AI-generated

### Blind Spot

The LLM may incorrectly classify:

* highly formal human writing
* carefully edited AI-generated writing

---

## Signal 2 – Stylometric Heuristics

The second signal analyzes measurable writing characteristics using pure Python.

### Metrics

* Sentence length variance
* Vocabulary diversity (type-token ratio)
* Punctuation density

### Why this signal?

AI writing is often more structurally uniform, while human writing usually contains more natural variation.

### Output

A score between **0.0 and 1.0**

Higher scores indicate more AI-like structural patterns.

### Blind Spot

The heuristic may struggle with:

* poems
* very short text
* academic essays
* heavily edited writing

---

# Confidence Scoring

The final confidence score combines both detection signals.

## Formula

```text
combined_score = (0.65 × llm_score) + (0.35 × stylometric_score)
```

The LLM receives a larger weight because it evaluates semantic meaning while the heuristic focuses on measurable writing structure.

## Thresholds

| Score       | Classification        |
| ----------- | --------------------- |
| 0.75 – 1.00 | High-confidence AI    |
| 0.40 – 0.74 | Uncertain             |
| 0.00 – 0.39 | High-confidence Human |

A score around **0.60** means the system has mixed evidence and therefore avoids making a strong attribution claim.

### False Positive Strategy

False positives are more harmful than false negatives on a creative writing platform. Because of this, the AI threshold is intentionally conservative (0.75).

---

# Transparency Labels

## High-confidence AI

> "This content shows strong signs of being AI-generated. This decision is based on multiple detection signals. Although confidence is high, mistakes are still possible. The creator may appeal this decision."

---

## High-confidence Human

> "This content shows strong signs of being human-written. This assessment is based on multiple detection signals and is provided to improve transparency for readers."

---

## Uncertain

> "This content contains mixed signals. The system cannot confidently determine whether it is AI-generated or human-written, so no final attribution claim is being made."

---

# Appeals Workflow

## Who may appeal?

Any creator whose content has been classified.

## Appeal Request

The request contains:

* content_id
* creator_reasoning

## Workflow

1. Locate the original submission.
2. Update the status to **under_review**.
3. Save the creator's explanation.
4. Record the appeal in the audit log.
5. Return confirmation to the creator.

## Human Reviewer Information

A reviewer would see:

* Content ID
* Creator ID
* Attribution result
* Confidence score
* LLM score
* Stylometric score
* Appeal reasoning
* Current status

---

# API Endpoints

## POST /submit

### Request

```json
{
  "text": "submitted creative writing",
  "creator_id": "creator123"
}
```

### Response

```json
{
  "content_id": "unique-id",
  "attribution": "likely_ai",
  "confidence": 0.82,
  "label": "Transparency label",
  "signals": {
    "llm_score": 0.85,
    "stylometric_score": 0.76
  },
  "status": "classified"
}
```

---

## POST /appeal

### Request

```json
{
  "content_id": "unique-id",
  "creator_reasoning": "I wrote this myself."
}
```

### Response

```json
{
  "message": "Appeal received",
  "content_id": "unique-id",
  "status": "under_review"
}
```

---

## GET /log

Returns recent structured audit log entries in JSON format.

---

# Anticipated Edge Cases

1. Poetry with repetitive wording may resemble AI because of limited sentence variation.
2. Formal academic writing by humans may receive higher AI scores.
3. Very short submissions provide too little data for reliable stylometric analysis.
4. AI-generated writing that has been heavily edited by a human may appear human-written.

---

# AI Tool Plan

## Milestone 3

### Provide

* Architecture
* Detection Signals
* API Endpoints

### Ask AI to Generate

* Flask application skeleton
* POST /submit endpoint
* Groq signal function
* Simple audit log helper

### Verify

* Flask server runs
* POST /submit works
* JSON contains content_id, attribution, confidence, label, and signal score
* GET /log returns entries

---

## Milestone 4

### Provide

* Detection Signals
* Confidence Scoring
* Architecture

### Ask AI to Generate

* Stylometric heuristic function
* Confidence scoring function
* Attribution mapping logic

### Verify

* Test AI-generated text
* Test casual human text
* Compare confidence scores
* Confirm audit log stores both signal scores

---

## Milestone 5

### Provide

* Transparency Labels
* Appeals Workflow
* Architecture
* API Endpoints

### Ask AI to Generate

* Label generation function
* POST /appeal endpoint
* Rate limiting
* Complete audit logging

### Verify

* All three label variants appear
* Appeals update status to **under_review**
* Rate limiting returns HTTP 429 when exceeded
* Audit log contains at least three complete entries
