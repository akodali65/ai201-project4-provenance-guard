from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from groq import Groq
import uuid
import json
import os
import re
import string
from datetime import datetime

load_dotenv()

app = Flask(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://"
)

AUDIT_LOG = "audit_log.json"
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def read_log():
    if not os.path.exists(AUDIT_LOG):
        return []
    with open(AUDIT_LOG, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def write_log(entry):
    log = read_log()
    log.append(entry)
    with open(AUDIT_LOG, "w") as f:
        json.dump(log, f, indent=4)


def get_llm_score(text):
    try:
        prompt = f"""
You are an AI-writing detection assistant.

Analyze the following text and return ONLY one decimal number from 0.0 to 1.0.

0.0 means definitely human-written.
0.5 means uncertain or mixed.
1.0 means definitely AI-generated.

Return only the number.

Text:
{text}
"""
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        score = float(response.choices[0].message.content.strip())
        return max(0.0, min(1.0, score))

    except Exception as e:
        print("Groq error:", e)
        return 0.5


def get_stylometric_score(text):
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    words = re.findall(r"\b\w+\b", text.lower())

    if not words:
        return 0.5

    sentence_lengths = [len(re.findall(r"\b\w+\b", s)) for s in sentences]

    if len(sentence_lengths) > 1:
        avg_len = sum(sentence_lengths) / len(sentence_lengths)
        variance = sum((x - avg_len) ** 2 for x in sentence_lengths) / len(sentence_lengths)
    else:
        variance = 0

    type_token_ratio = len(set(words)) / len(words)
    punctuation_count = sum(1 for char in text if char in string.punctuation)
    punctuation_density = punctuation_count / max(len(text), 1)

    variance_score = 1.0 - min(variance / 40, 1.0)
    vocab_score = 1.0 - min(type_token_ratio, 1.0)
    punctuation_score = 1.0 - min(punctuation_density * 10, 1.0)

    final_score = (
        0.45 * variance_score +
        0.35 * vocab_score +
        0.20 * punctuation_score
    )

    return round(max(0.0, min(1.0, final_score)), 2)


def combine_scores(llm_score, stylometric_score):
    return round((0.65 * llm_score) + (0.35 * stylometric_score), 2)


def get_attribution(confidence):
    if confidence >= 0.75:
        return "likely_ai"
    elif confidence <= 0.39:
        return "likely_human"
    return "uncertain"


def get_transparency_label(confidence):
    if confidence >= 0.75:
        return (
            "This content shows strong signs of being AI-generated. "
            "This decision is based on multiple detection signals. "
            "Although confidence is high, mistakes are still possible. "
            "The creator may appeal this decision."
        )
    elif confidence <= 0.39:
        return (
            "This content shows strong signs of being human-written. "
            "This assessment is based on multiple detection signals and is provided "
            "to improve transparency for readers."
        )
    return (
        "This content contains mixed signals. The system cannot confidently "
        "determine whether it is AI-generated or human-written, so no final "
        "attribution claim is being made."
    )


def find_submission(content_id):
    for entry in reversed(read_log()):
        if entry.get("content_id") == content_id and entry.get("event_type") == "submission":
            return entry
    return None


@app.route("/")
def home():
    return jsonify({"message": "Welcome to Provenance Guard API"})


@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
def submit():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    text = data.get("text")
    creator_id = data.get("creator_id")

    if not text or not creator_id:
        return jsonify({"error": "Both text and creator_id are required."}), 400

    content_id = str(uuid.uuid4())

    llm_score = get_llm_score(text)
    stylometric_score = get_stylometric_score(text)
    confidence = combine_scores(llm_score, stylometric_score)
    attribution = get_attribution(confidence)
    label = get_transparency_label(confidence)

    log_entry = {
        "event_type": "submission",
        "timestamp": datetime.utcnow().isoformat(),
        "content_id": content_id,
        "creator_id": creator_id,
        "attribution": attribution,
        "confidence": confidence,
        "llm_score": llm_score,
        "stylometric_score": stylometric_score,
        "signals_used": ["groq_llm", "stylometric_heuristics"],
        "status": "classified"
    }

    write_log(log_entry)

    return jsonify({
        "content_id": content_id,
        "attribution": attribution,
        "confidence": confidence,
        "label": label,
        "signals": {
            "llm_score": llm_score,
            "stylometric_score": stylometric_score
        },
        "status": "classified"
    })


@app.route("/appeal", methods=["POST"])
def appeal():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    content_id = data.get("content_id")
    creator_reasoning = data.get("creator_reasoning")

    if not content_id or not creator_reasoning:
        return jsonify({
            "error": "Both content_id and creator_reasoning are required."
        }), 400

    original = find_submission(content_id)

    if not original:
        return jsonify({"error": "Content ID not found."}), 404

    appeal_entry = {
        "event_type": "appeal",
        "timestamp": datetime.utcnow().isoformat(),
        "content_id": content_id,
        "creator_id": original.get("creator_id"),
        "original_attribution": original.get("attribution"),
        "original_confidence": original.get("confidence"),
        "llm_score": original.get("llm_score"),
        "stylometric_score": original.get("stylometric_score"),
        "appeal_reasoning": creator_reasoning,
        "status": "under_review"
    }

    write_log(appeal_entry)

    return jsonify({
        "message": "Appeal received",
        "content_id": content_id,
        "status": "under_review"
    })


@app.route("/log", methods=["GET"])
def get_log():
    return jsonify({"entries": read_log()})


if __name__ == "__main__":
    app.run(debug=True, port=5001)