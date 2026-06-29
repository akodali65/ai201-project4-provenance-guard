# Provenance Guard

Provenance Guard is a backend API that helps creative-sharing platforms provide transparent AI-attribution information for submitted text. The system combines multiple detection signals, produces an attribution result with a confidence score, displays a transparency label, and allows creators to appeal the decision.

---

## Features

* Submit creative writing for analysis
* AI detection using Groq's Llama 3.3 70B model
* Stylometric heuristic analysis
* Combined confidence scoring
* Transparency labels
* Audit logging
* Appeal workflow
* Rate limiting using Flask-Limiter

---

## System Architecture

### Submission Flow

```
POST /submit
        |
        v
Validate Request
        |
        v
Groq LLM Detection
        |
        v
Stylometric Analysis
        |
        v
Confidence Scoring
        |
        v
Transparency Label
        |
        v
Audit Log
        |
        v
JSON Response
```

### Appeal Flow

```
POST /appeal
        |
        v
Validate Request
        |
        v
Find Original Submission
        |
        v
Update Status
        |
        v
Write Appeal Entry
        |
        v
JSON Response
```

---

# Detection Signals

## Signal 1 – Groq LLM

The system uses the **llama-3.3-70b-versatile** model from Groq.

The model examines:

* writing style
* coherence
* structure
* overall language patterns

Output:

* 0.0 = strongly human-written
* 1.0 = strongly AI-generated

---

## Signal 2 – Stylometric Heuristics

Python heuristics measure structural writing characteristics.

Metrics include:

* sentence length variation
* vocabulary diversity (type-token ratio)
* punctuation density

Output:

* 0.0 = more human-like
* 1.0 = more AI-like

---

# Confidence Scoring

Both signals are combined using weighted averaging:

```
combined_score =
(0.65 × llm_score)
+
(0.35 × stylometric_score)
```

Thresholds:

| Score       | Attribution  |
| ----------- | ------------ |
| 0.75 – 1.00 | likely_ai    |
| 0.40 – 0.74 | uncertain    |
| 0.00 – 0.39 | likely_human |

---

# Transparency Labels

### High-confidence AI

The system explains that the content appears AI-generated while allowing the creator to appeal.

### High-confidence Human

The system explains that the content appears human-written based on multiple signals.

### Uncertain

The system explains that mixed signals were detected and no final attribution claim is made.

---

# API Endpoints

## POST /submit

Request

```json
{
  "text": "Example writing...",
  "creator_id": "creator123"
}
```

Example Response

```json
{
  "content_id": "...",
  "attribution": "likely_ai",
  "confidence": 0.81,
  "label": "...",
  "signals": {
    "llm_score": 0.86,
    "stylometric_score": 0.72
  },
  "status": "classified"
}
```

---

## POST /appeal

Request

```json
{
  "content_id": "...",
  "creator_reasoning": "I wrote this myself."
}
```

Example Response

```json
{
  "message": "Appeal received",
  "content_id": "...",
  "status": "under_review"
}
```

---

## GET /log

Returns all structured audit log entries.

---

# Running the Project

Clone the repository:

```bash
git clone <your-repository-url>
cd ai201-project4-provenance-guard
```

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```text
GROQ_API_KEY=your_api_key_here
```

Run the server:

```bash
python3 app.py
```

---

# Testing

Example submission:

```bash
curl -X POST http://127.0.0.1:5001/submit \
-H "Content-Type: application/json" \
-d '{"text":"Artificial intelligence is transforming education.","creator_id":"creator123"}'
```

Example appeal:

```bash
curl -X POST http://127.0.0.1:5001/appeal \
-H "Content-Type: application/json" \
-d '{"content_id":"YOUR_CONTENT_ID","creator_reasoning":"I wrote this myself."}'
```

View audit log:

```bash
curl http://127.0.0.1:5001/log
```

---

# Project Structure

```
ai201-project4-provenance-guard/
│
├── app.py
├── planning.md
├── requirements.txt
├── README.md
├── audit_log.json
├── .gitignore
└── .env
```

---

# Technologies Used

* Python
* Flask
* Flask-Limiter
* Groq API
* python-dotenv
* JSON
* Regular Expressions

---

# Future Improvements

* Database-backed audit log
* Human reviewer dashboard
* Additional stylometric features
* User authentication
* Frontend interface
* More advanced confidence calibration
